import Foundation

public enum KeywordSuggestionSource: String, Sendable {
    case manual
    case automatic
}

public struct KeywordSuggestionInput: Sendable {
    public var artistName: String
    public var artistType: String
    public var trackTitle: String
    public var albumTitle: String
    public var releaseYear: Int?
    public var primaryGenreName: String

    public init(
        artistName: String = "",
        artistType: String = "",
        trackTitle: String = "",
        albumTitle: String = "",
        releaseYear: Int? = nil,
        primaryGenreName: String = ""
    ) {
        self.artistName = artistName
        self.artistType = artistType
        self.trackTitle = trackTitle
        self.albumTitle = albumTitle
        self.releaseYear = releaseYear
        self.primaryGenreName = primaryGenreName
    }

    public init(artist: ArtistRef?, track: TrackRef?) {
        artistName = artist?.displayName ?? track?.artistName ?? ""
        artistType = artist?.artistType ?? ""
        trackTitle = track?.title ?? ""
        albumTitle = track?.albumTitle ?? ""
        releaseYear = track?.releaseYear
        primaryGenreName = track?.genreName ?? ""
    }
}

public enum KeywordSuggestionEngine {
    private static let stopWords: Set<String> = [
        "a", "an", "and", "de", "du", "feat", "featuring", "in", "la", "le", "les", "of", "the", "with", "ft", "vs",
    ]

    private static let moodKeywords: [String: [String]] = [
        "calm": ["calm", "chill", "relax", "soft"],
        "dramatic": ["dramatic", "epic", "orchestral"],
        "energetic": ["energy", "energetic", "intense", "power"],
        "happy": ["happy", "joy", "sunshine", "smile"],
        "melancholic": ["sad", "lonely", "tears", "blue"],
        "romantic": ["love", "heart", "kiss", "romance"],
        "summer": ["summer", "sun", "beach", "festival"],
        "upbeat": ["upbeat", "party", "dance", "groove"],
    ]

    private static let genreHints: [String: [String]] = [
        "alternative": ["alternative", "alt rock", "indie"],
        "dance": ["dance", "edm", "house", "club"],
        "electronic": ["electronic", "electro", "synth"],
        "hip-hop": ["hip hop", "rap", "trap"],
        "pop": ["pop"],
        "rock": ["rock", "metal", "punk"],
    ]

    public static func suggestKeywords(from input: KeywordSuggestionInput) -> [String] {
        var suggestions: [String] = []

        func add(_ value: String) {
            let normalized = normalizeKeyword(value)
            guard !normalized.isEmpty, !suggestions.contains(normalized) else { return }
            suggestions.append(normalized)
        }

        if !input.primaryGenreName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            add(input.primaryGenreName)
            for keyword in genreHints(from: input.primaryGenreName) {
                add(keyword)
            }
        }

        for keyword in titleKeywords(input.trackTitle) {
            add(keyword)
        }

        if !input.albumTitle.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            for keyword in titleKeywords(input.albumTitle, maxTokens: 2) {
                add(keyword)
            }
        }

        if let releaseYear = input.releaseYear, releaseYear >= 1900 {
            let decade = (releaseYear / 10) * 10
            add("\(decade)s")
        }

        let haystack = "\(input.trackTitle) \(input.albumTitle)".lowercased()
        for (mood, triggers) in moodKeywords {
            if triggers.contains(where: { haystack.contains($0) }) {
                add(mood)
            }
        }

        let artistType = input.artistType.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        if ["band", "group", "orchestra"].contains(artistType) {
            add(artistType)
        }

        if suggestions.isEmpty, !input.artistName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            for keyword in titleKeywords(input.artistName, maxTokens: 1) {
                add(keyword)
            }
        }

        return Array(suggestions.prefix(8))
    }

    public static func automaticKeywordRefs(from input: KeywordSuggestionInput) -> [KeywordRef] {
        suggestKeywords(from: input).map { label in
            KeywordRef(
                id: "auto:\(label.lowercased().replacingOccurrences(of: " ", with: "-"))",
                label: label,
                source: .automatic
            )
        }
    }

    public static func mergeAutomaticKeywords(
        existing: [KeywordRef],
        suggested: [KeywordRef]
    ) -> [KeywordRef] {
        var merged = existing
        let manualLabels = Set(existing.filter { $0.source == .manual }.map { normalizeKeyword($0.label) })
        let existingLabels = Set(existing.map { normalizeKeyword($0.label) })

        for keyword in suggested {
            let normalized = normalizeKeyword(keyword.label)
            guard !normalized.isEmpty else { continue }
            if manualLabels.contains(normalized) || existingLabels.contains(normalized) {
                continue
            }
            merged.append(keyword)
        }
        return merged
    }

    private static func genreHints(from value: String) -> [String] {
        let lowered = value.lowercased()
        return genreHints.compactMap { keyword, triggers in
            triggers.contains(where: { lowered.contains($0) }) ? keyword : nil
        }
    }

    private static func titleKeywords(_ value: String, maxTokens: Int = 3) -> [String] {
        var cleaned = value
        cleaned = cleaned.replacingOccurrences(of: #"\([^)]*\)"#, with: " ", options: .regularExpression)
        cleaned = cleaned.replacingOccurrences(of: #"\[[^]]*\]"#, with: " ", options: .regularExpression)
        cleaned = cleaned.replacingOccurrences(of: #"(?i)\bfeat\.?.*$"#, with: " ", options: .regularExpression)

        let tokens = cleaned
            .components(separatedBy: CharacterSet.alphanumerics.inverted)
            .map(normalizeKeyword)
            .filter { !$0.isEmpty && !stopWords.contains($0) && $0.count >= 3 }

        var result: [String] = []
        for token in tokens where !result.contains(token) {
            result.append(token)
            if result.count >= maxTokens {
                break
            }
        }
        return result
    }

    private static func normalizeKeyword(_ value: String) -> String {
        value
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .lowercased()
            .folding(options: [.diacriticInsensitive, .caseInsensitive], locale: .current)
            .replacingOccurrences(of: #"[^a-z0-9]+"#, with: " ", options: .regularExpression)
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }
}
