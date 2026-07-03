import XCTest

final class ManualAcquisitionCardGuardTests: XCTestCase {
    func testManualAcquisitionCardSupportsCopyActions() throws {
        let source = try String(
            contentsOf: manualAcquisitionCardSourceURL(),
            encoding: .utf8
        )
        XCTAssertTrue(source.contains("ManualAcquisitionCard"))
        XCTAssertTrue(source.contains("ClipboardSupport.copy"))
        XCTAssertTrue(source.contains("Copier recherche"))
        XCTAssertTrue(source.contains("Ouvrir dans Music"))
        XCTAssertTrue(source.contains("textSelection(.enabled)"))
    }

    func testImportViewModelBatchesProgressMutations() throws {
        let source = try String(
            contentsOf: importViewModelSourceURL(),
            encoding: .utf8
        )
        XCTAssertTrue(source.contains("func mutateProgress"))
        XCTAssertFalse(source.contains("progress.phase = phase\n            progress.currentStep"))
    }

    private func manualAcquisitionCardSourceURL() -> URL {
        sourceRoot().appendingPathComponent("Components/ManualAcquisitionCard.swift")
    }

    private func importViewModelSourceURL() -> URL {
        sourceRoot().appendingPathComponent("ViewModels/ImportViewModel.swift")
    }

    private func sourceRoot() -> URL {
        URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .appendingPathComponent("Sources/ResonanceMac")
    }
}
