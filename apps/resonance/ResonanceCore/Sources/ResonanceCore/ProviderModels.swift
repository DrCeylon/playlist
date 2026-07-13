import Foundation

public enum ProviderCapability: String, Codable, CaseIterable, Sendable {
    case catalogSearch = "catalog_search"
    case libraryResolve = "library_resolve"
    case playlistDelivery = "playlist_delivery"
    case playlistLibraryBrowse = "playlist_library_browse"
    case playlistSync = "playlist_sync"
    case publicPlaylistImport = "public_playlist_import"
    case authentication = "authentication"
    case experimental = "experimental"
}

public struct ProviderOption: Identifiable, Hashable, Sendable {
    public let providerID: ProviderID
    public let displayName: String
    public let isAvailable: Bool
    public let isConnected: Bool
    public let unavailableReason: String
    public let capabilities: [ProviderCapability]
    public let isExperimental: Bool

    public var id: String { providerID.rawValue }

    public init(
        providerID: ProviderID,
        displayName: String,
        isAvailable: Bool,
        isConnected: Bool = false,
        unavailableReason: String = "",
        capabilities: [ProviderCapability] = [],
        isExperimental: Bool = false
    ) {
        self.providerID = providerID
        self.displayName = displayName
        self.isAvailable = isAvailable
        self.isConnected = isConnected
        self.unavailableReason = unavailableReason
        self.capabilities = capabilities
        self.isExperimental = isExperimental
    }
}

public enum DefaultProviders {
    public static let options: [ProviderOption] = [
        ProviderOption(
            providerID: .appleMusic,
            displayName: "Apple Music",
            isAvailable: true,
            isConnected: true,
            capabilities: [.catalogSearch, .libraryResolve, .playlistDelivery, .playlistLibraryBrowse, .playlistSync]
        ),
        ProviderOption(
            providerID: .spotify,
            displayName: "Spotify",
            isAvailable: false,
            unavailableReason: "Prévu — gateway non enregistré."
        ),
        ProviderOption(
            providerID: .youtubeMusic,
            displayName: "YouTube Music",
            isAvailable: true,
            unavailableReason: "Connexion requise via fichier d'en-têtes ytmusicapi.",
            capabilities: [
                .catalogSearch,
                .libraryResolve,
                .playlistDelivery,
                .playlistLibraryBrowse,
                .playlistSync,
                .publicPlaylistImport,
                .authentication,
                .experimental,
            ],
            isExperimental: true
        ),
        ProviderOption(
            providerID: .deezer,
            displayName: "Deezer",
            isAvailable: false,
            unavailableReason: "Prévu — gateway non enregistré."
        ),
    ]
}
