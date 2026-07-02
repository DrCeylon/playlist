import Foundation

public enum SmartInputEntityKind: String, Codable, Sendable, CaseIterable {
    case artist
    case track
    case genre
    case keyword
}

public struct AutocompleteContext: Hashable, Codable, Sendable {
    public var artistName: String
    public var artistID: String

    public init(artistName: String = "", artistID: String = "") {
        self.artistName = artistName
        self.artistID = artistID
    }
}

public struct AutocompleteRequest: Hashable, Codable, Sendable {
    public var providerID: ProviderID
    public var entityKind: SmartInputEntityKind
    public var query: String
    public var limit: Int
    public var context: AutocompleteContext?

    public init(
        providerID: ProviderID = .appleMusic,
        entityKind: SmartInputEntityKind,
        query: String,
        limit: Int = 10,
        context: AutocompleteContext? = nil
    ) {
        self.providerID = providerID
        self.entityKind = entityKind
        self.query = query
        self.limit = limit
        self.context = context
    }
}

public enum AutocompleteSearchPhase: Equatable, Sendable {
    case idle
    case debouncing
    case searching
    case ready
    case error(String)
}

public struct SearchSession<Entity: CanonicalEntity>: Equatable, Sendable {
    public var query: String
    public var results: [Entity]
    public var highlightedIndex: Int
    public var phase: AutocompleteSearchPhase
    public var showsRecents: Bool
    public var recents: [Entity]

    public init(
        query: String = "",
        results: [Entity] = [],
        highlightedIndex: Int = -1,
        phase: AutocompleteSearchPhase = .idle,
        showsRecents: Bool = false,
        recents: [Entity] = []
    ) {
        self.query = query
        self.results = results
        self.highlightedIndex = highlightedIndex
        self.phase = phase
        self.showsRecents = showsRecents
        self.recents = recents
    }

    public var visibleItems: [Entity] {
        showsRecents && query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? recents : results
    }

    public var isPanelVisible: Bool {
        !visibleItems.isEmpty || phase == .searching
    }
}

public struct CanonicalSelection<Entity: CanonicalEntity>: Equatable, Sendable {
    public var selected: Entity?
    public var query: String
    public var isEditing: Bool

    public init(selected: Entity? = nil, query: String = "", isEditing: Bool = false) {
        self.selected = selected
        self.query = query
        self.isEditing = isEditing
    }
}
