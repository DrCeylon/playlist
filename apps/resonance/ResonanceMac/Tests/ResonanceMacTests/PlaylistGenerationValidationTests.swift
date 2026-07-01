import ResonanceCore
import XCTest

final class PlaylistGenerationValidationTests: XCTestCase {
    func testValidRequestPasses() {
        let request = PlaylistGenerationRequest(
            name: "Orlando Pool Party",
            providerID: .appleMusic,
            seeds: [SeedReference(artist: "Kygo", title: "Firestone")],
            targetTrackCount: 50,
            energyCurve: EnergyCurveOption(profile: .rising)
        )
        XCTAssertTrue(PlaylistGenerationValidator.validate(request).isValid)
    }

    func testMissingNameFails() {
        let request = PlaylistGenerationRequest(
            name: "   ",
            providerID: .appleMusic,
            seeds: [SeedReference(artist: "Kygo")],
            targetTrackCount: 50
        )
        let result = PlaylistGenerationValidator.validate(request)
        XCTAssertFalse(result.isValid)
        XCTAssertEqual(result.errors.first?.field, "name")
    }

    func testSeedsOrKeywordsRequired() {
        let request = PlaylistGenerationRequest(
            name: "Test",
            providerID: .appleMusic,
            targetTrackCount: 10
        )
        XCTAssertFalse(PlaylistGenerationValidator.validate(request).isValid)
    }

    func testTargetSizeRequired() {
        let request = PlaylistGenerationRequest(
            name: "Test",
            providerID: .appleMusic,
            seeds: [SeedReference(artist: "Kygo")]
        )
        XCTAssertFalse(PlaylistGenerationValidator.validate(request).isValid)
    }

    func testBridgeDictionaryUsesSnakeCaseKeys() {
        let request = PlaylistGenerationRequest(
            name: "Test",
            providerID: .appleMusic,
            seeds: [SeedReference(artist: "Kygo", title: "Firestone")],
            keywords: ["tropical"],
            targetTrackCount: 12,
            energyCurve: EnergyCurveOption(profile: .rising),
            exclusions: [ExclusionRule(kind: .artist, value: "Pitbull")]
        )
        let payload = BridgeContracts.generationRequestDictionary(request)
        XCTAssertEqual(payload["provider_id"] as? String, "apple_music")
        XCTAssertEqual(payload["target_track_count"] as? Int, 12)
        let seeds = payload["seeds"] as? [[String: Any]]
        XCTAssertEqual(seeds?.first?["artist"] as? String, "Kygo")
    }
}
