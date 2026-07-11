import Foundation

public protocol SessionHistoryServing: Sendable {
    func listHistory() async throws -> [SessionHistorySummary]
    func getHistorySession(sessionID: String) async throws -> SessionHistoryDetail?
    func deleteHistorySession(sessionID: String) async throws -> Bool
    func clearHistory() async throws -> Bool
    func exportHistorySession(sessionID: String) async throws -> SessionHistoryExport?
}

