import Foundation

public enum DiagnosticLevel: String, Codable, Sendable, CaseIterable {
    case debug
    case info
    case warning
    case error
}

public struct DiagnosticEventPayload: Hashable, Sendable {
    public let key: String
    public let value: String

    public init(key: String, value: String) {
        self.key = key
        self.value = value
    }
}

public struct DiagnosticEvent: Identifiable, Hashable, Sendable {
    public let id: UUID
    public let phase: String
    public let message: String
    public let level: DiagnosticLevel
    public let timestampISO: String
    public let payload: [DiagnosticEventPayload]

    public init(
        id: UUID = UUID(),
        phase: String,
        message: String,
        level: DiagnosticLevel = .info,
        timestampISO: String = "",
        payload: [DiagnosticEventPayload] = []
    ) {
        self.id = id
        self.phase = phase
        self.message = message
        self.level = level
        self.timestampISO = timestampISO
        self.payload = payload
    }
}

public struct DiagnosticsReportSummary: Identifiable, Hashable, Sendable {
    public let id: String
    public let filename: String
    public let playlistName: String
    public let generatedAt: String
    public let added: Int
    public let notFound: Int
    public let skipped: Int
    public let errors: Int

    public init(
        filename: String,
        playlistName: String,
        generatedAt: String,
        added: Int = 0,
        notFound: Int = 0,
        skipped: Int = 0,
        errors: Int = 0
    ) {
        self.id = filename
        self.filename = filename
        self.playlistName = playlistName
        self.generatedAt = generatedAt
        self.added = added
        self.notFound = notFound
        self.skipped = skipped
        self.errors = errors
    }
}

public struct DiagnosticsSummary: Hashable, Sendable {
    public let bridgeStatus: String
    public let platform: String
    public let executionMS: Int
    public let catalogCacheEntries: Int
    public let identityCacheEntries: Int
    public let catalogCacheEnabled: Bool
    public let countryCode: String
    public let activeProviders: [ProviderOption]
    public let recentReports: [DiagnosticsReportSummary]
    public let reportsDirectory: String

    public init(
        bridgeStatus: String,
        platform: String,
        executionMS: Int,
        catalogCacheEntries: Int,
        identityCacheEntries: Int,
        catalogCacheEnabled: Bool,
        countryCode: String,
        activeProviders: [ProviderOption],
        recentReports: [DiagnosticsReportSummary],
        reportsDirectory: String
    ) {
        self.bridgeStatus = bridgeStatus
        self.platform = platform
        self.executionMS = executionMS
        self.catalogCacheEntries = catalogCacheEntries
        self.identityCacheEntries = identityCacheEntries
        self.catalogCacheEnabled = catalogCacheEnabled
        self.countryCode = countryCode
        self.activeProviders = activeProviders
        self.recentReports = recentReports
        self.reportsDirectory = reportsDirectory
    }
}

public struct DiagnosticsSnapshot: Hashable, Sendable {
    public let engineVersion: String
    public let summary: DiagnosticsSummary
    public let events: [DiagnosticEvent]

    public init(engineVersion: String, summary: DiagnosticsSummary, events: [DiagnosticEvent]) {
        self.engineVersion = engineVersion
        self.summary = summary
        self.events = events
    }
}

public protocol DiagnosticsServing: Sendable {
    func fetchDiagnostics() async throws -> DiagnosticsSnapshot
    func listProviders() async throws -> [ProviderOption]
}
