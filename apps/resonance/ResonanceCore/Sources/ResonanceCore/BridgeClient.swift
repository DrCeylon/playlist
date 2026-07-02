import Foundation

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

public protocol BridgeTransport: Sendable {
    func send(command: BridgeCommand, requestID: String, params: [String: Any]) async throws -> (
        response: BridgeResponseMessage,
        events: [BridgeEventMessage]
    )
}

public extension BridgeTransport {
    /// Convenience helper used by ResonanceMac call sites; removable if callers pass full arguments.
    func send(
        command: BridgeCommand,
        requestID: String = UUID().uuidString,
        params: [String: Any] = [:]
    ) async throws -> (response: BridgeResponseMessage, events: [BridgeEventMessage]) {
        try await send(command: command, requestID: requestID, params: params)
    }
}

public final class BridgeClient: BridgeTransport, @unchecked Sendable {
    private let configuration: BridgeClientConfiguration
    private let lock = NSLock()

    public init(configuration: BridgeClientConfiguration) {
        self.configuration = configuration
    }

    public func send(
        command: BridgeCommand,
        requestID: String = UUID().uuidString,
        params: [String: Any] = [:]
    ) async throws -> (response: BridgeResponseMessage, events: [BridgeEventMessage]) {
        let payload: [String: Any] = [
            "id": requestID,
            "command": command.rawValue,
            "params": params,
        ]
        let requestLine = try Self.encodeJSONObject(payload)
        let lines = try await runProcess(requestLine: requestLine)
        return try Self.parseConversation(requestID: requestID, lines: lines)
    }

    static func parseConversation(
        requestID: String,
        lines: [String]
    ) throws -> (response: BridgeResponseMessage, events: [BridgeEventMessage]) {
        var events: [BridgeEventMessage] = []
        var response: BridgeResponseMessage?
        for line in lines where !line.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            let object = try BridgeResponseParser.parseJSONObject(line)
            if object["type"] as? String == "event" {
                events.append(try BridgeResponseParser.parseEventLine(line))
                continue
            }
            if object["type"] as? String == "response", object["id"] as? String == requestID {
                response = try BridgeResponseParser.parseResponseLine(line)
            }
        }
        guard let response else {
            throw BridgeClientError.invalidResponse
        }
        if !response.ok, let error = response.error {
            throw BridgeClientError.bridge(error)
        }
        return (response, events)
    }

    private func runProcess(requestLine: String) async throws -> [String] {
        try await withCheckedThrowingContinuation { continuation in
            lock.lock()
            defer { lock.unlock() }

            let process = Process()
            process.executableURL = URL(fileURLWithPath: configuration.pythonExecutable)
            process.arguments = ["-m", configuration.moduleName]
            process.currentDirectoryURL = configuration.workingDirectory

            var environment = ProcessInfo.processInfo.environment
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

            if let data = (requestLine + "\n").data(using: .utf8) {
                inputPipe.fileHandleForWriting.write(data)
            }
            inputPipe.fileHandleForWriting.closeFile()

            let deadline = Date().addingTimeInterval(configuration.timeoutSeconds)
            DispatchQueue.global().async {
                while process.isRunning && Date() < deadline {
                    Thread.sleep(forTimeInterval: 0.05)
                }
                if process.isRunning {
                    process.terminate()
                    continuation.resume(throwing: BridgeClientError.timeout)
                    return
                }

                let outputData = outputPipe.fileHandleForReading.readDataToEndOfFile()
                let text = String(decoding: outputData, as: UTF8.self)
                let lines = text.split(separator: "\n", omittingEmptySubsequences: false).map(String.init)
                continuation.resume(returning: lines)
            }
        }
    }

    static func encodeJSONObject(_ object: [String: Any]) throws -> String {
        let data = try JSONSerialization.data(withJSONObject: object)
        guard let line = String(data: data, encoding: .utf8) else {
            throw BridgeClientError.invalidResponse
        }
        return line
    }
}

public enum BridgePayloadBuilder {
    public static func playlistDictionary(from result: PlaylistGenerationResult) -> [String: Any] {
        [
            "name": result.playlistName,
            "description": "Importée depuis Resonance.",
            "sections": result.sections.map { section in
                [
                    "name": section.name,
                    "tracks": section.tracks.map { track in
                        [
                            "artist": track.artist,
                            "title": track.title,
                            "section": track.section,
                        ]
                    },
                ]
            },
        ]
    }

    public static func importResult(from payload: [String: Any]) throws -> ImportResultState {
        guard let importObject = payload["import"] as? [String: Any] else {
            throw BridgeClientError.invalidResponse
        }
        let playlistName = importObject["playlist_name"] as? String ?? ""
        let phaseRaw = importObject["phase"] as? String ?? ImportPhase.completed.rawValue
        let phase = ImportPhase(rawValue: phaseRaw) ?? .completed
        let outcomesRaw = importObject["outcomes"] as? [[String: Any]] ?? []
        let outcomes = outcomesRaw.map { item in
            ImportTrackOutcome(
                artist: item["artist"] as? String ?? "",
                title: item["title"] as? String ?? "",
                section: item["section"] as? String ?? "",
                status: ImportTrackStatus(rawValue: item["status"] as? String ?? "") ?? .error,
                message: item["message"] as? String ?? ""
            )
        }
        return ImportResultState(playlistName: playlistName, outcomes: outcomes, phase: phase)
    }

    public static func generationResult(from payload: [String: Any]) throws -> PlaylistGenerationResult {
        guard let generation = payload["generation"] as? [String: Any] else {
            throw BridgeClientError.invalidResponse
        }
        let playlistName = generation["playlist_name"] as? String ?? ""
        let averageScore = generation["average_score"] as? Double ?? 0
        let providerRaw = generation["provider_id"] as? String ?? ProviderID.appleMusic.rawValue
        let providerID = ProviderID(rawValue: providerRaw) ?? .appleMusic
        let sectionsRaw = generation["sections"] as? [[String: Any]] ?? []
        let sections = sectionsRaw.map { section in
            let tracksRaw = section["tracks"] as? [[String: Any]] ?? []
            let tracks = tracksRaw.map { track in
                GeneratedTrackPreview(
                    artist: track["artist"] as? String ?? "",
                    title: track["title"] as? String ?? "",
                    section: track["section"] as? String ?? "",
                    score: track["score"] as? Double ?? 0,
                    confidence: ConfidenceLevel(rawValue: track["confidence"] as? String ?? "") ?? .medium,
                    source: track["source"] as? String ?? ""
                )
            }
            return GeneratedSectionPreview(
                name: section["name"] as? String ?? "Playlist",
                tracks: tracks
            )
        }
        return PlaylistGenerationResult(
            playlistName: playlistName,
            sections: sections,
            averageScore: averageScore,
            providerID: providerID
        )
    }

    public static func diagnosticsSnapshot(from payload: [String: Any]) throws -> DiagnosticsSnapshot {
        let engineVersion = payload["engine_version"] as? String ?? ""
        guard let summaryObject = payload["summary"] as? [String: Any] else {
            throw BridgeClientError.invalidResponse
        }
        let summary = try diagnosticsSummary(from: summaryObject)
        let eventsRaw = payload["events"] as? [[String: Any]] ?? []
        let events = eventsRaw.map(diagnosticEvent)
        return DiagnosticsSnapshot(engineVersion: engineVersion, summary: summary, events: events)
    }

    public static func providerOptions(from payload: [String: Any]) throws -> [ProviderOption] {
        let providersRaw = payload["providers"] as? [[String: Any]] ?? []
        return providersRaw.map(providerOption)
    }

    private static func diagnosticsSummary(from object: [String: Any]) throws -> DiagnosticsSummary {
        let providersRaw = object["active_providers"] as? [[String: Any]] ?? []
        let reportsRaw = object["recent_reports"] as? [[String: Any]] ?? []
        return DiagnosticsSummary(
            bridgeStatus: object["bridge_status"] as? String ?? "unknown",
            platform: object["platform"] as? String ?? "",
            executionMS: object["execution_ms"] as? Int ?? 0,
            catalogCacheEntries: object["catalog_cache_entries"] as? Int ?? 0,
            identityCacheEntries: object["identity_cache_entries"] as? Int ?? 0,
            catalogCacheEnabled: object["catalog_cache_enabled"] as? Bool ?? false,
            countryCode: object["country_code"] as? String ?? "",
            activeProviders: providersRaw.map(providerOption),
            recentReports: reportsRaw.map(reportSummary),
            reportsDirectory: object["reports_directory"] as? String ?? ""
        )
    }

    private static func providerOption(_ object: [String: Any]) -> ProviderOption {
        let providerRaw = object["provider_id"] as? String ?? ProviderID.appleMusic.rawValue
        return ProviderOption(
            providerID: ProviderID(rawValue: providerRaw) ?? .appleMusic,
            displayName: object["display_name"] as? String ?? providerRaw,
            isAvailable: object["is_available"] as? Bool ?? false,
            isConnected: object["is_connected"] as? Bool ?? false,
            unavailableReason: object["unavailable_reason"] as? String ?? ""
        )
    }

    private static func reportSummary(_ object: [String: Any]) -> DiagnosticsReportSummary {
        let trackSummary = object["track_summary"] as? [String: Any] ?? [:]
        return DiagnosticsReportSummary(
            filename: object["filename"] as? String ?? "",
            playlistName: object["playlist_name"] as? String ?? "",
            generatedAt: object["generated_at"] as? String ?? "",
            added: trackSummary["added"] as? Int ?? 0,
            notFound: trackSummary["not_found"] as? Int ?? 0,
            skipped: trackSummary["skipped"] as? Int ?? 0,
            errors: trackSummary["errors"] as? Int ?? 0
        )
    }

    private static func diagnosticEvent(_ object: [String: Any]) -> DiagnosticEvent {
        let payloadRaw = object["payload"] as? [Any] ?? []
        let payload = payloadRaw.compactMap { item -> DiagnosticEventPayload? in
            if let dict = item as? [String: Any],
               let key = dict["key"] as? String,
               let value = dict["value"] as? String {
                return DiagnosticEventPayload(key: key, value: value)
            }
            if let pair = item as? [Any], pair.count == 2,
               let key = pair[0] as? String,
               let value = pair[1] as? String {
                return DiagnosticEventPayload(key: key, value: value)
            }
            return nil
        }
        let levelRaw = object["level"] as? String ?? DiagnosticLevel.info.rawValue
        return DiagnosticEvent(
            phase: object["phase"] as? String ?? "",
            message: object["message"] as? String ?? "",
            level: DiagnosticLevel(rawValue: levelRaw) ?? .info,
            timestampISO: object["timestamp_iso"] as? String ?? "",
            payload: payload
        )
    }
}
