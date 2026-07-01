import Foundation

public enum ImportPhase: String, Codable, Sendable, CaseIterable {
    case idle
    case resolving
    case acquiring
    case waitingForManualAcquisition = "waiting_for_manual_acquisition"
    case delivering
    case completed
    case partialSuccess = "partial_success"
    case failed
}

public enum ImportTrackStatus: String, Codable, Sendable, CaseIterable {
    case pending
    case added
    case skipped
    case notFound = "not_found"
    case error
    case acquiring
}

public struct ImportTrackOutcome: Identifiable, Hashable, Codable, Sendable {
    public let id: UUID
    public var artist: String
    public var title: String
    public var section: String
    public var status: ImportTrackStatus
    public var message: String

    public init(
        id: UUID = UUID(),
        artist: String,
        title: String,
        section: String,
        status: ImportTrackStatus,
        message: String = ""
    ) {
        self.id = id
        self.artist = artist
        self.title = title
        self.section = section
        self.status = status
        self.message = message
    }
}

public struct ImportProgressSnapshot: Equatable, Sendable {
    public var phase: ImportPhase
    public var playlistName: String
    public var totalTracks: Int
    public var processedTracks: Int
    public var currentTrackLabel: String
    public var diagnostics: [String]

    public init(
        phase: ImportPhase = .idle,
        playlistName: String = "",
        totalTracks: Int = 0,
        processedTracks: Int = 0,
        currentTrackLabel: String = "",
        diagnostics: [String] = []
    ) {
        self.phase = phase
        self.playlistName = playlistName
        self.totalTracks = totalTracks
        self.processedTracks = processedTracks
        self.currentTrackLabel = currentTrackLabel
        self.diagnostics = diagnostics
    }

    public var progressRatio: Double {
        guard totalTracks > 0 else { return 0 }
        return min(1.0, Double(processedTracks) / Double(totalTracks))
    }
}

public struct ManualAcquisitionPrompt: Equatable, Sendable {
    public var token: String
    public var artist: String
    public var title: String
    public var instructions: String
    public var catalogLabel: String

    public init(
        token: String,
        artist: String,
        title: String,
        instructions: String,
        catalogLabel: String = ""
    ) {
        self.token = token
        self.artist = artist
        self.title = title
        self.instructions = instructions
        self.catalogLabel = catalogLabel
    }
}

public struct ImportResultState: Hashable, Codable, Sendable {
    public var playlistName: String
    public var outcomes: [ImportTrackOutcome]
    public var phase: ImportPhase

    public init(
        playlistName: String,
        outcomes: [ImportTrackOutcome] = [],
        phase: ImportPhase = .completed
    ) {
        self.playlistName = playlistName
        self.outcomes = outcomes
        self.phase = phase
    }

    public var addedCount: Int {
        outcomes.filter { $0.status == .added }.count
    }

    public var skippedCount: Int {
        outcomes.filter { $0.status == .skipped }.count
    }

    public var notFoundCount: Int {
        outcomes.filter { $0.status == .notFound }.count
    }

    public var errorCount: Int {
        outcomes.filter { $0.status == .error }.count
    }

    public var cacheHitCount: Int {
        outcomes.filter { $0.message.localizedCaseInsensitiveContains("cache") }.count
    }
}

public protocol PlaylistImportServing: Sendable {
    func importPlaylist(
        _ result: PlaylistGenerationResult,
        onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
    ) async throws -> ImportResultState

    func continueManualAcquisition(importSessionID: String) async throws -> ImportResultState
}
