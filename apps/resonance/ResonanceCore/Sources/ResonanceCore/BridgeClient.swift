import Foundation
import os

private let bridgeLogger = Logger(subsystem: "com.resonance.mac", category: "Bridge")

public struct BridgeClientConfiguration: Sendable {
    public var pythonExecutable: String
    public var moduleName: String
    public var workingDirectory: URL
    public var timeoutSeconds: TimeInterval
    public var environment: [String: String]

    public init(
        pythonExecutable: String = "/usr/bin/python3",
        moduleName: String = "playlist_builder.cli.engine_bridge",
        workingDirectory: URL,
        timeoutSeconds: TimeInterval = 180,
        environment: [String: String] = [:]
    ) {
        self.pythonExecutable = pythonExecutable
        self.moduleName = moduleName
        self.workingDirectory = workingDirectory
        self.timeoutSeconds = timeoutSeconds
        self.environment = environment
    }
}

/// Shared transport contract used by Resonance shells to call Python bridge commands.
public protocol BridgeTransport: Sendable {
    func send(
        command: BridgeCommand,
        requestID: String,
        params: BridgeJSONObject,
        onEvent: (@Sendable (BridgeEventMessage) -> Void)?,
        onDiagnostic: (@Sendable (String) -> Void)?
    ) async throws -> (
        response: BridgeResponseMessage,
        events: [BridgeEventMessage]
    )
}

public extension BridgeTransport {
    /// Convenience helper used by ResonanceMac call sites; removable if callers pass full arguments.
    func send(
        command: BridgeCommand,
        requestID: String = UUID().uuidString,
        params: BridgeJSONObject = [:],
        onEvent: (@Sendable (BridgeEventMessage) -> Void)? = nil,
        onDiagnostic: (@Sendable (String) -> Void)? = nil
    ) async throws -> (response: BridgeResponseMessage, events: [BridgeEventMessage]) {
        try await send(
            command: command,
            requestID: requestID,
            params: params,
            onEvent: onEvent,
            onDiagnostic: onDiagnostic
        )
    }
}

private final class ProcessStreamCollector: @unchecked Sendable {
    private let lock = NSLock()
    private var stdoutBuffer = ""
    private var stderrBuffer = ""
    private(set) var lines: [String] = []
    private let onStdoutLine: (@Sendable (String) -> Void)?
    private let onStderrLine: (@Sendable (String) -> Void)?

    init(
        onStdoutLine: (@Sendable (String) -> Void)?,
        onStderrLine: (@Sendable (String) -> Void)?
    ) {
        self.onStdoutLine = onStdoutLine
        self.onStderrLine = onStderrLine
    }

    func consumeStdoutChunk(_ chunk: String) {
        lock.lock()
        defer { lock.unlock() }
        stdoutBuffer += chunk
        while let newlineIndex = stdoutBuffer.firstIndex(of: "\n") {
            let line = String(stdoutBuffer[..<newlineIndex])
            stdoutBuffer = String(stdoutBuffer[stdoutBuffer.index(after: newlineIndex)...])
            lines.append(line)
            onStdoutLine?(line)
        }
    }

    func consumeStderrChunk(_ chunk: String) {
        lock.lock()
        defer { lock.unlock() }
        stderrBuffer += chunk
        while let newlineIndex = stderrBuffer.firstIndex(of: "\n") {
            let line = String(stderrBuffer[..<newlineIndex])
            stderrBuffer = String(stderrBuffer[stderrBuffer.index(after: newlineIndex)...])
            onStderrLine?(line)
        }
    }

    func flushRemainingStdout() {
        lock.lock()
        defer { lock.unlock() }
        guard !stdoutBuffer.isEmpty else { return }
        lines.append(stdoutBuffer)
        onStdoutLine?(stdoutBuffer)
        stdoutBuffer = ""
    }

    func flushRemainingStderr() {
        lock.lock()
        defer { lock.unlock() }
        guard !stderrBuffer.isEmpty else { return }
        onStderrLine?(stderrBuffer)
        stderrBuffer = ""
    }
}

private final class BridgeProcessRunState: @unchecked Sendable {
    private let lock = NSLock()
    private var finished = false

    func finish(
        _ continuation: CheckedContinuation<[String], Error>,
        with result: Result<[String], Error>
    ) {
        lock.lock()
        defer { lock.unlock() }
        guard !finished else { return }
        finished = true
        switch result {
        case .success(let lines):
            continuation.resume(returning: lines)
        case .failure(let error):
            continuation.resume(throwing: error)
        }
    }
}

/// Process wrapper guarded by an internal lock; safe to share as bridge transport.
public final class BridgeClient: BridgeTransport, @unchecked Sendable {
    private let configuration: BridgeClientConfiguration
    private let lock = NSLock()

    public init(configuration: BridgeClientConfiguration) {
        self.configuration = configuration
    }

    public func send(
        command: BridgeCommand,
        requestID: String,
        params: BridgeJSONObject,
        onEvent: (@Sendable (BridgeEventMessage) -> Void)?,
        onDiagnostic: (@Sendable (String) -> Void)?
    ) async throws -> (response: BridgeResponseMessage, events: [BridgeEventMessage]) {
        let payload: BridgeJSONObject = [
            "id": .string(requestID),
            "command": .string(command.rawValue),
            "params": .object(params),
        ]
        let requestLine = try Self.encodeJSONObject(payload)
        bridgeLogger.info("Bridge send \(command.rawValue, privacy: .public) id=\(requestID, privacy: .public)")
        let lines = try await runProcess(requestLine: requestLine) { line in
            Self.dispatchStreamingLine(
                line: line,
                requestID: requestID,
                onEvent: onEvent,
                onDiagnostic: onDiagnostic
            )
        } onStderrLine: { line in
            let message = "[stderr] \(line)"
            bridgeLogger.warning("\(message, privacy: .public)")
            onDiagnostic?(message)
        }
        return try Self.parseConversation(requestID: requestID, lines: lines)
    }

    public static func dispatchStreamingLine(
        line: String,
        requestID: String,
        onEvent: (@Sendable (BridgeEventMessage) -> Void)?,
        onDiagnostic: (@Sendable (String) -> Void)?
    ) {
        let trimmed = line.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        bridgeLogger.debug("Bridge stdout: \(trimmed, privacy: .public)")

        if let object = try? BridgeResponseParser.parseJSONObject(trimmed),
           object["type"]?.stringValue == "event",
           let event = try? BridgeResponseParser.parseEventLine(trimmed) {
            onEvent?(event)
            return
        }

        if let object = try? BridgeResponseParser.parseJSONObject(trimmed),
           object["type"]?.stringValue == "response",
           object["id"]?.stringValue == requestID,
           object["ok"]?.boolValue == false,
           let errorObject = object["error"]?.objectValue,
           let message = errorObject["message"]?.stringValue {
            onDiagnostic?("[bridge error] \(message)")
        }
    }

    public static func parseConversation(
        requestID: String,
        lines: [String]
    ) throws -> (response: BridgeResponseMessage, events: [BridgeEventMessage]) {
        var events: [BridgeEventMessage] = []
        var response: BridgeResponseMessage?
        var skippedNonJSONLines = 0

        for line in lines where !line.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            guard let object = try? BridgeResponseParser.parseJSONObject(line) else {
                skippedNonJSONLines += 1
                bridgeLogger.warning(
                    "Bridge stdout ignored (non-JSON): \(line, privacy: .public)"
                )
                continue
            }

            if object["type"]?.stringValue == "event",
               let event = try? BridgeResponseParser.parseEventLine(line) {
                events.append(event)
                continue
            }

            if object["type"]?.stringValue == "response", object["id"]?.stringValue == requestID,
               let parsed = try? BridgeResponseParser.parseResponseLine(line) {
                response = parsed
            }
        }

        if skippedNonJSONLines > 0 {
            bridgeLogger.warning(
                "Bridge conversation skipped \(skippedNonJSONLines, privacy: .public) non-JSON stdout line(s)"
            )
        }

        guard let response else {
            throw BridgeClientError.invalidResponse
        }
        if !response.ok, let error = response.error {
            throw BridgeClientError.bridge(error)
        }
        return (response, events)
    }

    private func runProcess(
        requestLine: String,
        onStdoutLine: (@Sendable (String) -> Void)? = nil,
        onStderrLine: (@Sendable (String) -> Void)? = nil
    ) async throws -> [String] {
        try await withCheckedThrowingContinuation { continuation in
            lock.lock()
            defer { lock.unlock() }

            let process = Process()
            process.executableURL = URL(fileURLWithPath: configuration.pythonExecutable)
            process.arguments = ["-u", "-m", configuration.moduleName]
            process.currentDirectoryURL = configuration.workingDirectory

            var environment = ProcessInfo.processInfo.environment
            environment["PYTHONUNBUFFERED"] = "1"
            environment["PYTHONIOENCODING"] = "utf-8"
            for (key, value) in configuration.environment {
                environment[key] = value
            }
            process.environment = environment

            let inputPipe = Pipe()
            let outputPipe = Pipe()
            let errorPipe = Pipe()
            process.standardInput = inputPipe
            process.standardOutput = outputPipe
            process.standardError = errorPipe

            do {
                try process.run()
            } catch {
                continuation.resume(throwing: BridgeClientError.processUnavailable)
                return
            }

            bridgeLogger.info("Bridge process started pid=\(process.processIdentifier)")

            if let data = (requestLine + "\n").data(using: .utf8) {
                inputPipe.fileHandleForWriting.write(data)
            }
            inputPipe.fileHandleForWriting.closeFile()

            let streamCollector = ProcessStreamCollector(
                onStdoutLine: onStdoutLine,
                onStderrLine: onStderrLine
            )
            let runState = BridgeProcessRunState()
            let deadline = Date().addingTimeInterval(configuration.timeoutSeconds)

            outputPipe.fileHandleForReading.readabilityHandler = { @Sendable handle in
                let data = handle.availableData
                guard !data.isEmpty else { return }
                streamCollector.consumeStdoutChunk(String(decoding: data, as: UTF8.self))
            }

            errorPipe.fileHandleForReading.readabilityHandler = { @Sendable handle in
                let data = handle.availableData
                guard !data.isEmpty else { return }
                streamCollector.consumeStderrChunk(String(decoding: data, as: UTF8.self))
            }

            DispatchQueue.global(qos: .userInitiated).async { @Sendable in
                while process.isRunning && Date() < deadline {
                    Thread.sleep(forTimeInterval: 0.05)
                }

                outputPipe.fileHandleForReading.readabilityHandler = nil
                errorPipe.fileHandleForReading.readabilityHandler = nil

                let trailingOutput = outputPipe.fileHandleForReading.readDataToEndOfFile()
                if !trailingOutput.isEmpty {
                    streamCollector.consumeStdoutChunk(String(decoding: trailingOutput, as: UTF8.self))
                }
                streamCollector.flushRemainingStdout()

                let trailingError = errorPipe.fileHandleForReading.readDataToEndOfFile()
                if !trailingError.isEmpty {
                    streamCollector.consumeStderrChunk(String(decoding: trailingError, as: UTF8.self))
                }
                streamCollector.flushRemainingStderr()

                if process.isRunning {
                    process.terminate()
                    runState.finish(continuation, with: .failure(BridgeClientError.timeout))
                    return
                }

                let exitCode = process.terminationStatus
                let lines = streamCollector.lines
                bridgeLogger.info("Bridge process finished exit=\(exitCode) lines=\(lines.count)")
                if exitCode != 0, lines.isEmpty {
                    runState.finish(
                        continuation,
                        with: .failure(
                            BridgeClientError.bridge(
                                BridgeErrorPayload(
                                    code: .engineError,
                                    message: "Le processus Python s'est terminé avec le code \(exitCode)."
                                )
                            )
                        )
                    )
                    return
                }

                runState.finish(continuation, with: .success(lines))
            }
        }
    }

    static func encodeJSONObject(_ object: BridgeJSONObject) throws -> String {
        let data = try JSONSerialization.data(withJSONObject: object.mapValues(\.anyValue))
        guard let line = String(data: data, encoding: .utf8) else {
            throw BridgeClientError.invalidResponse
        }
        return line
    }
}

public enum BridgePayloadBuilder {
    public static func playlistDictionary(from result: PlaylistGenerationResult) -> BridgeJSONObject {
        [
            "name": .string(result.playlistName),
            "description": .string("Importée depuis Resonance."),
            "sections": .array(result.sections.map { section in
                .object([
                    "name": .string(section.name),
                    "tracks": .array(section.tracks.map { track in
                        .object([
                            "artist": .string(track.artist),
                            "title": .string(track.title),
                            "section": .string(track.section),
                        ])
                    }),
                ])
            }),
        ]
    }

    public static func importResult(from payload: BridgeJSONObject) throws -> ImportResultState {
        guard let importObject = payload["import"]?.objectValue else {
            throw BridgeClientError.invalidResponse
        }
        let playlistName = importObject["playlist_name"]?.stringValue ?? ""
        let phaseRaw = importObject["phase"]?.stringValue ?? ImportPhase.completed.rawValue
        let phase = ImportPhase(rawValue: phaseRaw) ?? .completed
        let outcomesRaw = importObject["outcomes"]?.arrayValue ?? []
        let outcomes = outcomesRaw.compactMap(\.objectValue).map { item in
            ImportTrackOutcome(
                artist: item["artist"]?.stringValue ?? "",
                title: item["title"]?.stringValue ?? "",
                section: item["section"]?.stringValue ?? "",
                status: ImportTrackStatus(rawValue: item["status"]?.stringValue ?? "") ?? .error,
                message: item["message"]?.stringValue ?? ""
            )
        }
        let historySessionID = payload["history_session_id"]?.stringValue ?? ""
        return ImportResultState(
            playlistName: playlistName,
            outcomes: outcomes,
            phase: phase,
            historySessionID: historySessionID
        )
    }

    public static func generationResult(from payload: BridgeJSONObject) throws -> PlaylistGenerationResult {
        guard let generation = payload["generation"]?.objectValue else {
            throw BridgeClientError.invalidResponse
        }
        let playlistName = generation["playlist_name"]?.stringValue ?? ""
        let averageScore = generation["average_score"]?.doubleValue ?? 0
        let providerRaw = generation["provider_id"]?.stringValue ?? ProviderID.appleMusic.rawValue
        let providerID = ProviderID(rawValue: providerRaw) ?? .appleMusic
        let sectionsRaw = generation["sections"]?.arrayValue ?? []
        let sections = sectionsRaw.compactMap(\.objectValue).map { section in
            let tracksRaw = section["tracks"]?.arrayValue ?? []
            let tracks = tracksRaw.compactMap(\.objectValue).map { track in
                GeneratedTrackPreview(
                    artist: track["artist"]?.stringValue ?? "",
                    title: track["title"]?.stringValue ?? "",
                    section: track["section"]?.stringValue ?? "",
                    score: track["score"]?.doubleValue ?? 0,
                    confidence: ConfidenceLevel(rawValue: track["confidence"]?.stringValue ?? "") ?? .medium,
                    source: track["source"]?.stringValue ?? ""
                )
            }
            return GeneratedSectionPreview(
                name: section["name"]?.stringValue ?? "Playlist",
                tracks: tracks
            )
        }
        return PlaylistGenerationResult(
            playlistName: playlistName,
            sections: sections,
            averageScore: averageScore,
            providerID: providerID,
            historySessionID: payload["history_session_id"]?.stringValue ?? ""
        )
    }

    public static func diagnosticsSnapshot(from payload: BridgeJSONObject) throws -> DiagnosticsSnapshot {
        let engineVersion = payload["engine_version"]?.stringValue ?? ""
        let summaryObject = payload["summary"]?.objectValue ?? [:]
        let summary = diagnosticsSummary(from: summaryObject)
        let eventsRaw = payload["events"]?.arrayValue ?? []
        let events = eventsRaw.compactMap(\.objectValue).map(diagnosticEvent)
        return DiagnosticsSnapshot(engineVersion: engineVersion, summary: summary, events: events)
    }

    public static func providerOptions(from payload: BridgeJSONObject) throws -> [ProviderOption] {
        let providersRaw = payload["providers"]?.arrayValue ?? []
        return providersRaw.compactMap(\.objectValue).map(providerOption)
    }

    private static func diagnosticsSummary(from object: BridgeJSONObject) -> DiagnosticsSummary {
        let providersRaw = object["active_providers"]?.arrayValue ?? []
        let reportsRaw = object["recent_reports"]?.arrayValue ?? []
        return DiagnosticsSummary(
            bridgeStatus: object["bridge_status"]?.stringValue ?? "unknown",
            platform: object["platform"]?.stringValue ?? "",
            executionMS: object["execution_ms"]?.intValue ?? 0,
            catalogCacheEntries: object["catalog_cache_entries"]?.intValue ?? 0,
            identityCacheEntries: object["identity_cache_entries"]?.intValue ?? 0,
            catalogCacheEnabled: object["catalog_cache_enabled"]?.boolValue ?? false,
            countryCode: object["country_code"]?.stringValue ?? "",
            activeProviders: providersRaw.compactMap(\.objectValue).map(providerOption),
            recentReports: reportsRaw.compactMap(\.objectValue).map(reportSummary),
            reportsDirectory: object["reports_directory"]?.stringValue ?? ""
        )
    }

    private static func providerOption(_ object: BridgeJSONObject) -> ProviderOption {
        let providerRaw = object["provider_id"]?.stringValue ?? ProviderID.appleMusic.rawValue
        return ProviderOption(
            providerID: ProviderID(rawValue: providerRaw) ?? .appleMusic,
            displayName: object["display_name"]?.stringValue ?? providerRaw,
            isAvailable: object["is_available"]?.boolValue ?? false,
            isConnected: object["is_connected"]?.boolValue ?? false,
            unavailableReason: object["unavailable_reason"]?.stringValue ?? ""
        )
    }

    private static func reportSummary(_ object: BridgeJSONObject) -> DiagnosticsReportSummary {
        let trackSummary = object["track_summary"]?.objectValue ?? [:]
        return DiagnosticsReportSummary(
            filename: object["filename"]?.stringValue ?? "",
            playlistName: object["playlist_name"]?.stringValue ?? "",
            generatedAt: object["generated_at"]?.stringValue ?? "",
            added: trackSummary["added"]?.intValue ?? 0,
            notFound: trackSummary["not_found"]?.intValue ?? 0,
            skipped: trackSummary["skipped"]?.intValue ?? 0,
            errors: trackSummary["errors"]?.intValue ?? 0
        )
    }

    private static func diagnosticEvent(_ object: BridgeJSONObject) -> DiagnosticEvent {
        let payloadRaw = object["payload"]?.arrayValue ?? []
        let payload = payloadRaw.compactMap { item -> DiagnosticEventPayload? in
            if let dict = item.objectValue,
               let key = dict["key"]?.stringValue,
               let value = dict["value"]?.stringValue {
                return DiagnosticEventPayload(key: key, value: value)
            }
            if let pair = item.arrayValue, pair.count == 2,
               let key = pair[0].stringValue,
               let value = pair[1].stringValue {
                return DiagnosticEventPayload(key: key, value: value)
            }
            return nil
        }
        let levelRaw = object["level"]?.stringValue ?? DiagnosticLevel.info.rawValue
        return DiagnosticEvent(
            phase: object["phase"]?.stringValue ?? "",
            message: object["message"]?.stringValue ?? "",
            level: DiagnosticLevel(rawValue: levelRaw) ?? .info,
            timestampISO: object["timestamp_iso"]?.stringValue ?? "",
            payload: payload
        )
    }

    public static func historySessions(from payload: BridgeJSONObject) -> [SessionHistorySummary] {
        let sessionsRaw = payload["sessions"]?.arrayValue ?? []
        return sessionsRaw.compactMap(\.objectValue).map(historySummary)
    }

    public static func historySessionDetail(from payload: BridgeJSONObject) -> SessionHistoryDetail? {
        guard let object = payload["session"]?.objectValue else { return nil }
        return historyDetail(from: object)
    }

    public static func exportHistorySession(from payload: BridgeJSONObject) -> SessionHistoryExport? {
        guard let object = payload["export"]?.objectValue else { return nil }
        return SessionHistoryExport(
            sessionID: object["session_id"]?.stringValue ?? "",
            playlistName: object["playlist_name"]?.stringValue ?? "",
            providerID: ProviderID(rawValue: object["provider_id"]?.stringValue ?? "") ?? .appleMusic,
            status: SessionHistoryStatus(rawValue: object["status"]?.stringValue ?? "") ?? .failed,
            textReportPath: object["text_report_path"]?.stringValue ?? "",
            jsonReportPath: object["json_report_path"]?.stringValue ?? ""
        )
    }

    private static func historySummary(_ object: BridgeJSONObject) -> SessionHistorySummary {
        SessionHistorySummary(
            sessionID: object["session_id"]?.stringValue ?? "",
            startedAtISO: object["started_at_iso"]?.stringValue ?? "",
            finishedAtISO: object["finished_at_iso"]?.stringValue ?? "",
            playlistName: object["playlist_name"]?.stringValue ?? "",
            providerID: ProviderID(rawValue: object["provider_id"]?.stringValue ?? "") ?? .appleMusic,
            status: SessionHistoryStatus(rawValue: object["status"]?.stringValue ?? "") ?? .failed,
            trackCount: object["track_count"]?.intValue ?? 0,
            addedCount: object["added_count"]?.intValue ?? 0,
            skippedCount: object["skipped_count"]?.intValue ?? 0,
            notFoundCount: object["not_found_count"]?.intValue ?? 0,
            errorCount: object["error_count"]?.intValue ?? 0,
            durationMS: object["duration_ms"]?.intValue,
            textReportPath: object["text_report_path"]?.stringValue ?? "",
            jsonReportPath: object["json_report_path"]?.stringValue ?? ""
        )
    }

    private static func historyDetail(from object: BridgeJSONObject) -> SessionHistoryDetail {
        let summary = historySummary(object)
        return SessionHistoryDetail(
            summary: summary,
            generationRequest: object["generation_request"]?.objectValue ?? [:],
            generationResult: object["generation_result"]?.objectValue ?? [:],
            importResult: object["import_result"]?.objectValue ?? [:],
            diagnostics: object["diagnostics"]?.objectValue ?? [:]
        )
    }
}
