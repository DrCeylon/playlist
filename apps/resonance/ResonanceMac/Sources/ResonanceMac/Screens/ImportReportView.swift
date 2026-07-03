import ResonanceCore
import ResonanceDesign
import SwiftUI

struct ImportReportView: View {
    let report: ImportResultState
    let onClose: () -> Void
    @EnvironmentObject private var themeManager: ThemeManager

    var body: some View {
        let palette = ThemePalette(theme: themeManager.active)

        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Rapport d'import")
                        .font(.title2.weight(.semibold))
                    SelectableText(
                        text: report.playlistName,
                        font: .headline,
                        foreground: palette.textSecondary
                    )
                    ImportSummaryHeader(report: report, palette: palette)
                }

                ImportMetricsRow(
                    resolved: nil,
                    resolvedTotal: nil,
                    added: report.addedCount,
                    skipped: report.skippedCount,
                    notFound: report.notFoundCount,
                    errors: report.errorCount,
                    palette: palette
                )

                if !report.outcomes.isEmpty {
                    VStack(alignment: .leading, spacing: 10) {
                        Text("Détail")
                            .font(.headline)
                        ForEach(report.outcomes) { outcome in
                            ImportOutcomeRow(outcome: outcome, palette: palette)
                        }
                    }
                }

                HStack(spacing: 10) {
                    Button("Ouvrir Music.app") {
                        MusicAppLink.openApp()
                    }
                    .buttonStyle(.bordered)

                    Button("Fermer", action: onClose)
                        .buttonStyle(.borderedProminent)
                        .tint(palette.accentPrimary)
                }
            }
            .padding(24)
        }
    }
}
