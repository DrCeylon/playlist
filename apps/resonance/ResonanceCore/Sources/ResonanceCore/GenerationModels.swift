import Foundation

public struct SeedReference: Hashable, Codable, Sendable {
    public var artist: String
    public var title: String
    public var weight: Double

    public init(artist: String = "", title: String = "", weight: Double = 1.0) {
        self.artist = artist
        self.title = title
        self.weight = weight
    }

    public var label: String {
        let trimmedArtist = artist.trimmingCharacters(in: .whitespacesAndNewlines)
        let trimmedTitle = title.trimmingCharacters(in: .whitespacesAndNewlines)
        if !trimmedArtist.isEmpty && !trimmedTitle.isEmpty {
            return "\(trimmedArtist) — \(trimmedTitle)"
        }
        return trimmedArtist.isEmpty ? trimmedTitle : trimmedArtist
    }
}

public struct EnergyCurveOption: Hashable, Codable, Sendable {
    public var profile: EnergyCurveProfile
    public var chapterLabels: [String]

    public init(profile: EnergyCurveProfile = .rising, chapterLabels: [String] = []) {
        self.profile = profile
        self.chapterLabels = chapterLabels
    }
}

public struct ExclusionRule: Identifiable, Hashable, Codable, Sendable {
    public let id: UUID
    public var kind: ExclusionKind
    public var value: String
    public var reason: String

    public init(
        id: UUID = UUID(),
        kind: ExclusionKind = .artist,
        value: String = "",
        reason: String = ""
    ) {
        self.id = id
        self.kind = kind
        self.value = value
        self.reason = reason
    }
}

public struct PlaylistGenerationRequest: Hashable, Codable, Sendable {
    public var name: String
    public var providerID: ProviderID
    public var seeds: [SeedReference]
    public var keywords: [String]
    public var description: String
    public var targetTrackCount: Int?
    public var targetDurationMinutes: Int?
    public var energyCurve: EnergyCurveOption
    public var exclusions: [ExclusionRule]
    public var playlistTheme: String

    public init(
        name: String = "",
        providerID: ProviderID = .appleMusic,
        seeds: [SeedReference] = [],
        keywords: [String] = [],
        description: String = "",
        targetTrackCount: Int? = nil,
        targetDurationMinutes: Int? = nil,
        energyCurve: EnergyCurveOption = EnergyCurveOption(),
        exclusions: [ExclusionRule] = [],
        playlistTheme: String = ""
    ) {
        self.name = name
        self.providerID = providerID
        self.seeds = seeds
        self.keywords = keywords
        self.description = description
        self.targetTrackCount = targetTrackCount
        self.targetDurationMinutes = targetDurationMinutes
        self.energyCurve = energyCurve
        self.exclusions = exclusions
        self.playlistTheme = playlistTheme
    }
}

public struct GeneratedTrackPreview: Identifiable, Hashable, Codable, Sendable {
    public let id: UUID
    public var artist: String
    public var title: String
    public var section: String
    public var score: Double
    public var confidence: ConfidenceLevel
    public var source: String

    public init(
        id: UUID = UUID(),
        artist: String,
        title: String,
        section: String,
        score: Double,
        confidence: ConfidenceLevel = .medium,
        source: String = ""
    ) {
        self.id = id
        self.artist = artist
        self.title = title
        self.section = section
        self.score = score
        self.confidence = confidence
        self.source = source
    }
}

public struct GeneratedSectionPreview: Identifiable, Hashable, Codable, Sendable {
    public let id: UUID
    public var name: String
    public var tracks: [GeneratedTrackPreview]

    public init(id: UUID = UUID(), name: String, tracks: [GeneratedTrackPreview] = []) {
        self.id = id
        self.name = name
        self.tracks = tracks
    }
}

public struct PlaylistGenerationResult: Hashable, Codable, Sendable {
    public var playlistName: String
    public var sections: [GeneratedSectionPreview]
    public var averageScore: Double
    public var providerID: ProviderID
    public var historySessionID: String
    public var targetTrackCount: Int?
    public var shortfallMessage: String

    public init(
        playlistName: String,
        sections: [GeneratedSectionPreview] = [],
        averageScore: Double = 0,
        providerID: ProviderID = .appleMusic,
        historySessionID: String = "",
        targetTrackCount: Int? = nil,
        shortfallMessage: String = ""
    ) {
        self.playlistName = playlistName
        self.sections = sections
        self.averageScore = averageScore
        self.providerID = providerID
        self.historySessionID = historySessionID
        self.targetTrackCount = targetTrackCount
        self.shortfallMessage = shortfallMessage
    }

    public var trackCount: Int {
        sections.reduce(0) { $0 + $1.tracks.count }
    }

    public var isShort: Bool {
        guard let targetTrackCount else { return false }
        return trackCount < targetTrackCount
    }
}
