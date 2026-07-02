import Foundation
import ResonanceCore

public enum ResonancePaths {
    public static func repoRoot(
        fileManager: FileManager = .default,
        startingAt: URL? = nil
    ) -> URL? {
        var url = startingAt ?? URL(fileURLWithPath: fileManager.currentDirectoryPath)
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

/// Immutable service wrapper around bridge transport and stateless fallback services.
public final class PythonEngineBridgeService: PlaylistGenerationServing, PlaylistImportServing, DiagnosticsServing, @unchecked Sendable {
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
            let (response, events) = try await transport.send(
                command: .importPlaylist,
                params: [
                    "playlist": .object(BridgePayloadBuilder.playlistDictionary(from: result)),
                    "sync": .bool(true),
                    "write_json_diagnostics": .bool(true),
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
