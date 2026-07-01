import Foundation

public enum ResonancePaths {
    public static func repoRoot(
        fileManager: FileManager = .default,
        startingAt: URL = URL(fileURLWithPath: fileManager.currentDirectoryPath)
    ) -> URL? {
        var url = startingAt
        for _ in 0..<10 {
            let marker = url.appendingPathComponent("playlist_builder")
            if fileManager.fileExists(atPath: marker.path) {
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
        if let configured = environment["RESONANCE_REPO_ROOT"], !configured.isEmpty {
            return PythonEngineBridgeConfiguration(workingDirectory: URL(fileURLWithPath: configured))
        }
        guard let root = ResonancePaths.repoRoot(fileManager: fileManager) else {
            return nil
        }
        return PythonEngineBridgeConfiguration(workingDirectory: root)
    }
}

public final class PythonEngineBridgeService: PlaylistGenerationServing, PlaylistImportServing, @unchecked Sendable {
    private let transport: BridgeTransport?
    private let fallbackGeneration: MockPlaylistGenerationService
    private let fallbackImport: MockPlaylistImportService

    public init(
        configuration: PythonEngineBridgeConfiguration? = PythonEngineBridgeConfiguration.automatic(),
        transport: BridgeTransport? = nil
    ) {
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
                params: ["request": BridgeContracts.generationRequestDictionary(request)]
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
            let (response, events) = try await transport.send(
                command: .importPlaylist,
                params: [
                    "playlist": BridgePayloadBuilder.playlistDictionary(from: result),
                    "sync": true,
                    "write_json_diagnostics": true,
                ]
            )
            for event in events {
                onEvent(event)
            }
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
            params: ["import_session_id": importSessionID]
        )
        guard let importObject = response.result["import"] as? [String: Any] else {
            throw PlaylistImportError.invalidResponse
        }
        return try BridgePayloadBuilder.importResult(from: ["import": importObject])
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
