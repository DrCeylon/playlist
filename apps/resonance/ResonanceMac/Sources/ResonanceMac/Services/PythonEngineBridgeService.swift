import Foundation
import ResonanceCore

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
        timeoutSeconds: TimeInterval = 180,
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
public final class PythonEngineBridgeService: PlaylistGenerationServing, PlaylistImportServing, DiagnosticsServing, SessionHistoryServing, @unchecked Sendable {
    private let transport: BridgeTransport?
    private let configuration: PythonEngineBridgeConfiguration?
    private let fallbackGeneration: MockPlaylistGenerationService
    private let fallbackImport: MockPlaylistImportService

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
                            "message": .string("Lancement process Python bridge dans \(workingDirectory)"),
                        ]
                    )
                )
            }

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
                    onEvent(
                        BridgeEventMessage(
                            id: "import-bridge",
                            event: .diagnostic,
                            payload: ["message": .string(line)]
                        )
                    )
                }
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
        guard let transport else {
            throw PlaylistImportError.bridgeUnavailable
        }
        let (response, _) = try await transport.send(
            command: .continueManualAcquisition,
            params: ["import_session_id": .string(importSessionID)]
        )
        guard let importObject = response.result["import"]?.objectValue else {
            throw PlaylistImportError.invalidResponse
        }
        return try BridgePayloadBuilder.importResult(from: ["import": .object(importObject)])
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

public enum PlaylistImportError: Error, Equatable {
    case bridgeUnavailable
    case timeout
    case invalidResponse
    case bridge(BridgeErrorPayload)
}
