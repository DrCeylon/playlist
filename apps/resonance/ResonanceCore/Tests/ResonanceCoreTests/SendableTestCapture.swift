import Foundation

/// Thread-safe box for values captured from `@Sendable` closures in tests.
final class LockedBox<Value>: @unchecked Sendable {
    private let lock = NSLock()
    private var storage: Value

    init(_ initialValue: Value) {
        storage = initialValue
    }

    func withLock<R>(_ body: (inout Value) -> R) -> R {
        lock.lock()
        defer { lock.unlock() }
        return body(&storage)
    }

    var value: Value {
        withLock { $0 }
    }
}

extension LockedBox where Value == Int {
    func increment(by amount: Int = 1) {
        withLock { $0 += amount }
    }
}
