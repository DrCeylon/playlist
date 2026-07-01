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
                    Text(report.playlistName)
                        .font(.headline)
                        .foregroundStyle(palette.textSecondary)
                    Text(laboratorySummary)
                        .font(.callout)
                        .foregroundStyle(palette.textPrimary)
                }

                metricsRow(palette: palette)

                if !report.outcomes.isEmpty {
                    VStack(alignment: .leading, spacing: 10) {
                        Text("Détail")
                            .font(.headline)
                        ForEach(report.outcomes) { outcome in
                            HStack(alignment: .top) {
                                Image(systemName: icon(for: outcome.status))
                                    .foregroundStyle(color(for: outcome.status, palette: palette))
                                VStack(alignment: .leading, spacing: 2) {
                                    Text("\(outcome.title) — \(outcome.artist)")
                                        .font(.body)
                                    Text(statusLabel(outcome.status))
                                        .font(.caption)
                                        .foregroundStyle(palette.textSecondary)
                                    if !outcome.message.isEmpty {
                                        Text(outcome.message)
                                            .font(.caption2)
                                            .foregroundStyle(palette.textTertiary)
                                    }
                                }
                                Spacer()
                            }
                        }
                    }
                }

                Button("Fermer", action: onClose)
                    .buttonStyle(.borderedProminent)
                    .tint(palette.accentPrimary)
            }
            .padding(24)
        }
    }

    private var laboratorySummary: String {
        switch report.phase {
        case .completed:
            return "Transfert terminé. Le laboratoire confirme une playlist stable."
        case .partialSuccess:
            return "Transfert partiel. Certains morceaux ont résisté à l'expérience."
        case .waitingForManualAcquisition:
            return "Pause scientifique : ajout manuel requis dans Music.app."
        case .failed:
            return "L'expérience a échoué. Aucun morceau n'a été livré."
        default:
            return "Rapport d'import Resonance."
        }
    }

    @ViewBuilder
    private func metricsRow(palette: ThemePalette) -> some View {
        HStack(spacing: 12) {
            metricCard("Ajoutés", value: report.addedCount, palette: palette)
            metricCard("Ignorés", value: report.skippedCount, palette: palette)
            metricCard("Introuvables", value: report.notFoundCount, palette: palette)
            metricCard("Erreurs", value: report.errorCount, palette: palette)
        }
    }

    private func metricCard(_ title: String, value: Int, palette: ThemePalette) -> some View {
        VStack(spacing: 4) {
            Text("\(value)")
                .font(.title3.monospacedDigit().weight(.semibold))
            Text(title)
                .font(.caption2)
                .foregroundStyle(palette.textSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(10)
        .background(palette.backgroundSecondary)
        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
    }

    private func icon(for status: ImportTrackStatus) -> String {
        switch status {
        case .added: return "checkmark.circle.fill"
        case .skipped: return "arrow.uturn.right.circle"
        case .notFound: return "questionmark.circle"
        case .error: return "xmark.octagon.fill"
        case .acquiring: return "arrow.down.circle"
        default: return "circle"
        }
    }

    private func color(for status: ImportTrackStatus, palette: ThemePalette) -> Color {
        switch status {
        case .added: return palette.statusSuccess
        case .skipped: return palette.textSecondary
        case .notFound: return palette.statusWarning
        case .error: return palette.statusWarning
        case .acquiring: return palette.accentPrimary
        default: return palette.textTertiary
        }
    }

    private func statusLabel(_ status: ImportTrackStatus) -> String {
        switch status {
        case .added: return "Ajouté"
        case .skipped: return "Déjà présent"
        case .notFound: return "Non trouvé"
        case .error: return "Erreur"
        case .acquiring: return "Acquisition requise"
        case .pending: return "En attente"
        }
    }
}
