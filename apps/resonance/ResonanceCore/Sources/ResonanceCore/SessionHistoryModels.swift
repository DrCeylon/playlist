import Foundation

public enum SessionHistoryStatus: String, Codable, Sendable, CaseIterable {
    case generated
    case imported
    case partialSuccess = "partial_success"
    case failed
    case waitingForManualAcquisition = "waiting_for_manual_acquisition"
}

public struct SessionHistorySummary: Identifiable, Hashable, Sendable {
    public let id: String
    public let sessionID: String
    public let startedAtISO: String
    public let finishedAtISO: String
    public let playlistName: String
    public let providerID: ProviderID
    public let status: SessionHistoryStatus
    public let trackCount: Int
    public let addedCount: Int
    public let skippedCount: Int
    public let notFoundCount: Int
    public let errorCount: Int
    public let durationMS: Int?
    public let textReportPath: String
    public let jsonReportPath: String

    public init(
        sessionID: String,
        startedAtISO: String,
        finishedAtISO: String,
        playlistName: String,
        providerID: ProviderID,
        status: SessionHistoryStatus,
        trackCount: Int,
        addedCount: Int,
        skippedCount: Int,
        notFoundCount: Int,
        errorCount: Int,
        durationMS: Int?,
        textReportPath: String,
        jsonReportPath: String
    ) {
        id = sessionID
        self.sessionID = sessionID
        self.startedAtISO = startedAtISO
        self.finishedAtISO = finishedAtISO
        self.playlistName = playlistName
        self.providerID = providerID
        self.status = status
        self.trackCount = trackCount
        self.addedCount = addedCount
        self.skippedCount = skippedCount
        self.notFoundCount = notFoundCount
        self.errorCount = errorCount
        self.durationMS = durationMS
        self.textReportPath = textReportPath
        self.jsonReportPath = jsonReportPath
    }
}

public struct SessionHistoryDetail: Sendable {
    public let summary: SessionHistorySummary
    public let generationRequest: BridgeJSONObject
    public let generationResult: BridgeJSONObject
    public let importResult: BridgeJSONObject
    public let diagnostics: BridgeJSONObject

    public init(
        summary: SessionHistorySummary,
        generationRequest: BridgeJSONObject = [:],
        generationResult: BridgeJSONObject = [:],
        importResult: BridgeJSONObject = [:],
        diagnostics: BridgeJSONObject = [:]
    ) {
        self.summary = summary
        self.generationRequest = generationRequest
        self.generationResult = generationResult
        self.importResult = importResult
        self.diagnostics = diagnostics
    }
}

public struct SessionHistoryExport: Hashable, Sendable {
    public let sessionID: String
    public let playlistName: String
    public let providerID: ProviderID
    public let status: SessionHistoryStatus
    public let textReportPath: String
    public let jsonReportPath: String

    public init(
        sessionID: String,
        playlistName: String,
        providerID: ProviderID,
        status: SessionHistoryStatus,
        textReportPath: String,
        jsonReportPath: String
    ) {
        self.sessionID = sessionID
        self.playlistName = playlistName
        self.providerID = providerID
        self.status = status
        self.textReportPath = textReportPath
        self.jsonReportPath = jsonReportPath
    }
}
