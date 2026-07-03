import Foundation

@MainActor
public final class AutocompleteEngine<Provider: SuggestionProvider> {
    public typealias Entity = Provider.Entity

    public private(set) var session = SearchSession<Entity>()
    public private(set) var selection = CanonicalSelection<Entity>()

    private let provider: Provider
    private let recentSearchProvider: any RecentSearchStoring
    private let cache: AutocompleteCache
    private let entityKind: SmartInputEntityKind
    private let providerID: ProviderID
    private let debounceInterval: TimeInterval
    private let resultLimit: Int
    private var context: AutocompleteContext?
    private var searchTask: Task<Void, Never>?

    public init(
        provider: Provider,
        entityKind: SmartInputEntityKind,
        providerID: ProviderID = .appleMusic,
        recentSearchProvider: any RecentSearchStoring = UserDefaultsRecentSearchProvider.shared,
        cache: AutocompleteCache = AutocompleteCache(),
        debounceInterval: TimeInterval = 0.28,
        resultLimit: Int = 10
    ) {
        self.provider = provider
        self.entityKind = entityKind
        self.providerID = providerID
        self.recentSearchProvider = recentSearchProvider
        self.cache = cache
        self.debounceInterval = debounceInterval
        self.resultLimit = resultLimit
        reloadRecents()
    }

    public func setContext(_ context: AutocompleteContext?) {
        self.context = context
    }

    public func setSelected(_ entity: Entity?) {
        selection.selected = entity
        selection.query = entity?.displayLabel ?? ""
        selection.isEditing = false
        session.showsRecents = false
    }

    public func clearSelection() {
        selection = CanonicalSelection()
        session.query = ""
        session.results = []
        session.highlightedIndex = -1
        session.phase = .idle
    }

    public func beginEditing() {
        selection.isEditing = true
        if selection.selected != nil {
            selection.query = selection.selected?.displayLabel ?? ""
        }
        updateRecentsVisibility()
    }

    public func endEditing() {
        selection.isEditing = false
        session.showsRecents = false
        dismiss()
    }

    public func updateQuery(_ query: String) {
        selection.query = query
        session.query = query
        session.highlightedIndex = -1
        updateRecentsVisibility()

        let trimmed = query.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed.isEmpty {
            searchTask?.cancel()
            session.results = []
            session.phase = .idle
            return
        }

        searchTask?.cancel()
        session.phase = .debouncing
        searchTask = Task { [weak self] in
            guard let self else { return }
            do {
                try await Task.sleep(nanoseconds: UInt64(debounceInterval * 1_000_000_000))
            } catch {
                return
            }
            guard !Task.isCancelled else { return }
            await self.performSearch(query: trimmed)
        }
    }

    public func moveHighlight(delta: Int) {
        let items = session.visibleItems
        guard !items.isEmpty else {
            session.highlightedIndex = -1
            return
        }
        if session.highlightedIndex < 0 {
            session.highlightedIndex = delta > 0 ? 0 : items.count - 1
            return
        }
        let next = session.highlightedIndex + delta
        if next < 0 {
            session.highlightedIndex = items.count - 1
        } else if next >= items.count {
            session.highlightedIndex = 0
        } else {
            session.highlightedIndex = next
        }
    }

    @discardableResult
    public func selectHighlighted() -> Entity? {
        let items = session.visibleItems
        guard !items.isEmpty else { return nil }
        let index = session.highlightedIndex >= 0 ? session.highlightedIndex : 0
        guard items.indices.contains(index) else { return nil }
        return select(items[index])
    }

    @discardableResult
    public func select(_ entity: Entity) -> Entity {
        setSelected(entity)
        recentSearchProvider.record(entity, entityKind: entityKind)
        reloadRecents()
        dismiss()
        return entity
    }

    public func dismiss() {
        searchTask?.cancel()
        session.results = []
        session.highlightedIndex = -1
        session.phase = .idle
        session.showsRecents = selection.isEditing && session.query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    public func reloadRecents() {
        session.recents = recentSearchProvider.load(entityKind: entityKind)
    }

    private func updateRecentsVisibility() {
        session.showsRecents = selection.isEditing
            && session.query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    private func performSearch(query: String) async {
        session.phase = .searching
        if let cached: [Entity] = await cache.lookup(
            entityKind: entityKind,
            query: query,
            context: context
        ) {
            session.results = cached
            session.phase = .ready
            return
        }

        let request = AutocompleteRequest(
            providerID: providerID,
            entityKind: entityKind,
            query: query,
            limit: resultLimit,
            context: context
        )

        do {
            let results = try await provider.suggestions(for: request)
            guard !Task.isCancelled else { return }
            await cache.store(
                results,
                entityKind: entityKind,
                query: query,
                context: context
            )
            session.results = results
            session.phase = .ready
        } catch {
            guard !Task.isCancelled else { return }
            session.results = []
            session.phase = .error(error.localizedDescription)
        }
    }
}
