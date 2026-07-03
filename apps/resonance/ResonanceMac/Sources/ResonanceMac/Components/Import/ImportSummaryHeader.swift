import ResonanceCore
import ResonanceDesign
import SwiftUI

struct ImportSummaryHeader: View {
    let report: ImportResultState
    let palette: ThemePalette

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            if report.addedCount > 0 {
                summaryLine(
                    icon: "checkmark.circle.fill",
                    text: "\(report.addedCount) morceau\(report.addedCount > 1 ? "x" : "") importé\(report.addedCount > 1 ? "s" : "")",
                    color: palette.statusSuccess
                )
            }
            if manualActionCount > 0 {
                summaryLine(
                    icon: "exclamationmark.triangle.fill",
                    text: "\(manualActionCount) nécessite\(manualActionCount > 1 ? "nt" : "") une action",
                    color: palette.statusWarning
                )
            }
            if report.notFoundCount > 0 {
                summaryLine(
                    icon: "questionmark.circle.fill",
                    text: "\(report.notFoundCount) introuvable\(report.notFoundCount > 1 ? "s" : "")",
                    color: palette.statusWarning
                )
            }
            if report.errorCount > 0 {
                summaryLine(
                    icon: "xmark.octagon.fill",
                    text: "\(report.errorCount) erreur\(report.errorCount > 1 ? "s" : "")",
                    color: palette.statusWarning
                )
            }
            if report.skippedCount > 0 {
                summaryLine(
                    icon: "arrow.uturn.right.circle.fill",
                    text: "\(report.skippedCount) déjà présent\(report.skippedCount > 1 ? "s" : "")",
                    color: palette.textSecondary
                )
            }
        }
    }

    private var manualActionCount: Int {
        report.outcomes.filter { $0.status == .acquiring || $0.status == .notFound || $0.status == .error }.count
    }

    private func summaryLine(icon: String, text: String, color: Color) -> some View {
        HStack(spacing: 8) {
            Image(systemName: icon)
                .foregroundStyle(color)
            SelectableText(text: text, font: .callout.weight(.medium), foreground: palette.textPrimary)
        }
    }
}
