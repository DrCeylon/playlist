import Foundation
import ResonanceCore

private struct BridgeServiceLogger {
    func debug(_ message: String) { print("[BridgeService] DEBUG: \(message)") }
}

private let bridgeServiceLogger = BridgeServiceLogger()

public enum ResonancePaths {
    public static func repoRoot(
        fileManager: FileManager = .default,
        environment: [String: String] = ProcessInfo.processInfo.environment
    ) -> URL? {
        if let configured = environment["RESONANCE_REPO_ROOT"]?.trimmingCharacters(in: .whitespacesAndNewlines),
           !configured.isEmpty {
            let url = URL(fileURLWithPath: configured)
            if containsRepoMarker(at: url, fileManager: fileManager) {
                return url
            }
        }

        var candidates: [URL] = [
            URL(fileURLWithPath: fileManager.currentDirectoryPath),
        ]
        if let executable = environment["RESONANCE_EXECUTABLE_PATH"] ?? Bundle.main.executablePath {
            candidates.append(URL(fileURLWithPath: executable).deletingLastPathComponent())
        }

        for start in candidates {
            if let root = walkUpToRepoRoot(from: start, fileManager: fileManager) {
                return root
            }
        }
        return nil
    }

    public static func resolvePythonExecutable(
        repoRoot: URL,
        fileManager: FileManager = .default
    ) -> String {
        let candidates = [
            repoRoot.appendingPathComponent(".venv/bin/python"),
            repoRoot.appendingPathComponent(".venv/bin/python3"),
            URL(fileURLWithPath: "/opt/homebrew/bin/python3.12"),
            URL(fileURLWithPath: "/usr/local/bin/python3.12"),
            URL(fileURLWithPath: "/usr/bin/python3"),
        ]
        for candidate in candidates where fileManager.isExecutableFile(atPath: candidate.path) {
            return candidate.path
        }
        return "/usr/bin/python3"
    }

    private static func walkUpToRepoRoot(from start: URL, fileManager: FileManager) -> URL? {
        var url = start
        for _ in 0..<12 {
            if containsRepoMarker(at: url, fileManager: fileManager) {
                return url
            }
            let parent = url.deletingLastPathComponent()
            if parent.path == url.path {
                break
            }
            url = parent
        }
        return nil
    }

    private static func containsRepoMarker(at url: URL, fileManager: FileManager) -> Bool {
        fileManager.fileExists(atPath: url.appendingPathComponent("playlist_builder").path)
    }
}

public struct PythonEngineBridgeConfiguration: Sendable {
    public var pythonExecutable: String
    public var workingDirectory: URL
    public var timeoutSeconds: TimeInterval
    public var useBridgeWhenAvailable: Bool

    public init(
        pythonExecutable: String = "/usr/bin/python3",
        workingDirectory: URL,
        timeoutSeconds: TimeInterval = 600,
        useBridgeWhenAvailable: Bool = true
    ) {
        self.pythonExecutable = pythonExecutable
        self.workingDirectory = workingDirectory
        self.timeoutSeconds = timeoutSeconds
        self.useBridgeWhenAvailable = useBridgeWhenAvailable
    }

    public static func automatic(
        fileManager: FileManager = .default,
        environment: [String: String] = ProcessInfo.processInfo.environment
    ) -> PythonEngineBridgeConfiguration? {
        guard let root = ResonancePaths.repoRoot(fileManager: fileManager, environment: environment) else {
            return nil
        }
        let python = ResonancePaths.resolvePythonExecutable(repoRoot: root, fileManager: fileManager)
        return PythonEngineBridgeConfiguration(pythonExecutable: python, workingDirectory: root)
    }
}

/// Immutable service wrapper around bridge transport and stateless fallback services.
public final class PythonEngineBridgeService: PlaylistGenerationServing, PlaylistImportServing, PlaylistLibraryServing, DiagnosticsServing, SessionHistoryServing, AutocompleteServing, @unchecked Sendable {
    private let transport: BridgeTransport?
    private let configuration: PythonEngineBridgeConfiguration?
    private let fallbackGeneration: MockPlaylistGenerationService
    private let fallbackImport: MockPlaylistImportService
    private let fallbackAutocomplete = MockAutocompleteService()

    public var isBridgeConfigured: Bool {
        transport != nil
    }

    public var bridgeWorkingDirectory: String? {
        configuration?.workingDirectory.path
    }

    public init(
        configuration: PythonEngineBridgeConfiguration? = PythonEngineBridgeConfiguration.automatic(),
        transport: BridgeTransport? = nil
    ) {
        self.configuration = configuration
        if let transport {
            self.transport = transport
        } else if let configuration, configuration.useBridgeWhenAvailable {
            let client = BridgeClient(
                configuration: BridgeClientConfiguration(
                    pythonExecutable: configuration.pythonExecutable,
                    workingDirectory: configuration.workingDirectory,
                    timeoutSeconds: configuration.timeoutSeconds
                )
            )
            self.transport = client
        } else {
            self.transport = nil
        }
        self.fallbackGeneration = MockPlaylistGenerationService()
        self.fallbackImport = MockPlaylistImportService()
    }

    public func validate(request: PlaylistGenerationRequest) -> ValidationResult {
        fallbackGeneration.validate(request: request)
    }

    public func generate(request: PlaylistGenerationRequest) async throws -> PlaylistGenerationResult {
        guard let transport else {
            return try await fallbackGeneration.generate(request: request)
        }
        do {
            let (response, _) = try await transport.send(
                command: .generatePlaylist,
                params: ["request": .object(BridgeContracts.generationRequestDictionary(request))]
            )
            return try BridgePayloadBuilder.generationResult(from: response.result)
        } catch let error as BridgeClientError {
            if case .processUnavailable = error {
                return try await fallbackGeneration.generate(request: request)
            }
            throw mapError(error)
        }
    }

    public func importPlaylist(
        _ result: PlaylistGenerationResult,
        onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
    ) async throws -> ImportResultState {
        guard let transport else {
            return try await fallbackImport.importPlaylist(result, onEvent: onEvent)
        }
        do {
            let playlistPayload = BridgePayloadBuilder.playlistDictionary(from: result)
            let sectionCount = result.sections.count
            onEvent(
                BridgeEventMessage(
                    id: "import-local",
                    event: .diagnostic,
                    payload: [
                        "message": .string(
                            "Import cliqué — playlist «\(result.playlistName)», \(result.trackCount) morceau(x), \(sectionCount) section(s), history_session_id=\(result.historySessionID.isEmpty ? "—" : result.historySessionID)"
                        ),
                    ]
                )
            )
            if let workingDirectory = bridgeWorkingDirectory {
                onEvent(
                    BridgeEventMessage(
                        id: "import-local",
                        event: .diagnostic,
                        payload: [
                            "message": .string(
                                "Démarrage process Python bridge (nouveau processus par commande) dans \(workingDirectory)"
                            ),
                        ]
                    )
                )
            }

            let bridgeStarted = Date()
            let (response, _) = try await transport.send(
                command: .importPlaylist,
                params: [
                    "playlist": .object(playlistPayload),
                    "sync": .bool(true),
                    "write_json_diagnostics": .bool(true),
                    "history_session_id": .string(result.historySessionID),
                ],
                onEvent: onEvent,
                onDiagnostic: { line in
                    bridgeServiceLogger.debug("Bridge stderr: \(line)")
                }
            )
            let bridgeMS = max(0, Int(Date().timeIntervalSince(bridgeStarted) * 1000))
            onEvent(
                BridgeEventMessage(
                    id: "import-local",
                    event: .diagnostic,
                    payload: [
                        "message": .string("[+\(bridgeMS) ms] Bridge Python handshake terminé"),
                    ]
                )
            )
            if let importState = try? BridgePayloadBuilder.importResult(from: response.result),
               importState.phase == .waitingForManualAcquisition {
                return importState
            }
            return try BridgePayloadBuilder.importResult(from: response.result)
        } catch let error as BridgeClientError {
            throw mapError(error)
        }
    }

    public func continueManualAcquisition(importSessionID: String) async throws -> ImportResultState {
        try await continueManualAcquisition(importSessionID: importSessionID, onEvent: { _ in })
    }

    public func continueManualAcquisition(
        importSessionID: String,
        onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
    ) async throws -> ImportResultState {
        ManualContinueTrace.log("ENTER PythonEngineBridgeService.continueManualAcquisition(importSessionID:)")
        guard let transport else {
            ManualContinueTrace.log("ERROR PythonEngineBridgeService.continueManualAcquisition — bridge unavailable")
            throw PlaylistImportError.bridgeUnavailable
        }
        ManualContinueTrace.log("CALL BridgeClient.send command=continue_manual_acquisition")
        let (response, _) = try await transport.send(
            command: .continueManualAcquisition,
            params: ["import_session_id": .string(importSessionID)],
            onEvent: onEvent,
            onDiagnostic: { line in
                bridgeServiceLogger.debug("Bridge stderr: \(line)")
            }
        )
        ManualContinueTrace.log("RETURN BridgeClient.send command=continue_manual_acquisition")
        guard let importObject = response.result["import"]?.objectValue else {
            ManualContinueTrace.log("ERROR PythonEngineBridgeService.continueManualAcquisition — invalid response")
            throw PlaylistImportError.invalidResponse
        }
        let result = try BridgePayloadBuilder.importResult(from: ["import": .object(importObject)])
        ManualContinueTrace.log("RETURN PythonEngineBridgeService.continueManualAcquisition(importSessionID:) phase=\(result.phase.rawValue)")
        return result
    }

    public func probeManualAcquisition(importSessionID: String) async throws -> ManualAcquisitionProbeResult {
        ManualContinueTrace.log("ENTER PythonEngineBridgeService.probeManualAcquisition(importSessionID:)")
        guard let transport else {
            ManualContinueTrace.log("ERROR PythonEngineBridgeService.probeManualAcquisition — bridge unavailable")
            throw PlaylistImportError.bridgeUnavailable
        }
        ManualContinueTrace.log("CALL BridgeClient.send command=probe_manual_acquisition")
        let (response, _) = try await transport.send(
            command: .probeManualAcquisition,
            params: ["import_session_id": .string(importSessionID)],
            onEvent: { _ in }
        )
        ManualContinueTrace.log("RETURN BridgeClient.send command=probe_manual_acquisition")
        let found = response.result["found"]?.boolValue ?? false
        let message = response.result["message"]?.stringValue ?? ""
        let errorCode = response.result["error_code"]?.stringValue
        let workflowPhase = response.result["workflow_phase"]?.stringValue
        let diagnostics = Self.manualProbeDiagnostics(from: response.result["diagnostics"]?.objectValue)
        let result = ManualAcquisitionProbeResult(
            found: found,
            message: message,
            errorCode: errorCode,
            workflowPhase: workflowPhase,
            diagnostics: diagnostics
        )
        ManualContinueTrace.log("RETURN PythonEngineBridgeService.probeManualAcquisition found=\(found) errorCode=\(errorCode ?? "nil")")
        return result
    }

    private static func manualProbeDiagnostics(from payload: BridgeJSONObject?) -> ManualAcquisitionProbeDiagnostics? {
        guard let payload else { return nil }
        let searchTerms = payload["search_terms"]?.arrayValue?.compactMap(\.stringValue) ?? []
        let probeError = payload["probe_error"]?.stringValue
        let probeStartedAt = Self.parseProbeTimestamp(payload["probe_started_at"])
        let probeFinishedAt = Self.parseProbeTimestamp(payload["probe_finished_at"])
        let probeDurationMs = payload["probe_duration_ms"]?.intValue
        return ManualAcquisitionProbeDiagnostics(
            importSessionID: payload["import_session_id"]?.stringValue ?? "",
            checkpointPath: payload["checkpoint_path"]?.stringValue ?? "",
            checkpointExists: payload["checkpoint_exists"]?.boolValue ?? false,
            searchTerms: searchTerms,
            providerID: payload["provider_id"]?.stringValue ?? "",
            probeError: probeError?.isEmpty == true ? nil : probeError,
            probeStartedAt: probeStartedAt,
            probeFinishedAt: probeFinishedAt,
            probeDurationMs: probeDurationMs
        )
    }

    private static func parseProbeTimestamp(_ value: BridgeJSONValue?) -> Date? {
        guard let number = value?.doubleValue ?? value?.intValue.map(Double.init) else {
            return nil
        }
        return Date(timeIntervalSince1970: number)
    }

    public func retryImportTracks(
        _ result: PlaylistGenerationResult,
        trackIndices: [Int],
        existingOutcomes: [ImportTrackOutcome]? = nil,
        historySessionID: String? = nil,
        onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
    ) async throws -> ImportResultState {
        guard let transport else {
            return try await fallbackImport.retryImportTracks(
                result,
                trackIndices: trackIndices,
                existingOutcomes: existingOutcomes,
                historySessionID: historySessionID,
                onEvent: onEvent
            )
        }
        let playlistPayload = BridgePayloadBuilder.playlistDictionary(from: result)
        var params: BridgeJSONObject = [
            "playlist": .object(playlistPayload),
            "track_indices": .array(trackIndices.map { .number(Double($0)) }),
        ]
        if let existingOutcomes, !existingOutcomes.isEmpty {
            params["existing_outcomes"] = .array(BridgePayloadBuilder.importOutcomesArray(from: existingOutcomes))
        }
        let resolvedHistorySessionID = (historySessionID ?? result.historySessionID)
            .trimmingCharacters(in: .whitespacesAndNewlines)
        if !resolvedHistorySessionID.isEmpty {
            params["history_session_id"] = .string(resolvedHistorySessionID)
        }
        let (response, _) = try await transport.send(
            command: .retryImportTracks,
            params: params,
            onEvent: onEvent,
            onDiagnostic: { line in
                bridgeServiceLogger.debug("Bridge stderr: \(line)")
            }
        )
        return try BridgePayloadBuilder.importResult(from: response.result)
    }

    public func fetchDiagnostics() async throws -> DiagnosticsSnapshot {
        guard let transport else {
            throw DiagnosticsServiceError.bridgeUnavailable
        }
        do {
            let (response, _) = try await transport.send(command: .diagnostics, params: [:])
            return try BridgePayloadBuilder.diagnosticsSnapshot(from: response.result)
        } catch let error as BridgeClientError {
            throw mapDiagnosticsError(error)
        }
    }

    public func listProviders() async throws -> [ProviderOption] {
        guard let transport else {
            return DefaultProviders.options
        }
        do {
            let (response, _) = try await transport.send(command: .listProviders, params: [:])
            return try BridgePayloadBuilder.providerOptions(from: response.result)
        } catch let error as BridgeClientError {
            throw mapDiagnosticsError(error)
        }
    }

    public func listHistory() async throws -> [SessionHistorySummary] {
        guard let transport else {
            throw SessionHistoryServiceError.bridgeUnavailable
        }
        do {
            let (response, _) = try await transport.send(command: .listHistory, params: [:])
            return BridgePayloadBuilder.historySessions(from: response.result)
        } catch let error as BridgeClientError {
            throw mapHistoryError(error)
        }
    }

    public func getHistorySession(sessionID: String) async throws -> SessionHistoryDetail? {
        guard let transport else { return nil }
        let (response, _) = try await transport.send(
            command: .getHistorySession,
            params: ["session_id": .string(sessionID)]
        )
        return BridgePayloadBuilder.historySessionDetail(from: response.result)
    }

    public func deleteHistorySession(sessionID: String) async throws -> Bool {
        guard let transport else { return false }
        let (response, _) = try await transport.send(
            command: .deleteHistorySession,
            params: ["session_id": .string(sessionID)]
        )
        return response.result["deleted"]?.boolValue ?? false
    }

    public func clearHistory() async throws -> Bool {
        guard let transport else { return false }
        let (response, _) = try await transport.send(command: .clearHistory, params: [:])
        return response.result["cleared"]?.boolValue ?? false
    }

    public func replayGeneration(sessionID: String) async throws -> PlaylistGenerationResult {
        guard let transport else {
            throw DiagnosticsServiceError.bridgeUnavailable
        }
        let (response, _) = try await transport.send(
            command: .replayGeneration,
            params: ["session_id": .string(sessionID)]
        )
        return try BridgePayloadBuilder.generationResult(from: response.result)
    }

    public func exportHistorySession(sessionID: String) async throws -> SessionHistoryExport? {
        guard let transport else { return nil }
        let (response, _) = try await transport.send(
            command: .exportHistorySession,
            params: ["session_id": .string(sessionID)]
        )
        return BridgePayloadBuilder.exportHistorySession(from: response.result)
    }

    public func listManagedPlaylists() async throws -> [ManagedPlaylistSummary] {
        guard let transport else {
            return DefaultManagedPlaylists.samples
        }
        let (response, _) = try await transport.send(command: .listManagedPlaylists, params: [:])
        return BridgePayloadBuilder.managedPlaylists(from: response.result)
    }

    public func getManagedPlaylist(localPlaylistID: String) async throws -> ManagedPlaylistDetail? {
        guard let transport else {
            return try await MockPlaylistLibraryService().getManagedPlaylist(localPlaylistID: localPlaylistID)
        }
        let (response, _) = try await transport.send(
            command: .getManagedPlaylist,
            params: ["local_playlist_id": .string(localPlaylistID)]
        )
        return BridgePayloadBuilder.managedPlaylistDetail(from: response.result)
    }

    public func syncManagedPlaylist(_ request: PlaylistSyncRequest) async throws -> PlaylistSyncResult {
        guard let transport else {
            return try await MockPlaylistLibraryService().syncManagedPlaylist(request)
        }
        let (response, _) = try await transport.send(
            command: .syncManagedPlaylist,
            params: [
                "local_playlist_id": .string(request.localPlaylistID),
                "direction": .string(request.direction.rawValue),
                "provider_id": .string(request.providerID.rawValue),
            ]
        )
        guard let result = BridgePayloadBuilder.playlistSyncResult(from: response.result) else {
            throw PlaylistImportError.invalidResponse
        }
        return result
    }

    public func planSync(_ request: PlaylistSyncPlanRequest) async throws -> PlaylistSyncPlan? {
        guard let transport else {
            return nil
        }
        var params: BridgeJSONObject = [
            "local_playlist_id": .string(request.localPlaylistID),
            "provider_id": .string(request.providerID.rawValue),
            "direction": .string(request.direction.rawValue),
            "sync_mode": .string(request.syncMode.rawValue),
        ]
        if !request.remotePlaylistID.isEmpty {
            params["remote_playlist_id"] = .string(request.remotePlaylistID)
        }
        let (response, _) = try await transport.send(command: .planSync, params: params)
        return BridgePayloadBuilder.playlistSyncPlan(from: response.result)
    }

    public func search(request: AutocompleteRequest) async throws -> AutocompleteResponse {
        guard let transport else {
            return try await fallbackAutocomplete.search(request: request)
        }
        do {
            let (response, _) = try await transport.send(
                command: .autocompleteSearch,
                params: AutocompleteBridgeContracts.requestDictionary(request)
            )
            return AutocompleteBridgeContracts.parseResponse(response.result, entityKind: request.entityKind)
        } catch let error as BridgeClientError {
            if case .processUnavailable = error {
                return try await fallbackAutocomplete.search(request: request)
            }
            throw mapAutocompleteError(error)
        }
    }

    private func mapAutocompleteError(_ error: BridgeClientError) -> AutocompleteServiceError {
        switch error {
        case .bridge(let payload):
            return .bridge(payload)
        case .processUnavailable, .bridgeUnavailable:
            return .bridgeUnavailable
        case .timeout:
            return .timeout
        case .invalidResponse:
            return .invalidResponse
        }
    }

    private func mapDiagnosticsError(_ error: BridgeClientError) -> DiagnosticsServiceError {
        switch error {
        case .bridge(let payload):
            return .bridge(payload)
        case .processUnavailable, .bridgeUnavailable:
            return .bridgeUnavailable
        case .timeout:
            return .timeout
        case .invalidResponse:
            return .invalidResponse
        }
    }

    private func mapHistoryError(_ error: BridgeClientError) -> SessionHistoryServiceError {
        switch error {
        case .bridge(let payload):
            return .bridge(payload)
        case .processUnavailable, .bridgeUnavailable:
            return .bridgeUnavailable
        case .timeout:
            return .timeout
        case .invalidResponse:
            return .invalidResponse
        }
    }

    private func mapError(_ error: BridgeClientError) -> Error {
        switch error {
        case .bridge(let payload):
            return PlaylistImportError.bridge(payload)
        case .processUnavailable:
            return PlaylistImportError.bridgeUnavailable
        case .timeout:
            return PlaylistImportError.timeout
        case .invalidResponse, .bridgeUnavailable:
            return PlaylistImportError.invalidResponse
        }
    }
}

public enum AutocompleteServiceError: Error, Equatable, Sendable {
    case bridgeUnavailable
    case timeout
    case invalidResponse
    case bridge(BridgeErrorPayload)
}
