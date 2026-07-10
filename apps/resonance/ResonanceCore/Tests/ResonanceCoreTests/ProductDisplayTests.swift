import ResonanceCore
import XCTest

final class ProductDisplayTests: XCTestCase {
    func testMappingStatusLabelsAreHumanReadable() {
        XCTAssertEqual(ProductDisplay.mappingStatusLabel(.matched), "Correspondance trouvée")
        XCTAssertFalse(ProductDisplay.mappingStatusLabel(.unresolved).contains("_"))
    }

    func testConflictKindLabelsHideTechnicalIDs() {
        XCTAssertEqual(ProductDisplay.conflictKindLabel("metadata_mismatch"), "Informations différentes")
        XCTAssertEqual(ProductDisplay.resolutionStrategyLabel("keep_local"), "Garder la version locale")
    }

    func testProviderCapabilityLabelsAreFrench() {
        XCTAssertEqual(ProductDisplay.providerCapabilityLabel(.playlistSync), "Synchronisation")
        XCTAssertEqual(ProductDisplay.providerCapabilityLabel(.authentication), "Connexion de compte")
    }
}
