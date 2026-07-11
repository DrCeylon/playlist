import Foundation
import ResonanceCore

public struct MockSessionHistoryService: SessionHistoryServing {
    public var sessions: [SessionHistorySummary]

    public init(sessions: [SessionHistorySummary] = []) {
        self.sessions = sessions
    }

    public func listHistory() async throws -> [SessionHistorySummary] {
        sessions
    }

    public func getHistorySession(sessionID: String) async throws -> SessionHistoryDetail? {
        nil
    }

    public func deleteHistorySession(sessionID: String) async throws -> Bool {
        false
    }

    public func clearHistory() async throws -> Bool {
        false
    }

    public func exportHistorySession(sessionID: String) async throws -> SessionHistoryExport? {
        nil
    }
}
