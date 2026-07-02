import ResonanceCore
@testable import ResonanceMac
import XCTest

final class ImportReportPartialSuccessTests: XCTestCase {
    func testPartialSuccessReportExposesNonAddedTracks() {
        let report = ImportResultState(
            playlistName: "Demo",
            outcomes: [
                ImportTrackOutcome(artist: "Kygo", title: "Firestone", section: "Main", status: .added),
                ImportTrackOutcome(artist: "A", title: "B", section: "Main", status: .notFound, message: "Introuvable"),
                ImportTrackOutcome(artist: "C", title: "D", section: "Main", status: .skipped, message: "Déjà présent"),
            ],
            phase: .partialSuccess
        )

        XCTAssertEqual(report.addedCount, 1)
        XCTAssertEqual(report.notFoundCount, 1)
        XCTAssertEqual(report.skippedCount, 1)
        XCTAssertEqual(report.outcomes.filter { $0.status != .added }.count, 2)
    }
}

final class HistoryPayloadMapperTests: XCTestCase {
    func testGenerationResultFromStoredHistoryPayload() throws {
        let payload: BridgeJSONObject = [
            "playlist_name": .string("Demo"),
            "sections": .array([
                .object([
                    "name": .string("Main"),
                    "tracks": .array([
                        .object([
                            "artist": .string("Kygo"),
                            "title": .string("Firestone"),
                            "section": .string("Main"),
                            "score": .number(0.9),
                            "confidence": .string("high"),
                            "source": .string("seed"),
                        ]),
                    ]),
                ]),
            ]),
            "average_score": .number(0.9),
            "provider_id": .string("apple_music"),
        ]
        let result = try HistoryPayloadMapper.generationResult(from: payload)
        XCTAssertEqual(result.playlistName, "Demo")
        XCTAssertEqual(result.trackCount, 1)
    }
}
