@testable import ResonanceMac
import XCTest

final class TrackConfidenceDisplayTests: XCTestCase {
    func testHighConfidenceLabel() {
        XCTAssertEqual(TrackConfidenceDisplay.label(for: 0.92), "Confiance élevée")
        XCTAssertEqual(TrackConfidenceDisplay.label(for: 95), "Confiance élevée")
    }

    func testMediumConfidenceLabel() {
        XCTAssertEqual(TrackConfidenceDisplay.label(for: 0.65), "Confiance moyenne")
    }

    func testLowConfidenceLabel() {
        XCTAssertEqual(TrackConfidenceDisplay.label(for: 0.24), "Faible confiance")
    }
}
