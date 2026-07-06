import Foundation

/// Horodatage et delta inter-étapes pour le flux « J'ai ajouté le morceau, continuer ».
/// Écrit sur stderr : `manual-continue-trace: [HH:mm:ss.SSS] (+Nms) …`
public enum ManualContinueTrace {
    private static let lock = NSLock()
    private static var sessionID = ""
    private static var lastTimestamp: Date?

    private static let timeFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = .current
        formatter.dateFormat = "HH:mm:ss.SSS"
        return formatter
    }()

    public static func beginSession(importSessionID: String) {
        lock.lock()
        defer { lock.unlock() }
        sessionID = importSessionID
        lastTimestamp = nil
        emit("BEGIN session import_session_id=\(importSessionID)")
    }

    public static func log(_ message: String) {
        lock.lock()
        defer { lock.unlock() }
        emit(message)
    }

    private static func emit(_ message: String) {
        let now = Date()
        let deltaLabel: String
        if let lastTimestamp {
            let deltaMs = max(0, Int(now.timeIntervalSince(lastTimestamp) * 1000))
            deltaLabel = " (+\(deltaMs)ms)"
        } else {
            deltaLabel = ""
        }
        lastTimestamp = now
        let timestamp = timeFormatter.string(from: now)
        let sessionSuffix = sessionID.isEmpty ? "" : " [session=\(sessionID)]"
        let line = "manual-continue-trace: [\(timestamp)]\(deltaLabel)\(sessionSuffix) \(message)\n"
        if let data = line.data(using: .utf8) {
            FileHandle.standardError.write(data)
        }
    }
}
