import Foundation
private struct BridgeRuntimeLogger {
    let category: String

    func info(_ message: String) { print("[\(category)] INFO: \(message)") }
    func warning(_ message: String) { print("[\(category)] WARN: \(message)") }
    func debug(_ message: String) { print("[\(category)] DEBUG: \(message)") }
}

private let bridgeLogger = BridgeRuntimeLogger(category: "Bridge")

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
        timeoutSeconds: TimeInterval = 600,
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
        let bridgeStarted = Date()
        let requestLine = try Self.encodeJSONObject(payload)
        if command == .probeManualAcquisition || command == .continueManualAcquisition {
            ManualContinueTrace.log("ENTER BridgeClient.send command=\(command.rawValue) request_id=\(requestID)")
            ManualContinueTrace.log("Bridge request JSON sent: \(requestLine)")
        }
        bridgeLogger.info("Bridge send \(command.rawValue) id=\(requestID)")
        let lines = try await runProcess(requestLine: requestLine) { line in
            Self.dispatchStreamingLine(
                line: line,
                requestID: requestID,
                onEvent: onEvent,
                onDiagnostic: onDiagnostic
            )
        } onStderrLine: { line in
            if line.hasPrefix("resonance-perf:") {
                bridgeLogger.info(line)
                return
            }
            let message = "[stderr] \(line)"
            bridgeLogger.warning(message)
            onDiagnostic?(message)
        }
        let bridgeRoundTripMS = max(0, Int(Date().timeIntervalSince(bridgeStarted) * 1000))
        let conversation = try Self.parseConversation(requestID: requestID, lines: lines)
        if command == .probeManualAcquisition || command == .continueManualAcquisition {
            ManualContinueTrace.log(
                "RETURN BridgeClient.send command=\(command.rawValue) round_trip_ms=\(bridgeRoundTripMS) ok=\(conversation.response.ok)"
            )
        }
        bridgeLogger.info(
            "resonance-perf: {\"phase\":\"bridge\",\"operation\":\"swift_round_trip\",\"duration_ms\":\(bridgeRoundTripMS),\"metadata\":{\"command\":\"\(command.rawValue)\"}}"
        )
        return conversation
    }

    static func dispatchStreamingLine(
        line: String,
        requestID: String,
        onEvent: (@Sendable (BridgeEventMessage) -> Void)?,
        onDiagnostic: (@Sendable (String) -> Void)?
    ) {
        let trimmed = line.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        bridgeLogger.debug("Bridge stdout: \(trimmed)")

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
                    "Bridge stdout ignored (non-JSON): \(line)"
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
                "Bridge conversation skipped \(skippedNonJSONLines) non-JSON stdout line(s)"
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

            let processStarted = Date()
            do {
                try process.run()
            } catch {
                continuation.resume(throwing: BridgeClientError.processUnavailable)
                return
            }

            let processSpawnMS = max(0, Int(Date().timeIntervalSince(processStarted) * 1000))
            bridgeLogger.info("Bridge process started pid=\(process.processIdentifier) spawn_ms=\(processSpawnMS)")
            bridgeLogger.info(
                "resonance-perf: {\"phase\":\"bridge\",\"operation\":\"process_spawn\",\"duration_ms\":\(processSpawnMS)}"
            )

            if let data = (requestLine + "\n").data(using: .utf8) {
                inputPipe.fileHandleForWriting.write(data)
            }
            inputPipe.fileHandleForWriting.closeFile()

            let streamCollector = ProcessStreamCollector(
                onStdoutLine: onStdoutLine,
                onStderrLine: onStderrLine
            )
            let runState = BridgeProcessRunState()
            let deadline = Date().addingTimeInterval(self.configuration.timeoutSeconds)

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

    public static func importOutcomesArray(from outcomes: [ImportTrackOutcome]) -> [BridgeJSONValue] {
        outcomes.map { item in
            .object([
                "artist": .string(item.artist),
                "title": .string(item.title),
                "section": .string(item.section),
                "status": .string(item.status.rawValue),
                "message": .string(item.message),
            ])
        }
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
                message: item["message"]?.stringValue ?? "",
                album: item["album"]?.stringValue ?? "",
                catalogURL: item["catalog_url"]?.stringValue ?? ""
            )
        }
        let historySessionID = payload["history_session_id"]?.stringValue ?? ""
        return ImportResultState(
            playlistName: playlistName,
            outcomes: outcomes,
            phase: phase,
            historySessionID: historySessionID,
            importSessionID: importObject["import_session_id"]?.stringValue ?? "",
            manualToken: importObject["manual_token"]?.stringValue ?? "",
            manualArtist: importObject["manual_artist"]?.stringValue ?? "",
            manualTitle: importObject["manual_title"]?.stringValue ?? "",
            manualInstructions: importObject["manual_instructions"]?.stringValue ?? "",
            manualCatalogLabel: importObject["manual_catalog_label"]?.stringValue ?? "",
            manualCatalogURL: importObject["manual_catalog_url"]?.stringValue ?? "",
            manualAlbum: importObject["manual_album"]?.stringValue ?? ""
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
            historySessionID: payload["history_session_id"]?.stringValue ?? "",
            targetTrackCount: generation["target_track_count"]?.intValue,
            shortfallMessage: generation["shortfall_message"]?.stringValue ?? ""
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
        let capabilitiesRaw = object["capabilities"]?.arrayValue ?? []
        let capabilities = capabilitiesRaw.compactMap { item -> ProviderCapability? in
            guard let raw = item.stringValue else { return nil }
            return ProviderCapability(rawValue: raw)
        }
        return ProviderOption(
            providerID: ProviderID(rawValue: providerRaw) ?? .appleMusic,
            displayName: object["display_name"]?.stringValue ?? providerRaw,
            isAvailable: object["is_available"]?.boolValue ?? false,
            isConnected: object["is_connected"]?.boolValue ?? false,
            unavailableReason: object["unavailable_reason"]?.stringValue ?? "",
            capabilities: capabilities,
            isExperimental: object["is_experimental"]?.boolValue ?? false
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

    public static func managedPlaylists(from payload: BridgeJSONObject) -> [ManagedPlaylistSummary] {
        let playlistsRaw = payload["playlists"]?.arrayValue ?? []
        return playlistsRaw.compactMap(\.objectValue).map(managedPlaylistSummary)
    }

    public static func managedPlaylistDetail(from payload: BridgeJSONObject) -> ManagedPlaylistDetail? {
        guard let object = payload["playlist"]?.objectValue else { return nil }
        let summary = managedPlaylistSummary(object)
        let tracksRaw = object["tracks"]?.arrayValue ?? []
        let tracks = tracksRaw.compactMap(\.objectValue).map(managedPlaylistTrack)
        let conflictsRaw = object["sync_conflicts"]?.arrayValue ?? []
        let conflicts = conflictsRaw.compactMap(\.objectValue).map(syncConflict)
        return ManagedPlaylistDetail(summary: summary, tracks: tracks, syncConflicts: conflicts)
    }

    public static func playlistSyncResult(from payload: BridgeJSONObject) -> PlaylistSyncResult? {
        guard let object = payload["sync"]?.objectValue else { return nil }
        let conflictsRaw = object["conflicts"]?.arrayValue ?? []
        let conflicts = conflictsRaw.compactMap(\.objectValue).map(syncConflict)
        let statusRaw = object["sync_status"]?.stringValue ?? PlaylistSyncStatus.pending.rawValue
        return PlaylistSyncResult(
            localPlaylistID: object["local_playlist_id"]?.stringValue ?? "",
            syncStatus: PlaylistSyncStatus(rawValue: statusRaw) ?? .pending,
            message: object["message"]?.stringValue ?? "",
            conflicts: conflicts
        )
    }

    private static func managedPlaylistSummary(_ object: BridgeJSONObject) -> ManagedPlaylistSummary {
        let providerRaw = object["provider_id"]?.stringValue ?? ProviderID.appleMusic.rawValue
        let syncRaw = object["sync_status"]?.stringValue ?? PlaylistSyncStatus.unknown.rawValue
        let sourceRaw = object["source_kind"]?.stringValue ?? PlaylistSourceKind.localSnapshot.rawValue
        let importStatusRaw = object["import_status"]?.stringValue
        let originRaw = object["origin"]?.stringValue ?? PlaylistOrigin.generated.rawValue
        let refsRaw = object["linked_remote_refs"]?.arrayValue ?? []
        let linkedRefs = refsRaw.compactMap(\.objectValue).map(linkedRemoteRef)
        return ManagedPlaylistSummary(
            localPlaylistID: object["local_playlist_id"]?.stringValue ?? "",
            name: object["name"]?.stringValue ?? "",
            providerID: ProviderID(rawValue: providerRaw) ?? .appleMusic,
            trackCount: object["track_count"]?.intValue ?? 0,
            syncStatus: PlaylistSyncStatus(rawValue: syncRaw) ?? .unknown,
            lastSyncedAtISO: object["last_synced_at_iso"]?.stringValue ?? "",
            providerPlaylistID: object["provider_playlist_id"]?.stringValue ?? "",
            sourceKind: PlaylistSourceKind(rawValue: sourceRaw) ?? .localSnapshot,
            importStatus: importStatusRaw.flatMap(SessionHistoryStatus.init(rawValue:)),
            historySessionID: object["history_session_id"]?.stringValue ?? "",
            origin: PlaylistOrigin(rawValue: originRaw) ?? .generated,
            playlistVersion: object["playlist_version"]?.intValue ?? 1,
            linkedRemoteRefs: linkedRefs,
            createdAtISO: object["created_at_iso"]?.stringValue ?? "",
            updatedAtISO: object["updated_at_iso"]?.stringValue ?? ""
        )
    }

    private static func linkedRemoteRef(_ object: BridgeJSONObject) -> LinkedRemoteRef {
        let providerRaw = object["provider_id"]?.stringValue ?? ProviderID.appleMusic.rawValue
        return LinkedRemoteRef(
            providerID: ProviderID(rawValue: providerRaw) ?? .appleMusic,
            remotePlaylistID: object["remote_playlist_id"]?.stringValue ?? "",
            snapshotChecksum: object["snapshot_checksum"]?.stringValue ?? "",
            syncState: object["sync_state"]?.stringValue ?? "",
            lastSyncAt: object["last_sync_at"]?.stringValue ?? ""
        )
    }

    public static func remotePlaylistSnapshotJSONObject(_ snapshot: RemotePlaylistSnapshot) -> BridgeJSONObject {
        [
            "provider_id": .string(snapshot.providerID.rawValue),
            "remote_playlist_id": .string(snapshot.remotePlaylistID),
            "name": .string(snapshot.name),
            "snapshot_at_iso": .string(snapshot.snapshotAtISO),
            "track_count": .number(Double(snapshot.trackCount)),
            "checksum": .string(snapshot.checksum),
            "source_kind": .string(snapshot.sourceKind.rawValue),
            "source_url": .string(snapshot.sourceURL),
            "tracks": .array(snapshot.tracks.map(remotePlaylistTrackJSONObject)),
        ]
    }

    private static func remotePlaylistTrackJSONObject(_ track: RemotePlaylistTrack) -> BridgeJSONValue {
        .object([
            "remote_track_id": .string(track.remoteTrackID),
            "artist": .string(track.artist),
            "title": .string(track.title),
            "album": .string(track.album),
            "duration_ms": .number(Double(track.durationMS)),
            "position": .number(Double(track.position)),
            "provider_metadata": .object(track.providerMetadata.mapValues { .string($0) }),
        ])
    }

    private static func managedPlaylistTrack(_ object: BridgeJSONObject) -> ManagedPlaylistTrack {
        let mappingRaw = object["mapping_status"]?.stringValue ?? PlaylistTrackMappingStatus.matched.rawValue
        return ManagedPlaylistTrack(
            localTrackID: object["local_track_id"]?.stringValue ?? "",
            providerTrackID: object["provider_track_id"]?.stringValue ?? "",
            artist: object["artist"]?.stringValue ?? "",
            title: object["title"]?.stringValue ?? "",
            section: object["section"]?.stringValue ?? "",
            mappingStatus: PlaylistTrackMappingStatus(rawValue: mappingRaw) ?? .matched
        )
    }

    private static func syncConflict(_ object: BridgeJSONObject) -> PlaylistSyncConflict {
        let kindRaw = object["kind"]?.stringValue ?? PlaylistTrackMappingStatus.unresolved.rawValue
        return PlaylistSyncConflict(
            id: object["id"]?.stringValue ?? "",
            trackKey: object["track_key"]?.stringValue ?? "",
            kind: PlaylistTrackMappingStatus(rawValue: kindRaw) ?? .unresolved,
            message: object["message"]?.stringValue ?? ""
        )
    }

    public static func remotePlaylists(from payload: BridgeJSONObject) -> [RemotePlaylist] {
        let playlistsRaw = payload["remote_playlists"]?.arrayValue ?? []
        return playlistsRaw.compactMap(\.objectValue).map(remotePlaylist)
    }

    public static func remotePlaylistSnapshot(from payload: BridgeJSONObject) -> RemotePlaylistSnapshot? {
        guard let object = payload["remote_playlist"]?.objectValue else { return nil }
        return remotePlaylistSnapshotObject(object)
    }

    public static func remoteProviderAccounts(from payload: BridgeJSONObject) -> [RemoteProviderAccount] {
        let accountsRaw = payload["provider_accounts"]?.arrayValue ?? []
        return accountsRaw.compactMap(\.objectValue).map(remoteProviderAccount)
    }

    public static func providerAuthState(from payload: BridgeJSONObject) -> ProviderAuthState? {
        guard let raw = payload["auth_state"]?.stringValue else { return nil }
        return ProviderAuthState(rawValue: raw)
    }

    public static func playlistSyncPlan(from payload: BridgeJSONObject) -> PlaylistSyncPlan? {
        guard let object = payload["sync_plan"]?.objectValue else { return nil }
        return playlistSyncPlanObject(object)
    }

    private static func remotePlaylist(_ object: BridgeJSONObject) -> RemotePlaylist {
        let providerRaw = object["provider_id"]?.stringValue ?? ProviderID.appleMusic.rawValue
        return RemotePlaylist(
            providerID: ProviderID(rawValue: providerRaw) ?? .appleMusic,
            remotePlaylistID: object["remote_playlist_id"]?.stringValue ?? "",
            name: object["name"]?.stringValue ?? "",
            trackCount: object["track_count"]?.intValue ?? 0,
            isPublic: object["is_public"]?.boolValue ?? false,
            ownerLabel: object["owner_label"]?.stringValue ?? "",
            snapshotAtISO: object["snapshot_at_iso"]?.stringValue ?? "",
            sourceURL: object["source_url"]?.stringValue ?? ""
        )
    }

    private static func playlistSyncPlanObject(_ object: BridgeJSONObject) -> PlaylistSyncPlan {
        let providerRaw = object["target_provider_id"]?.stringValue ?? ProviderID.appleMusic.rawValue
        let directionRaw = object["direction"]?.stringValue ?? PlaylistSyncDirection.pullFromProvider.rawValue
        let modeRaw = object["sync_mode"]?.stringValue ?? SyncMode.dryRun.rawValue
        let actionsRaw = object["actions"]?.arrayValue ?? []
        let actions = actionsRaw.compactMap(\.objectValue).map(playlistSyncAction)
        let conflictsRaw = object["conflicts"]?.arrayValue ?? []
        let conflicts = conflictsRaw.compactMap(\.objectValue).map(syncConflict)
        let summaryObject = object["summary"]?.objectValue ?? [:]
        return PlaylistSyncPlan(
            localPlaylistID: object["local_playlist_id"]?.stringValue ?? "",
            targetProviderID: ProviderID(rawValue: providerRaw) ?? .appleMusic,
            direction: PlaylistSyncDirection(rawValue: directionRaw) ?? .pullFromProvider,
            syncMode: SyncMode(rawValue: modeRaw) ?? .dryRun,
            remotePlaylistID: object["remote_playlist_id"]?.stringValue ?? "",
            playlistNameLocal: object["playlist_name_local"]?.stringValue ?? "",
            playlistNameRemote: object["playlist_name_remote"]?.stringValue ?? "",
            actions: actions,
            conflicts: conflicts,
            summary: playlistSyncSummary(summaryObject)
        )
    }

    private static func playlistSyncAction(_ object: BridgeJSONObject) -> PlaylistSyncAction {
        let kindRaw = object["kind"]?.stringValue ?? PlaylistSyncActionKind.addTrack.rawValue
        return PlaylistSyncAction(
            kind: PlaylistSyncActionKind(rawValue: kindRaw) ?? .addTrack,
            trackKey: object["track_key"]?.stringValue ?? "",
            artist: object["artist"]?.stringValue ?? "",
            title: object["title"]?.stringValue ?? "",
            message: object["message"]?.stringValue ?? "",
            localTrackID: object["local_track_id"]?.stringValue ?? "",
            remoteTrackID: object["remote_track_id"]?.stringValue ?? "",
            sourcePosition: object["source_position"]?.intValue,
            targetPosition: object["target_position"]?.intValue
        )
    }

    private static func playlistSyncSummary(_ object: BridgeJSONObject) -> PlaylistSyncSummary {
        PlaylistSyncSummary(
            additions: object["additions"]?.intValue ?? 0,
            removals: object["removals"]?.intValue ?? 0,
            alreadyPresent: object["already_present"]?.intValue ?? 0,
            metadataMismatches: object["metadata_mismatches"]?.intValue ?? 0,
            reorders: object["reorders"]?.intValue ?? 0,
            conflicts: object["conflicts"]?.intValue ?? 0,
            renameRequired: object["rename_required"]?.boolValue ?? false
        )
    }

    private static func remotePlaylistSnapshotObject(_ object: BridgeJSONObject) -> RemotePlaylistSnapshot {
        let providerRaw = object["provider_id"]?.stringValue ?? ProviderID.appleMusic.rawValue
        let sourceRaw = object["source_kind"]?.stringValue ?? PlaylistSourceKind.providerLibrary.rawValue
        let tracksRaw = object["tracks"]?.arrayValue ?? []
        let tracks = tracksRaw.compactMap(\.objectValue).map(remotePlaylistTrack)
        return RemotePlaylistSnapshot(
            providerID: ProviderID(rawValue: providerRaw) ?? .appleMusic,
            remotePlaylistID: object["remote_playlist_id"]?.stringValue ?? "",
            name: object["name"]?.stringValue ?? "",
            snapshotAtISO: object["snapshot_at_iso"]?.stringValue ?? "",
            tracks: tracks,
            trackCount: object["track_count"]?.intValue ?? tracks.count,
            checksum: object["checksum"]?.stringValue ?? "",
            sourceKind: PlaylistSourceKind(rawValue: sourceRaw) ?? .providerLibrary,
            sourceURL: object["source_url"]?.stringValue ?? ""
        )
    }

    private static func remotePlaylistTrack(_ object: BridgeJSONObject) -> RemotePlaylistTrack {
        let metadataRaw = object["provider_metadata"]?.objectValue ?? [:]
        let metadata = metadataRaw.reduce(into: [String: String]()) { result, pair in
            if let value = pair.value.stringValue {
                result[pair.key] = value
            }
        }
        return RemotePlaylistTrack(
            remoteTrackID: object["remote_track_id"]?.stringValue ?? "",
            artist: object["artist"]?.stringValue ?? "",
            title: object["title"]?.stringValue ?? "",
            album: object["album"]?.stringValue ?? "",
            durationMS: object["duration_ms"]?.intValue ?? 0,
            position: object["position"]?.intValue ?? 0,
            providerMetadata: metadata
        )
    }

    private static func remoteProviderAccount(_ object: BridgeJSONObject) -> RemoteProviderAccount {
        let providerRaw = object["provider_id"]?.stringValue ?? ProviderID.appleMusic.rawValue
        let authRaw = object["auth_state"]?.stringValue ?? ProviderAuthState.disconnected.rawValue
        let capabilitiesRaw = object["capabilities"]?.arrayValue ?? []
        let capabilities = capabilitiesRaw.compactMap { item -> ProviderCapability? in
            guard let raw = item.stringValue else { return nil }
            return ProviderCapability(rawValue: raw)
        }
        return RemoteProviderAccount(
            providerID: ProviderID(rawValue: providerRaw) ?? .appleMusic,
            displayName: object["display_name"]?.stringValue ?? "",
            authState: ProviderAuthState(rawValue: authRaw) ?? .disconnected,
            lastConnectedAtISO: object["last_connected_at_iso"]?.stringValue ?? "",
            capabilities: capabilities
        )
    }
}
