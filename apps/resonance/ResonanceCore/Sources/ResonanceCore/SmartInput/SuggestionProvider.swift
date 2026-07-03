import Foundation

enum AutocompleteArtistNameMatching {
    static func matches(wanted: String, candidate: String) -> Bool {
        let wantedNorm = wanted.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        let candidateNorm = candidate.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        if wantedNorm.isEmpty { return true }
        if candidateNorm.isEmpty { return false }
        if wantedNorm == candidateNorm { return true }
        return candidateNorm.contains(wantedNorm) || wantedNorm.contains(candidateNorm)
    }
}

public protocol SuggestionProvider<Entity>: Sendable {
    associatedtype Entity: CanonicalEntity
    func suggestions(for request: AutocompleteRequest) async throws -> [Entity]
}

public struct BridgeArtistSuggestionProvider: SuggestionProvider {
    private let service: any AutocompleteServing

    public init(service: any AutocompleteServing) {
        self.service = service
    }

    public func suggestions(for request: AutocompleteRequest) async throws -> [ArtistRef] {
        let response = try await service.search(request: request)
        return response.artists
    }
}

public struct BridgeTrackSuggestionProvider: SuggestionProvider {
    private let service: any AutocompleteServing

    public init(service: any AutocompleteServing) {
        self.service = service
    }

    public func suggestions(for request: AutocompleteRequest) async throws -> [TrackRef] {
        let response = try await service.search(request: request)
        return response.tracks
    }
}

public struct LocalGenreSuggestionProvider: SuggestionProvider {
    private let service: any AutocompleteServing

    public init(service: any AutocompleteServing) {
        self.service = service
    }

    public func suggestions(for request: AutocompleteRequest) async throws -> [GenreRef] {
        let response = try await service.search(request: request)
        return response.genres
    }
}

public struct LocalKeywordSuggestionProvider: SuggestionProvider {
    private let service: any AutocompleteServing

    public init(service: any AutocompleteServing) {
        self.service = service
    }

    public func suggestions(for request: AutocompleteRequest) async throws -> [KeywordRef] {
        let response = try await service.search(request: request)
        return response.keywords
    }
}

public struct MockArtistSuggestionProvider: SuggestionProvider {
    private let fixtures: [ArtistRef]

    public init(fixtures: [ArtistRef] = MockAutocompleteFixtures.artists) {
        self.fixtures = fixtures
    }

    public func suggestions(for request: AutocompleteRequest) async throws -> [ArtistRef] {
        let query = request.query.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !query.isEmpty else { return [] }
        return fixtures.filter { $0.displayName.lowercased().contains(query) }
    }
}

public struct MockTrackSuggestionProvider: SuggestionProvider {
    private let fixtures: [TrackRef]

    public init(fixtures: [TrackRef] = MockAutocompleteFixtures.tracks) {
        self.fixtures = fixtures
    }

    public func suggestions(for request: AutocompleteRequest) async throws -> [TrackRef] {
        let query = request.query.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !query.isEmpty else { return [] }
        let artistContext = request.context?.artistName ?? ""
        return fixtures
            .filter { track in
                guard AutocompleteArtistNameMatching.matches(wanted: artistContext, candidate: track.artistName) else {
                    return false
                }
                return track.title.lowercased().contains(query)
                    || track.artistName.lowercased().contains(query)
            }
            .sorted { $0.title < $1.title }
    }
}

public enum MockAutocompleteFixtures {
    public static let artists: [ArtistRef] = [
        ArtistRef(id: "muse", displayName: "Muse"),
        ArtistRef(id: "daft-punk", displayName: "Daft Punk"),
        ArtistRef(id: "kygo", displayName: "Kygo"),
        ArtistRef(id: "nayeon", displayName: "NAYEON"),
        ArtistRef(id: "coldplay", displayName: "Coldplay"),
    ]

    public static let tracks: [TrackRef] = [
        TrackRef(id: "firestone", title: "Firestone", artistName: "Kygo", albumTitle: "Cloud Nine", releaseYear: 2016, durationMs: 271_000),
        TrackRef(id: "starlight", title: "Starlight", artistName: "Muse", albumTitle: "Black Holes and Revelations", releaseYear: 2006, durationMs: 242_000),
        TrackRef(id: "get-lucky", title: "Get Lucky", artistName: "Daft Punk", albumTitle: "Random Access Memories", releaseYear: 2013, durationMs: 369_000),
    ]

    public static let genres: [GenreRef] = [
        GenreRef(id: "hip-hop", displayName: "Hip-Hop", synonyms: ["Hip Hop"]),
        GenreRef(id: "alternative-rock", displayName: "Alternative Rock", synonyms: ["Rock alternatif"]),
        GenreRef(id: "heavy-metal", displayName: "Heavy Metal", synonyms: ["Metal"]),
    ]

    public static let keywords: [KeywordRef] = [
        KeywordRef(id: "summer", label: "Summer"),
        KeywordRef(id: "pool-party", label: "Pool Party"),
        KeywordRef(id: "relax", label: "Relax"),
        KeywordRef(id: "driving", label: "Driving"),
    ]
}
