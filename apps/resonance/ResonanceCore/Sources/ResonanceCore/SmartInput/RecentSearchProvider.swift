import Foundation

public protocol RecentSearchStoring: Sendable {
    func load<Entity: CanonicalEntity>(entityKind: SmartInputEntityKind) -> [Entity]
    func record<Entity: CanonicalEntity>(_ entity: Entity, entityKind: SmartInputEntityKind)
    func remove<Entity: CanonicalEntity>(_ entity: Entity, entityKind: SmartInputEntityKind)
    func clear(entityKind: SmartInputEntityKind)
}

public final class UserDefaultsRecentSearchProvider: RecentSearchStoring, @unchecked Sendable {
    public static let shared = UserDefaultsRecentSearchProvider()

    private let defaults: UserDefaults
    private let maxEntries: Int
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()
    private let lock = NSLock()

    public init(defaults: UserDefaults = .standard, maxEntries: Int = 12) {
        self.defaults = defaults
        self.maxEntries = maxEntries
    }

    public func load<Entity: CanonicalEntity>(entityKind: SmartInputEntityKind) -> [Entity] {
        lock.lock()
        defer { lock.unlock() }
        guard let data = defaults.data(forKey: storageKey(entityKind)) else { return [] }
        return (try? decoder.decode([Entity].self, from: data)) ?? []
    }

    public func record<Entity: CanonicalEntity>(_ entity: Entity, entityKind: SmartInputEntityKind) {
        lock.lock()
        defer { lock.unlock() }
        var entries: [Entity] = loadUnlocked(entityKind: entityKind)
        entries.removeAll { $0.id == entity.id }
        entries.insert(entity, at: 0)
        if entries.count > maxEntries {
            entries = Array(entries.prefix(maxEntries))
        }
        if let data = try? encoder.encode(entries) {
            defaults.set(data, forKey: storageKey(entityKind))
        }
    }

    public func remove<Entity: CanonicalEntity>(_ entity: Entity, entityKind: SmartInputEntityKind) {
        lock.lock()
        defer { lock.unlock() }
        var entries: [Entity] = loadUnlocked(entityKind: entityKind)
        entries.removeAll { $0.id == entity.id }
        if let data = try? encoder.encode(entries) {
            defaults.set(data, forKey: storageKey(entityKind))
        }
    }

    public func clear(entityKind: SmartInputEntityKind) {
        lock.lock()
        defer { lock.unlock() }
        defaults.removeObject(forKey: storageKey(entityKind))
    }

    private func loadUnlocked<Entity: CanonicalEntity>(entityKind: SmartInputEntityKind) -> [Entity] {
        guard let data = defaults.data(forKey: storageKey(entityKind)) else { return [] }
        return (try? decoder.decode([Entity].self, from: data)) ?? []
    }

    private func storageKey(_ entityKind: SmartInputEntityKind) -> String {
        "resonance.smartinput.recents.\(entityKind.rawValue)"
    }
}

public final class InMemoryRecentSearchProvider: RecentSearchStoring, @unchecked Sendable {
    private var storage: [SmartInputEntityKind: Data] = [:]
    private let maxEntries: Int
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()
    private let lock = NSLock()

    public init(maxEntries: Int = 12) {
        self.maxEntries = maxEntries
    }

    public func load<Entity: CanonicalEntity>(entityKind: SmartInputEntityKind) -> [Entity] {
        lock.lock()
        defer { lock.unlock() }
        guard let data = storage[entityKind] else { return [] }
        return (try? decoder.decode([Entity].self, from: data)) ?? []
    }

    public func record<Entity: CanonicalEntity>(_ entity: Entity, entityKind: SmartInputEntityKind) {
        lock.lock()
        defer { lock.unlock() }
        var entries: [Entity] = []
        if let data = storage[entityKind] {
            entries = (try? decoder.decode([Entity].self, from: data)) ?? []
        }
        entries.removeAll { $0.id == entity.id }
        entries.insert(entity, at: 0)
        if entries.count > maxEntries {
            entries = Array(entries.prefix(maxEntries))
        }
        storage[entityKind] = try? encoder.encode(entries)
    }

    public func remove<Entity: CanonicalEntity>(_ entity: Entity, entityKind: SmartInputEntityKind) {
        lock.lock()
        defer { lock.unlock() }
        guard let data = storage[entityKind] else { return }
        var entries: [Entity] = (try? decoder.decode([Entity].self, from: data)) ?? []
        entries.removeAll { $0.id == entity.id }
        storage[entityKind] = try? encoder.encode(entries)
    }

    public func clear(entityKind: SmartInputEntityKind) {
        lock.lock()
        defer { lock.unlock() }
        storage.removeValue(forKey: entityKind)
    }
}
