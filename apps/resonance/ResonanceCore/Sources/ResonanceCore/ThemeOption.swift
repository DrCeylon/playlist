import Foundation

/// UI theme selector option mirrored from Python `ThemeOption`.
public struct ThemeOption: Identifiable, Hashable, Sendable {
    public let themeID: String
    public let displayName: String
    public let previewBackground: String
    public let previewAccent: String

    public var id: String { themeID }

    public init(
        themeID: String,
        displayName: String,
        previewBackground: String = "",
        previewAccent: String = ""
    ) {
        self.themeID = themeID
        self.displayName = displayName
        self.previewBackground = previewBackground
        self.previewAccent = previewAccent
    }
}
