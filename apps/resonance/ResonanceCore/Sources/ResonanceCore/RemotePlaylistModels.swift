import Foundation

public enum ProviderAuthState: String, Codable, CaseIterable, Sendable {
    case disconnected = "disconnected"
    case configured = "configured"
    case connected = "connected"
    case expired = "expired"
    case error = "error"
    case experimentalUnavailable = "experimental_unavailable"
}

public struct RemotePlaylistTrack: Identifiable, Hashable, Sendable {
    public let remoteTrackID: String
    public let artist: String
    public let title: String
    public let album: String
    public let durationMS: Int
    public let position: Int
    public let providerMetadata: [String: String]

    public var id: String { remoteTrackID }

    public init(
        remoteTrackID: String,
        artist: String,
        title: String,
        album: String = "",
        durationMS: Int = 0,
        position: Int = 0,
        providerMetadata: [String: String] = [:]
    ) {
        self.remoteTrackID = remoteTrackID
        self.artist = artist
        self.title = title
        self.album = album
        self.durationMS = durationMS
        self.position = position
        self.providerMetadata = providerMetadata
    }
}

public struct RemotePlaylist: Identifiable, Hashable, Sendable {
    public let providerID: ProviderID
    public let remotePlaylistID: String
    public let name: String
    public let trackCount: Int
    public let isPublic: Bool
    public let ownerLabel: String
    public let snapshotAtISO: String
    public let sourceURL: String

    public var id: String { "\(providerID.rawValue):\(remotePlaylistID)" }

    public init(
        providerID: ProviderID,
        remotePlaylistID: String,
        name: String,
        trackCount: Int,
        isPublic: Bool = false,
        ownerLabel: String = "",
        snapshotAtISO: String = "",
        sourceURL: String = ""
    ) {
        self.providerID = providerID
        self.remotePlaylistID = remotePlaylistID
        self.name = name
        self.trackCount = trackCount
        self.isPublic = isPublic
        self.ownerLabel = ownerLabel
        self.snapshotAtISO = snapshotAtISO
        self.sourceURL = sourceURL
    }
}

public struct RemotePlaylistSnapshot: Sendable {
    public let providerID: ProviderID
    public let remotePlaylistID: String
    public let name: String
    public let snapshotAtISO: String
    public let tracks: [RemotePlaylistTrack]
    public let trackCount: Int
    public let checksum: String
    public let sourceKind: PlaylistSourceKind
    public let sourceURL: String

    public init(
        providerID: ProviderID,
        remotePlaylistID: String,
        name: String,
        snapshotAtISO: String,
        tracks: [RemotePlaylistTrack],
        trackCount: Int,
        checksum: String,
        sourceKind: PlaylistSourceKind,
        sourceURL: String = ""
    ) {
        self.providerID = providerID
        self.remotePlaylistID = remotePlaylistID
        self.name = name
        self.snapshotAtISO = snapshotAtISO
        self.tracks = tracks
        self.trackCount = trackCount
        self.checksum = checksum
        self.sourceKind = sourceKind
        self.sourceURL = sourceURL
    }
}

public struct RemoteProviderAccount: Identifiable, Hashable, Sendable {
    public let providerID: ProviderID
    public let displayName: String
    public let authState: ProviderAuthState
    public let lastConnectedAtISO: String
    public let capabilities: [ProviderCapability]

    public var id: String { providerID.rawValue }

    public init(
        providerID: ProviderID,
        displayName: String,
        authState: ProviderAuthState,
        lastConnectedAtISO: String = "",
        capabilities: [ProviderCapability] = []
    ) {
        self.providerID = providerID
        self.displayName = displayName
        self.authState = authState
        self.lastConnectedAtISO = lastConnectedAtISO
        self.capabilities = capabilities
    }
}
