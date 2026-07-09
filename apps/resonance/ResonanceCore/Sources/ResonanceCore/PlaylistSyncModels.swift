import Foundation

public enum SyncMode: String, Codable, CaseIterable, Sendable {
    case dryRun = "dry_run"
    case appendOnly = "append_only"
    case mirror = "mirror"
    case manualResolve = "manual_resolve"
}

public enum PlaylistSyncActionKind: String, Codable, CaseIterable, Sendable {
    case addTrack = "add_track"
    case removeTrack = "remove_track"
    case reorder = "reorder"
    case mapTrack = "map_track"
    case renamePlaylist = "rename_playlist"
}

public struct PlaylistSyncAction: Identifiable, Hashable, Sendable {
    public let kind: PlaylistSyncActionKind
    public let trackKey: String
    public let artist: String
    public let title: String
    public let message: String
    public let localTrackID: String
    public let remoteTrackID: String
    public let sourcePosition: Int?
    public let targetPosition: Int?

    public var id: String { "\(kind.rawValue):\(trackKey):\(message)" }

    public init(
        kind: PlaylistSyncActionKind,
        trackKey: String,
        artist: String,
        title: String,
        message: String = "",
        localTrackID: String = "",
        remoteTrackID: String = "",
        sourcePosition: Int? = nil,
        targetPosition: Int? = nil
    ) {
        self.kind = kind
        self.trackKey = trackKey
        self.artist = artist
        self.title = title
        self.message = message
        self.localTrackID = localTrackID
        self.remoteTrackID = remoteTrackID
        self.sourcePosition = sourcePosition
        self.targetPosition = targetPosition
    }
}

public struct PlaylistSyncSummary: Hashable, Sendable {
    public let additions: Int
    public let removals: Int
    public let alreadyPresent: Int
    public let metadataMismatches: Int
    public let reorders: Int
    public let conflicts: Int
    public let renameRequired: Bool

    public init(
        additions: Int = 0,
        removals: Int = 0,
        alreadyPresent: Int = 0,
        metadataMismatches: Int = 0,
        reorders: Int = 0,
        conflicts: Int = 0,
        renameRequired: Bool = false
    ) {
        self.additions = additions
        self.removals = removals
        self.alreadyPresent = alreadyPresent
        self.metadataMismatches = metadataMismatches
        self.reorders = reorders
        self.conflicts = conflicts
        self.renameRequired = renameRequired
    }
}

public struct PlaylistSyncPlan: Sendable {
    public let localPlaylistID: String
    public let targetProviderID: ProviderID
    public let direction: PlaylistSyncDirection
    public let syncMode: SyncMode
    public let remotePlaylistID: String
    public let playlistNameLocal: String
    public let playlistNameRemote: String
    public let actions: [PlaylistSyncAction]
    public let conflicts: [PlaylistSyncConflict]
    public let summary: PlaylistSyncSummary

    public init(
        localPlaylistID: String,
        targetProviderID: ProviderID,
        direction: PlaylistSyncDirection,
        syncMode: SyncMode,
        remotePlaylistID: String,
        playlistNameLocal: String = "",
        playlistNameRemote: String = "",
        actions: [PlaylistSyncAction] = [],
        conflicts: [PlaylistSyncConflict] = [],
        summary: PlaylistSyncSummary = PlaylistSyncSummary()
    ) {
        self.localPlaylistID = localPlaylistID
        self.targetProviderID = targetProviderID
        self.direction = direction
        self.syncMode = syncMode
        self.remotePlaylistID = remotePlaylistID
        self.playlistNameLocal = playlistNameLocal
        self.playlistNameRemote = playlistNameRemote
        self.actions = actions
        self.conflicts = conflicts
        self.summary = summary
    }
}

public struct PlaylistSyncPlanRequest: Sendable {
    public let localPlaylistID: String
    public let providerID: ProviderID
    public let direction: PlaylistSyncDirection
    public let syncMode: SyncMode
    public let remotePlaylistID: String

    public init(
        localPlaylistID: String,
        providerID: ProviderID,
        direction: PlaylistSyncDirection,
        syncMode: SyncMode = .dryRun,
        remotePlaylistID: String = ""
    ) {
        self.localPlaylistID = localPlaylistID
        self.providerID = providerID
        self.direction = direction
        self.syncMode = syncMode
        self.remotePlaylistID = remotePlaylistID
    }
}
