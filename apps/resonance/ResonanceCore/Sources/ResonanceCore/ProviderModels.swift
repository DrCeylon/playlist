import Foundation

public struct ProviderOption: Identifiable, Hashable, Sendable {
    public let providerID: ProviderID
    public let displayName: String
    public let isAvailable: Bool
    public let isConnected: Bool
    public let unavailableReason: String

    public var id: String { providerID.rawValue }

    public init(
        providerID: ProviderID,
        displayName: String,
        isAvailable: Bool,
        isConnected: Bool = false,
        unavailableReason: String = ""
    ) {
        self.providerID = providerID
        self.displayName = displayName
        self.isAvailable = isAvailable
        self.isConnected = isConnected
        self.unavailableReason = unavailableReason
    }
}

public enum DefaultProviders {
    public static let options: [ProviderOption] = [
        ProviderOption(
            providerID: .appleMusic,
            displayName: "Apple Music",
            isAvailable: true,
            isConnected: true
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
            isAvailable: false,
            unavailableReason: "Prévu — gateway non enregistré."
        ),
        ProviderOption(
            providerID: .deezer,
            displayName: "Deezer",
            isAvailable: false,
            unavailableReason: "Prévu — gateway non enregistré."
        ),
    ]
}
