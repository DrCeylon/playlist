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
    public static let maxVisibleDiagnostics = 8

    public var phase: ImportPhase
    public var playlistName: String
    public var totalTracks: Int
    public var processedTracks: Int
    public var currentTrackLabel: String
    public var currentStep: String
    public var addedCount: Int
    public var skippedCount: Int
    public var notFoundCount: Int
    public var errorCount: Int
    public var diagnostics: [String]
    public var cancellationNote: String
    public var lastActivityAt: Date

    public init(
        phase: ImportPhase = .idle,
        playlistName: String = "",
        totalTracks: Int = 0,
        processedTracks: Int = 0,
        currentTrackLabel: String = "",
        currentStep: String = "",
        addedCount: Int = 0,
        skippedCount: Int = 0,
        notFoundCount: Int = 0,
        errorCount: Int = 0,
        diagnostics: [String] = [],
        cancellationNote: String = "Annulation prévue — l'import en cours ne peut pas être interrompu proprement.",
        lastActivityAt: Date = .now
    ) {
        self.phase = phase
        self.playlistName = playlistName
        self.totalTracks = totalTracks
        self.processedTracks = processedTracks
        self.currentTrackLabel = currentTrackLabel
        self.currentStep = currentStep
        self.addedCount = addedCount
        self.skippedCount = skippedCount
        self.notFoundCount = notFoundCount
        self.errorCount = errorCount
        self.diagnostics = diagnostics
        self.cancellationNote = cancellationNote
        self.lastActivityAt = lastActivityAt
    }

    public var resolvedCount: Int {
        processedTracks
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
    public var historySessionID: String

    public init(
        playlistName: String,
        outcomes: [ImportTrackOutcome] = [],
        phase: ImportPhase = .completed,
        historySessionID: String = ""
    ) {
        self.playlistName = playlistName
        self.outcomes = outcomes
        self.phase = phase
        self.historySessionID = historySessionID
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

public extension PlaylistImportServing {
    func continueManualAcquisition(
        importSessionID: String,
        onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
    ) async throws -> ImportResultState {
        _ = onEvent
        return try await continueManualAcquisition(importSessionID: importSessionID)
    }
}
