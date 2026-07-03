import Foundation

public struct AutocompleteResponse: Hashable, Sendable {
    public var artists: [ArtistRef]
    public var tracks: [TrackRef]
    public var genres: [GenreRef]
    public var keywords: [KeywordRef]

    public init(
        artists: [ArtistRef] = [],
        tracks: [TrackRef] = [],
        genres: [GenreRef] = [],
        keywords: [KeywordRef] = []
    ) {
        self.artists = artists
        self.tracks = tracks
        self.genres = genres
        self.keywords = keywords
    }
}

public enum AutocompleteBridgeContracts {
    public static func requestDictionary(_ request: AutocompleteRequest) -> BridgeJSONObject {
        var payload: BridgeJSONObject = [
            "provider_id": .string(request.providerID.rawValue),
            "entity_kind": .string(request.entityKind.rawValue),
            "query": .string(request.query),
            "limit": .number(Double(request.limit)),
        ]
        if let context = request.context {
            var contextObject: BridgeJSONObject = [:]
            if !context.artistName.isEmpty {
                contextObject["artist_name"] = .string(context.artistName)
            }
            if !context.artistID.isEmpty {
                contextObject["artist_id"] = .string(context.artistID)
            }
            if !contextObject.isEmpty {
                payload["context"] = .object(contextObject)
            }
        }
        return payload
    }

    public static func parseResponse(_ result: BridgeJSONObject, entityKind: SmartInputEntityKind) -> AutocompleteResponse {
        guard case .array(let suggestions) = result["suggestions"] else {
            return AutocompleteResponse()
        }

        var artists: [ArtistRef] = []
        var tracks: [TrackRef] = []
        var genres: [GenreRef] = []
        var keywords: [KeywordRef] = []

        for item in suggestions {
            guard case .object(let object) = item else { continue }
            switch entityKind {
            case .artist:
                if let artist = parseArtist(object) { artists.append(artist) }
            case .track:
                if let track = parseTrack(object) { tracks.append(track) }
            case .genre:
                if let genre = parseGenre(object) { genres.append(genre) }
            case .keyword:
                if let keyword = parseKeyword(object) { keywords.append(keyword) }
            }
        }

        return AutocompleteResponse(artists: artists, tracks: tracks, genres: genres, keywords: keywords)
    }

    private static func parseArtist(_ object: BridgeJSONObject) -> ArtistRef? {
        guard case .string(let id) = object["id"],
              case .string(let displayName) = object["display_name"] else {
            return nil
        }
        let sortName: String?
        if case .string(let value) = object["sort_name"] { sortName = value } else { sortName = nil }

        let artworkURL: URL?
        if case .string(let value) = object["artwork_url"], let url = URL(string: value) {
            artworkURL = url
        } else {
            artworkURL = nil
        }

        let albumCount: Int?
        if case .number(let value) = object["album_count"] { albumCount = Int(value) } else { albumCount = nil }

        let artistType: String?
        if case .string(let value) = object["artist_type"] { artistType = value } else { artistType = nil }

        return ArtistRef(
            id: id,
            displayName: displayName,
            sortName: sortName,
            artworkURL: artworkURL,
            albumCount: albumCount,
            artistType: artistType
        )
    }

    private static func parseTrack(_ object: BridgeJSONObject) -> TrackRef? {
        guard case .string(let id) = object["id"],
              case .string(let title) = object["title"],
              case .string(let artistName) = object["artist_name"] else {
            return nil
        }

        let albumTitle: String?
        if case .string(let value) = object["album_title"] { albumTitle = value } else { albumTitle = nil }

        let releaseYear: Int?
        if case .number(let value) = object["release_year"] { releaseYear = Int(value) } else { releaseYear = nil }

        let durationMs: Int?
        if case .number(let value) = object["duration_ms"] { durationMs = Int(value) } else { durationMs = nil }

        let artworkURL: URL?
        if case .string(let value) = object["artwork_url"], let url = URL(string: value) {
            artworkURL = url
        } else {
            artworkURL = nil
        }

        return TrackRef(
            id: id,
            title: title,
            artistName: artistName,
            albumTitle: albumTitle,
            releaseYear: releaseYear,
            durationMs: durationMs,
            artworkURL: artworkURL
        )
    }

    private static func parseGenre(_ object: BridgeJSONObject) -> GenreRef? {
        guard case .string(let id) = object["id"],
              case .string(let displayName) = object["display_name"] else {
            return nil
        }
        var synonyms: [String] = []
        if case .array(let values) = object["synonyms"] {
            synonyms = values.compactMap { value in
                if case .string(let text) = value { return text }
                return nil
            }
        }
        return GenreRef(id: id, displayName: displayName, synonyms: synonyms)
    }

    private static func parseKeyword(_ object: BridgeJSONObject) -> KeywordRef? {
        guard case .string(let id) = object["id"],
              case .string(let label) = object["label"] else {
            return nil
        }
        return KeywordRef(id: id, label: label)
    }
}

public protocol AutocompleteServing: Sendable {
    func search(request: AutocompleteRequest) async throws -> AutocompleteResponse
}

public struct MockAutocompleteService: AutocompleteServing {
    public init() {}

    public func search(request: AutocompleteRequest) async throws -> AutocompleteResponse {
        let query = request.query.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        switch request.entityKind {
        case .artist:
            let artists = MockAutocompleteFixtures.artists.filter { $0.displayName.lowercased().contains(query) }
            return AutocompleteResponse(artists: artists)
        case .track:
            let artistContext = request.context?.artistName ?? ""
            let tracks = MockAutocompleteFixtures.tracks
                .filter { track in
                    guard AutocompleteArtistNameMatching.matches(wanted: artistContext, candidate: track.artistName) else {
                        return false
                    }
                    return track.title.lowercased().contains(query) || track.artistName.lowercased().contains(query)
                }
                .sorted { $0.title < $1.title }
            return AutocompleteResponse(tracks: tracks)
        case .genre:
            let genres = MockAutocompleteFixtures.genres.filter {
                $0.displayName.lowercased().contains(query)
                    || $0.synonyms.contains { $0.lowercased().contains(query) }
            }
            return AutocompleteResponse(genres: genres)
        case .keyword:
            let keywords = MockAutocompleteFixtures.keywords.filter { $0.label.lowercased().contains(query) }
            if keywords.isEmpty, !query.isEmpty {
                return AutocompleteResponse(keywords: [KeywordRef(id: query.replacingOccurrences(of: " ", with: "-"), label: request.query.trimmingCharacters(in: .whitespacesAndNewlines))])
            }
            return AutocompleteResponse(keywords: keywords)
        }
    }
}
