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

public enum ImportTrackStep: String, Codable, Sendable, CaseIterable {
    case pending
    case searching
    case resolving
    case acquiring
    case adding
    case completed
}

public struct ImportTrackActivity: Identifiable, Equatable, Sendable {
    public let trackKey: String
    public var trackIndex: Int
    public var artist: String
    public var title: String
    public var album: String
    public var section: String
    public var step: ImportTrackStep
    public var status: ImportTrackStatus
    public var message: String
    public var catalogURL: String
    public var isCurrent: Bool

    public var id: String { trackKey }

    public init(
        trackKey: String,
        trackIndex: Int,
        artist: String,
        title: String,
        album: String = "",
        section: String = "",
        step: ImportTrackStep = .pending,
        status: ImportTrackStatus = .pending,
        message: String = "",
        catalogURL: String = "",
        isCurrent: Bool = false
    ) {
        self.trackKey = trackKey
        self.trackIndex = trackIndex
        self.artist = artist
        self.title = title
        self.album = album
        self.section = section
        self.step = step
        self.status = status
        self.message = message
        self.catalogURL = catalogURL
        self.isCurrent = isCurrent
    }

    public var displayLabel: String {
        let artist = artist.trimmingCharacters(in: .whitespacesAndNewlines)
        let title = title.trimmingCharacters(in: .whitespacesAndNewlines)
        if artist.isEmpty { return title }
        if title.isEmpty { return artist }
        return "\(artist) — \(title)"
    }
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
    public var album: String
    public var catalogURL: String

    public init(
        id: UUID = UUID(),
        artist: String,
        title: String,
        section: String,
        status: ImportTrackStatus,
        message: String = "",
        album: String = "",
        catalogURL: String = ""
    ) {
        self.id = id
        self.artist = artist
        self.title = title
        self.section = section
        self.status = status
        self.message = message
        self.album = album
        self.catalogURL = catalogURL
    }

    public var displayLabel: String {
        let artist = artist.trimmingCharacters(in: .whitespacesAndNewlines)
        let title = title.trimmingCharacters(in: .whitespacesAndNewlines)
        if artist.isEmpty { return title }
        if title.isEmpty { return artist }
        return "\(title) — \(artist)"
    }

    public var searchLine: String {
        let artist = artist.trimmingCharacters(in: .whitespacesAndNewlines)
        let title = title.trimmingCharacters(in: .whitespacesAndNewlines)
        if artist.isEmpty { return title }
        if title.isEmpty { return artist }
        return "\(artist) \(title)"
    }
}

public struct ImportProgressSnapshot: Equatable, Sendable {
    public static let maxVisibleDiagnostics = 8
    public static let maxVisibleActivities = 12

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
    public var activities: [ImportTrackActivity]
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
        activities: [ImportTrackActivity] = [],
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
        self.activities = activities
        self.cancellationNote = cancellationNote
        self.lastActivityAt = lastActivityAt
    }

    public var resolvedCount: Int {
        processedTracks
    }

    public var progressRatio: Double {
        guard totalTracks > 0 else { return 0 }
        switch phase {
        case .delivering:
            let resolvedWeight = 0.7
            let deliveryProgress = min(1.0, Double(addedCount + skippedCount + notFoundCount + errorCount) / Double(totalTracks))
            return min(1.0, resolvedWeight + (1.0 - resolvedWeight) * deliveryProgress)
        case .completed:
            return 1.0
        default:
            return min(0.7, Double(processedTracks) / Double(totalTracks) * 0.7)
        }
    }

    public var remainingTracksLabel: String {
        guard totalTracks > 0 else { return "" }
        let remaining = max(0, totalTracks - processedTracks)
        if phase == .delivering {
            return "Finalisation dans Music.app…"
        }
        if remaining == 0 {
            return "Résolution terminée"
        }
        return "\(remaining) morceau(x) restant(s)"
    }

    public var phaseLabel: String {
        switch phase {
        case .resolving: return "Étape 1/2 — Recherche et résolution"
        case .delivering: return "Étape 2/2 — Ajout dans Music.app"
        case .waitingForManualAcquisition: return "En attente d'ajout manuel"
        case .completed: return "Import terminé"
        case .partialSuccess: return "Import partiel"
        case .failed: return "Import échoué"
        default: return "Préparation"
        }
    }
}

public struct ManualAcquisitionPrompt: Equatable, Sendable {
    public var token: String
    public var artist: String
    public var title: String
    public var instructions: String
    public var catalogLabel: String
    public var album: String
    public var catalogURL: String

    public init(
        token: String,
        artist: String,
        title: String,
        instructions: String,
        catalogLabel: String = "",
        album: String = "",
        catalogURL: String = ""
    ) {
        self.token = token
        self.artist = artist
        self.title = title
        self.instructions = instructions
        self.catalogLabel = catalogLabel
        self.album = album
        self.catalogURL = catalogURL
    }

    public var searchLine: String {
        let artist = artist.trimmingCharacters(in: .whitespacesAndNewlines)
        let title = title.trimmingCharacters(in: .whitespacesAndNewlines)
        if artist.isEmpty { return title }
        if title.isEmpty { return artist }
        return "\(artist) — \(title)"
    }
}

public struct ImportResultState: Hashable, Codable, Sendable {
    public var playlistName: String
    public var outcomes: [ImportTrackOutcome]
    public var phase: ImportPhase
    public var historySessionID: String
    public var importSessionID: String
    public var manualToken: String
    public var manualArtist: String
    public var manualTitle: String
    public var manualInstructions: String
    public var manualCatalogLabel: String
    public var manualCatalogURL: String
    public var manualAlbum: String

    public init(
        playlistName: String,
        outcomes: [ImportTrackOutcome] = [],
        phase: ImportPhase = .completed,
        historySessionID: String = "",
        importSessionID: String = "",
        manualToken: String = "",
        manualArtist: String = "",
        manualTitle: String = "",
        manualInstructions: String = "",
        manualCatalogLabel: String = "",
        manualCatalogURL: String = "",
        manualAlbum: String = ""
    ) {
        self.playlistName = playlistName
        self.outcomes = outcomes
        self.phase = phase
        self.historySessionID = historySessionID
        self.importSessionID = importSessionID
        self.manualToken = manualToken
        self.manualArtist = manualArtist
        self.manualTitle = manualTitle
        self.manualInstructions = manualInstructions
        self.manualCatalogLabel = manualCatalogLabel
        self.manualCatalogURL = manualCatalogURL
        self.manualAlbum = manualAlbum
    }

    public var manualPrompt: ManualAcquisitionPrompt? {
        guard phase == .waitingForManualAcquisition else { return nil }
        guard !manualArtist.isEmpty || !manualTitle.isEmpty else { return nil }
        return ManualAcquisitionPrompt(
            token: manualToken,
            artist: manualArtist,
            title: manualTitle,
            instructions: manualInstructions,
            catalogLabel: manualCatalogLabel,
            album: manualAlbum,
            catalogURL: manualCatalogURL
        )
    }

    public var canResumeManualAcquisition: Bool {
        phase == .waitingForManualAcquisition && !importSessionID.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
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

public struct ManualAcquisitionUIStatus: Equatable, Sendable {
    public var phase: ManualAcquisitionWorkflowPhase
    public var lastUserClickAt: Date?
    public var phaseEnteredAt: Date?
    public var currentStep: String
    public var lastVerificationResult: String
    public var userAdvice: String
    public var lastProbeStartedAt: Date?
    public var lastProbeFinishedAt: Date?
    public var lastProbeDurationMs: Int?
    public var backendErrorCode: String?
    public var backendMessage: String?

    public init(
        phase: ManualAcquisitionWorkflowPhase = .waitingForUser,
        lastUserClickAt: Date? = nil,
        phaseEnteredAt: Date? = nil,
        currentStep: String = "",
        lastVerificationResult: String = "",
        userAdvice: String = "",
        lastProbeStartedAt: Date? = nil,
        lastProbeFinishedAt: Date? = nil,
        lastProbeDurationMs: Int? = nil,
        backendErrorCode: String? = nil,
        backendMessage: String? = nil
    ) {
        self.phase = phase
        self.lastUserClickAt = lastUserClickAt
        self.phaseEnteredAt = phaseEnteredAt
        self.currentStep = currentStep
        self.lastVerificationResult = lastVerificationResult
        self.userAdvice = userAdvice
        self.lastProbeStartedAt = lastProbeStartedAt
        self.lastProbeFinishedAt = lastProbeFinishedAt
        self.lastProbeDurationMs = lastProbeDurationMs
        self.backendErrorCode = backendErrorCode
        self.backendMessage = backendMessage
    }

    public var elapsedSincePhaseEnteredLabel: String? {
        guard let phaseEnteredAt else { return nil }
        let seconds = max(0, Int(Date().timeIntervalSince(phaseEnteredAt)))
        if seconds <= 1 { return "Démarré à l'instant" }
        return "En cours depuis \(seconds) s"
    }

    public var nextStepHint: String {
        if !userAdvice.isEmpty { return userAdvice }
        return phase.nextStepHint
    }

    public var lastUserClickLabel: String? {
        guard let lastUserClickAt else { return nil }
        return Self.formattedClickTime(lastUserClickAt)
    }

    public static func formattedClickTime(_ date: Date) -> String {
        timestampFormatter.string(from: date)
    }

    private static let timestampFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "fr_FR")
        formatter.dateFormat = "HH:mm:ss"
        return formatter
    }()
}

public struct ManualAcquisitionProbeDiagnostics: Equatable, Sendable {
    public var importSessionID: String
    public var checkpointPath: String
    public var checkpointExists: Bool
    public var searchTerms: [String]
    public var providerID: String
    public var probeError: String?
    public var probeStartedAt: Date?
    public var probeFinishedAt: Date?
    public var probeDurationMs: Int?

    public init(
        importSessionID: String = "",
        checkpointPath: String = "",
        checkpointExists: Bool = false,
        searchTerms: [String] = [],
        providerID: String = "",
        probeError: String? = nil,
        probeStartedAt: Date? = nil,
        probeFinishedAt: Date? = nil,
        probeDurationMs: Int? = nil
    ) {
        self.importSessionID = importSessionID
        self.checkpointPath = checkpointPath
        self.checkpointExists = checkpointExists
        self.searchTerms = searchTerms
        self.providerID = providerID
        self.probeError = probeError
        self.probeStartedAt = probeStartedAt
        self.probeFinishedAt = probeFinishedAt
        self.probeDurationMs = probeDurationMs
    }

    public var architectSummary: String {
        var lines = [
            "import_session_id: \(importSessionID)",
            "checkpoint_path: \(checkpointPath)",
            "checkpoint_exists: \(checkpointExists)",
            "search_terms: \(searchTerms.joined(separator: ", "))",
            "provider_id: \(providerID)",
        ]
        if let probeStartedAt {
            lines.append("last_probe_started_at: \(ISO8601DateFormatter().string(from: probeStartedAt))")
        }
        if let probeFinishedAt {
            lines.append("last_probe_finished_at: \(ISO8601DateFormatter().string(from: probeFinishedAt))")
        }
        if let probeDurationMs {
            lines.append("last_probe_duration_ms: \(probeDurationMs)")
        }
        if let probeError, !probeError.isEmpty {
            lines.append("probe_error: \(probeError)")
        }
        return lines.joined(separator: "\n")
    }
}

public struct ManualAcquisitionProbeResult: Equatable, Sendable {
    public var found: Bool
    public var message: String
    public var errorCode: String?
    public var workflowPhase: String?
    public var diagnostics: ManualAcquisitionProbeDiagnostics?

    public init(
        found: Bool,
        message: String = "",
        errorCode: String? = nil,
        workflowPhase: String? = nil,
        diagnostics: ManualAcquisitionProbeDiagnostics? = nil
    ) {
        self.found = found
        self.message = message
        self.errorCode = errorCode
        self.workflowPhase = workflowPhase
        self.diagnostics = diagnostics
    }

    public var architectSummary: String? {
        var lines: [String] = []
        if let errorCode, !errorCode.isEmpty {
            lines.append("error_code: \(errorCode)")
        }
        if let diagnostics {
            lines.append(diagnostics.architectSummary)
        }
        return lines.isEmpty ? nil : lines.joined(separator: "\n")
    }
}

public protocol PlaylistImportServing: Sendable {
    func importPlaylist(
        _ result: PlaylistGenerationResult,
        onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
    ) async throws -> ImportResultState

    func continueManualAcquisition(importSessionID: String) async throws -> ImportResultState

    func probeManualAcquisition(importSessionID: String) async throws -> ManualAcquisitionProbeResult

    func retryImportTracks(
        _ generationResult: PlaylistGenerationResult,
        trackIndices: [Int],
        onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
    ) async throws -> ImportResultState
}

public extension PlaylistImportServing {
    func retryImportTracks(
        _ generationResult: PlaylistGenerationResult,
        trackIndices: [Int],
        onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
    ) async throws -> ImportResultState {
        _ = generationResult
        _ = trackIndices
        _ = onEvent
        throw PlaylistImportError.bridgeUnavailable
    }
    func probeManualAcquisition(importSessionID: String) async throws -> ManualAcquisitionProbeResult {
        _ = importSessionID
        return ManualAcquisitionProbeResult(found: false, message: "Probe indisponible.")
    }

    func continueManualAcquisition(
        importSessionID: String,
        onEvent: @escaping @Sendable (BridgeEventMessage) -> Void
    ) async throws -> ImportResultState {
        _ = onEvent
        return try await continueManualAcquisition(importSessionID: importSessionID)
    }
}
