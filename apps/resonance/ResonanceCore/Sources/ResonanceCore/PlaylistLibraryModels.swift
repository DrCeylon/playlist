import Foundation

public enum PlaylistSourceKind: String, Codable, CaseIterable, Sendable {
    case localSnapshot = "local_snapshot"
    case providerLibrary = "provider_library"
    case generatedImport = "generated_import"
    case publicCatalog = "public_catalog"
}

public enum PlaylistOrigin: String, Codable, CaseIterable, Sendable {
    case providerLibrary = "provider_library"
    case generated = "generated"
    case importedFile = "imported_file"
    case manual = "manual"
    case shared = "shared"
}

public enum PlaylistSyncStatus: String, Codable, CaseIterable, Sendable {
    case unknown = "unknown"
    case synced = "synced"
    case pending = "pending"
    case partial = "partial"
    case conflict = "conflict"
    case error = "error"
    case notLinked = "not_linked"
}

public enum PlaylistTrackMappingStatus: String, Codable, CaseIterable, Sendable {
    case matched = "matched"
    case missingLocally = "missing_locally"
    case missingOnProvider = "missing_on_provider"
    case duplicate = "duplicate"
    case metadataMismatch = "metadata_mismatch"
    case unresolved = "unresolved"
}

public enum PlaylistSyncDirection: String, Codable, CaseIterable, Sendable {
    case pullFromProvider = "pull_from_provider"
    case pushToProvider = "push_to_provider"
    case bidirectionalPreview = "bidirectional_preview"
}

public struct LinkedRemoteRef: Hashable, Sendable {
    public let providerID: ProviderID
    public let remotePlaylistID: String
    public let snapshotChecksum: String
    public let lastSeenSnapshotChecksum: String
    public let lastAppliedSnapshotChecksum: String
    public let syncState: String
    public let lastSyncAt: String

    public init(
        providerID: ProviderID,
        remotePlaylistID: String,
        snapshotChecksum: String = "",
        lastSeenSnapshotChecksum: String = "",
        lastAppliedSnapshotChecksum: String = "",
        syncState: String = "",
        lastSyncAt: String = ""
    ) {
        self.providerID = providerID
        self.remotePlaylistID = remotePlaylistID
        self.snapshotChecksum = snapshotChecksum
        self.lastSeenSnapshotChecksum = lastSeenSnapshotChecksum
        self.lastAppliedSnapshotChecksum = lastAppliedSnapshotChecksum
        self.syncState = syncState
        self.lastSyncAt = lastSyncAt
    }
}

public struct ManagedPlaylistSummary: Identifiable, Hashable, Sendable {
    public let localPlaylistID: String
    public let name: String
    public let providerID: ProviderID
    public let trackCount: Int
    public let syncStatus: PlaylistSyncStatus
    public let lastSyncedAtISO: String
    public let providerPlaylistID: String
    public let sourceKind: PlaylistSourceKind
    public let importStatus: SessionHistoryStatus?
    public let historySessionID: String
    public let origin: PlaylistOrigin
    public let playlistVersion: Int
    public let linkedRemoteRefs: [LinkedRemoteRef]
    public let createdAtISO: String
    public let updatedAtISO: String

    public var id: String { localPlaylistID }

    public init(
        localPlaylistID: String,
        name: String,
        providerID: ProviderID,
        trackCount: Int,
        syncStatus: PlaylistSyncStatus,
        lastSyncedAtISO: String = "",
        providerPlaylistID: String = "",
        sourceKind: PlaylistSourceKind = .localSnapshot,
        importStatus: SessionHistoryStatus? = nil,
        historySessionID: String = "",
        origin: PlaylistOrigin = .generated,
        playlistVersion: Int = 1,
        linkedRemoteRefs: [LinkedRemoteRef] = [],
        createdAtISO: String = "",
        updatedAtISO: String = ""
    ) {
        self.localPlaylistID = localPlaylistID
        self.name = name
        self.providerID = providerID
        self.trackCount = trackCount
        self.syncStatus = syncStatus
        self.lastSyncedAtISO = lastSyncedAtISO
        self.providerPlaylistID = providerPlaylistID
        self.sourceKind = sourceKind
        self.importStatus = importStatus
        self.historySessionID = historySessionID
        self.origin = origin
        self.playlistVersion = playlistVersion
        self.linkedRemoteRefs = linkedRemoteRefs
        self.createdAtISO = createdAtISO
        self.updatedAtISO = updatedAtISO
    }
}

public struct ManagedPlaylistTrack: Identifiable, Hashable, Sendable {
    public let localTrackID: String
    public let providerTrackID: String
    public let artist: String
    public let title: String
    public let section: String
    public let mappingStatus: PlaylistTrackMappingStatus

    public var id: String { localTrackID }

    public init(
        localTrackID: String,
        providerTrackID: String = "",
        artist: String,
        title: String,
        section: String = "",
        mappingStatus: PlaylistTrackMappingStatus = .matched
    ) {
        self.localTrackID = localTrackID
        self.providerTrackID = providerTrackID
        self.artist = artist
        self.title = title
        self.section = section
        self.mappingStatus = mappingStatus
    }
}

public struct PlaylistSyncConflict: Identifiable, Hashable, Sendable {
    public let id: String
    public let trackKey: String
    public let conflictKind: String
    public let message: String
    public let scope: String
    public let severity: String
    public let availableResolutions: [String]
    public let recommendedResolution: String

    public init(
        id: String,
        trackKey: String,
        conflictKind: String,
        message: String,
        scope: String = "track",
        severity: String = "blocking",
        availableResolutions: [String] = [],
        recommendedResolution: String = ""
    ) {
        self.id = id
        self.trackKey = trackKey
        self.conflictKind = conflictKind
        self.message = message
        self.scope = scope
        self.severity = severity
        self.availableResolutions = availableResolutions
        self.recommendedResolution = recommendedResolution
    }
}

public struct ManagedPlaylistDetail: Sendable {
    public let summary: ManagedPlaylistSummary
    public let tracks: [ManagedPlaylistTrack]
    public let syncConflicts: [PlaylistSyncConflict]

    public init(
        summary: ManagedPlaylistSummary,
        tracks: [ManagedPlaylistTrack],
        syncConflicts: [PlaylistSyncConflict] = []
    ) {
        self.summary = summary
        self.tracks = tracks
        self.syncConflicts = syncConflicts
    }
}

public struct PlaylistSyncRequest: Sendable {
    public let localPlaylistID: String
    public let direction: PlaylistSyncDirection
    public let providerID: ProviderID

    public init(
        localPlaylistID: String,
        direction: PlaylistSyncDirection,
        providerID: ProviderID
    ) {
        self.localPlaylistID = localPlaylistID
        self.direction = direction
        self.providerID = providerID
    }
}

public struct PlaylistSyncResult: Sendable {
    public let localPlaylistID: String
    public let syncStatus: PlaylistSyncStatus
    public let message: String
    public let conflicts: [PlaylistSyncConflict]

    public init(
        localPlaylistID: String,
        syncStatus: PlaylistSyncStatus,
        message: String,
        conflicts: [PlaylistSyncConflict] = []
    ) {
        self.localPlaylistID = localPlaylistID
        self.syncStatus = syncStatus
        self.message = message
        self.conflicts = conflicts
    }
}

public enum SyncOperationStatus: String, Codable, CaseIterable, Sendable {
    case pending = "pending"
    case running = "running"
    case completed = "completed"
    case partial = "partial"
    case failed = "failed"
    case cancelled = "cancelled"
    case blockedConfirmation = "blocked_confirmation"
    case blockedConflict = "blocked_conflict"
    case noOp = "no_op"
}

public struct PlaylistSyncOperation: Sendable {
    public let operationID: String
    public let status: SyncOperationStatus
    public let localPlaylistVersionBefore: Int
    public let localPlaylistVersionAfter: Int

    public init(
        operationID: String,
        status: SyncOperationStatus,
        localPlaylistVersionBefore: Int,
        localPlaylistVersionAfter: Int
    ) {
        self.operationID = operationID
        self.status = status
        self.localPlaylistVersionBefore = localPlaylistVersionBefore
        self.localPlaylistVersionAfter = localPlaylistVersionAfter
    }
}

public struct SyncActionOutcome: Sendable {
    public let actionID: String
    public let kind: String
    public let trackKey: String
    public let status: String
    public let message: String

    public init(actionID: String, kind: String, trackKey: String, status: String, message: String) {
        self.actionID = actionID
        self.kind = kind
        self.trackKey = trackKey
        self.status = status
        self.message = message
    }
}

public struct PlaylistSyncApplyResult: Sendable {
    public let operation: PlaylistSyncOperation
    public let finalSyncStatus: String
    public let message: String
    public let requiresConfirmation: Bool
    public let actionsApplied: [SyncActionOutcome]

    public init(
        operation: PlaylistSyncOperation,
        finalSyncStatus: String,
        message: String,
        requiresConfirmation: Bool,
        actionsApplied: [SyncActionOutcome]
    ) {
        self.operation = operation
        self.finalSyncStatus = finalSyncStatus
        self.message = message
        self.requiresConfirmation = requiresConfirmation
        self.actionsApplied = actionsApplied
    }
}

public enum PlaylistLibraryDisplay {
    public static func syncStatusLabel(_ status: PlaylistSyncStatus) -> String {
        switch status {
        case .unknown: return "Inconnu"
        case .synced: return "Synchronisée"
        case .pending: return "Synchronisation en attente"
        case .partial: return "Synchronisation partielle"
        case .conflict: return "Conflits détectés"
        case .error: return "Erreur de synchronisation"
        case .notLinked: return "Non liée au provider"
        }
    }

    public static func providerLabel(_ providerID: ProviderID) -> String {
        switch providerID {
        case .appleMusic, .appleMusicKit: return "Apple Music"
        case .spotify: return "Spotify"
        case .youtubeMusic: return "YouTube Music"
        case .deezer: return "Deezer"
        case .discogs: return "Discogs"
        case .musicbrainz: return "MusicBrainz"
        }
    }
}
