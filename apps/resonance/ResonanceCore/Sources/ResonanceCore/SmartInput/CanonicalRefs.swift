import Foundation

// MARK: - Canonical entity protocol

public protocol CanonicalEntity: Hashable, Codable, Sendable, Identifiable {
    var displayLabel: String { get }
}

// MARK: - ArtistRef

public struct ArtistRef: CanonicalEntity {
    public var id: String
    public var displayName: String
    public var sortName: String?
    public var artworkURL: URL?
    public var albumCount: Int?
    public var artistType: String?

    public var displayLabel: String { displayName }

    public init(
        id: String,
        displayName: String,
        sortName: String? = nil,
        artworkURL: URL? = nil,
        albumCount: Int? = nil,
        artistType: String? = nil
    ) {
        self.id = id
        self.displayName = displayName
        self.sortName = sortName
        self.artworkURL = artworkURL
        self.albumCount = albumCount
        self.artistType = artistType
    }
}

// MARK: - TrackRef

public struct TrackRef: CanonicalEntity {
    public var id: String
    public var title: String
    public var artistName: String
    public var albumTitle: String?
    public var releaseYear: Int?
    public var durationMs: Int?
    public var artworkURL: URL?

    public var displayLabel: String {
        if albumTitle?.isEmpty == false, let albumTitle {
            return "\(title) — \(albumTitle)"
        }
        return "\(title) — \(artistName)"
    }

    public init(
        id: String,
        title: String,
        artistName: String,
        albumTitle: String? = nil,
        releaseYear: Int? = nil,
        durationMs: Int? = nil,
        artworkURL: URL? = nil
    ) {
        self.id = id
        self.title = title
        self.artistName = artistName
        self.albumTitle = albumTitle
        self.releaseYear = releaseYear
        self.durationMs = durationMs
        self.artworkURL = artworkURL
    }

    public var formattedDuration: String? {
        guard let durationMs, durationMs > 0 else { return nil }
        let totalSeconds = durationMs / 1000
        let minutes = totalSeconds / 60
        let seconds = totalSeconds % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
}

// MARK: - GenreRef

public struct GenreRef: CanonicalEntity {
    public var id: String
    public var displayName: String
    public var synonyms: [String]

    public var displayLabel: String { displayName }

    public init(id: String, displayName: String, synonyms: [String] = []) {
        self.id = id
        self.displayName = displayName
        self.synonyms = synonyms
    }
}

// MARK: - KeywordRef

public struct KeywordRef: CanonicalEntity {
    public var id: String
    public var label: String

    public var displayLabel: String { label }

    public init(id: String, label: String) {
        self.id = id
        self.label = label
    }
}
