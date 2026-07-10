import Foundation

public enum ProviderID: String, Codable, CaseIterable, Identifiable, Sendable {
    case appleMusic = "apple_music"
    case appleMusicKit = "apple_musickit"
    case spotify = "spotify"
    case youtubeMusic = "youtube_music"
    case deezer = "deezer"
    case soundcloud = "soundcloud"
    case tidal = "tidal"
    case qobuz = "qobuz"
    case bandcamp = "bandcamp"
    case plex = "plex"
    case jellyfin = "jellyfin"
    case navidrome = "navidrome"
    case subsonic = "subsonic"
    case localFiles = "local_files"
    case discogs = "discogs"
    case musicbrainz = "musicbrainz"

    public var id: String { rawValue }
}

public enum EnergyCurveProfile: String, Codable, CaseIterable, Identifiable, Sendable {
    case chill = "chill"
    case steady = "steady"
    case rising = "rising"
    case party = "party"
    case maxFromStart = "max_from_start"
    case random = "random"

    public var id: String { rawValue }

    public var displayName: String {
        switch self {
        case .chill:
            return "Repos"
        case .steady:
            return "Stable"
        case .rising:
            return "Montée progressive"
        case .party:
            return "Party"
        case .maxFromStart:
            return "Max dès le début"
        case .random:
            return "Aléatoire"
        }
    }
}

public enum ExclusionKind: String, Codable, CaseIterable, Identifiable, Sendable {
    case artist = "artist"
    case album = "album"
    case track = "track"
    case genre = "genre"
    case mood = "mood"
    case language = "language"

    public var id: String { rawValue }

    public var displayName: String {
        switch self {
        case .artist:
            return "Artiste"
        case .album:
            return "Album"
        case .track:
            return "Morceau"
        case .genre:
            return "Genre"
        case .mood:
            return "Ambiance"
        case .language:
            return "Langue"
        }
    }
}

public enum ConfidenceLevel: String, Codable, Sendable {
    case low = "low"
    case medium = "medium"
    case high = "high"
}
