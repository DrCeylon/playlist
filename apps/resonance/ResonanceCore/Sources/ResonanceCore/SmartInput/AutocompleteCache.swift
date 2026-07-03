import Foundation

public actor AutocompleteCache {
    public struct Entry: Sendable {
        public let results: [AnySendableEntity]
        public let expiresAt: Date
    }

    public struct AnySendableEntity: Sendable {
        public let id: String
        public let payload: Data

        public init<Entity: CanonicalEntity & Codable>(_ entity: Entity) throws {
            self.id = String(describing: entity.id)
            self.payload = try JSONEncoder().encode(entity)
        }

        public func decode<Entity: CanonicalEntity & Codable>(as type: Entity.Type) -> Entity? {
            try? JSONDecoder().decode(Entity.self, from: payload)
        }
    }

    private struct CacheKey: Hashable {
        let entityKind: SmartInputEntityKind
        let normalizedQuery: String
        let contextHash: String
    }

    private var storage: [CacheKey: Entry] = [:]
    private var accessOrder: [CacheKey] = []
    private let maxEntries: Int
    private let defaultTTL: TimeInterval

    public init(maxEntries: Int = 128, defaultTTL: TimeInterval = 300) {
        self.maxEntries = maxEntries
        self.defaultTTL = defaultTTL
    }

    public func lookup<Entity: CanonicalEntity & Codable>(
        entityKind: SmartInputEntityKind,
        query: String,
        context: AutocompleteContext?
    ) -> [Entity]? {
        purgeExpired()
        let key = makeKey(entityKind: entityKind, query: query, context: context)
        guard let entry = storage[key], entry.expiresAt > Date() else {
            storage.removeValue(forKey: key)
            accessOrder.removeAll { $0 == key }
            return nil
        }
        touch(key)
        return entry.results.compactMap { $0.decode(as: Entity.self) }
    }

    public func store<Entity: CanonicalEntity & Codable>(
        _ results: [Entity],
        entityKind: SmartInputEntityKind,
        query: String,
        context: AutocompleteContext?,
        ttl: TimeInterval? = nil
    ) {
        purgeExpired()
        let key = makeKey(entityKind: entityKind, query: query, context: context)
        let wrapped = results.compactMap { try? AnySendableEntity($0) }
        let expiresAt = Date().addingTimeInterval(ttl ?? defaultTTL)
        storage[key] = Entry(results: wrapped, expiresAt: expiresAt)
        touch(key)
        while accessOrder.count > maxEntries, let oldest = accessOrder.first {
            storage.removeValue(forKey: oldest)
            accessOrder.removeFirst()
        }
    }

    public func clear() {
        storage.removeAll()
        accessOrder.removeAll()
    }

    private func makeKey(
        entityKind: SmartInputEntityKind,
        query: String,
        context: AutocompleteContext?
    ) -> CacheKey {
        let normalized = query.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        let contextHash = [
            context?.artistName ?? "",
            context?.artistID ?? "",
        ].joined(separator: "|")
        return CacheKey(entityKind: entityKind, normalizedQuery: normalized, contextHash: contextHash)
    }

    private func touch(_ key: CacheKey) {
        accessOrder.removeAll { $0 == key }
        accessOrder.append(key)
    }

    private func purgeExpired() {
        let now = Date()
        for key in storage.keys where storage[key]?.expiresAt ?? .distantPast <= now {
            storage.removeValue(forKey: key)
            accessOrder.removeAll { $0 == key }
        }
    }
}
