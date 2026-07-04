import ResonanceCore
import ResonanceDesign
import SwiftUI

struct HistoryWorkflowResumeView: View {
    enum ResumeContent: Equatable {
        case none
        case preview(PlaylistGenerationResult)
        case importReport(ImportResultState)
        case unavailable(hasRequest: Bool, playlistName: String)
    }

    let detail: SessionHistoryDetail?
    let resumeContent: ResumeContent
    let isBusy: Bool
    let onEditForm: () -> Void
    let onImport: (PlaylistGenerationResult) -> Void
    let onRetryTrack: (Int) -> Void
    let onExport: () -> Void
    @EnvironmentObject private var themeManager: ThemeManager

    var body: some View {
        let palette = ThemePalette(theme: themeManager.active)

        BoundedScrollScreen {
            VStack(alignment: .leading, spacing: 16) {
                header(palette: palette)

                switch resumeContent {
                case .none:
                    Text("Sélectionne une session pour reprendre le workflow.")
                        .foregroundStyle(palette.textSecondary)
                case .preview(let result):
                    PlaylistPreviewView(
                        result: result,
                        previewSourceLabel: "Session enregistrée",
                        actionsDisabled: isBusy,
                        onEdit: onEditForm,
                        onImport: { onImport(result) }
                    )
                case .importReport(let report):
                    ImportReportView(
                        report: report,
                        showsDismissButton: false,
                        onRetryTrack: { index in onRetryTrack(index) },
                        onClose: {}
                    )
                case .unavailable(let hasRequest, let playlistName):
                    unavailablePanel(
                        playlistName: playlistName,
                        hasRequest: hasRequest,
                        palette: palette
                    )
                }

                if ResonanceFeatureFlags.architectModeEnabled, let detail {
                    architectSection(for: detail, palette: palette)
                }
            }
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .topLeading)
        }
        .themedSurfaceCard(fill: palette.surface, border: palette.borderSubtle)
    }

    @ViewBuilder
    private func header(palette: ThemePalette) -> some View {
        if let detail {
            VStack(alignment: .leading, spacing: 8) {
                Text("Reprendre le workflow")
                    .font(.headline)
                    .foregroundStyle(palette.textPrimary)
                Text(detail.summary.playlistName)
                    .font(.title3.weight(.semibold))
                    .foregroundStyle(palette.textPrimary)
                Text(SessionHistoryDisplay.statusLabel(for: detail.summary.status))
                    .font(.caption.weight(.semibold))
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(statusTint(for: detail.summary.status, palette: palette).opacity(0.15))
                    .foregroundStyle(statusTint(for: detail.summary.status, palette: palette))
                    .clipShape(Capsule())
                Text(SessionHistoryDisplay.rowSubtitle(for: detail.summary))
                    .font(.callout)
                    .foregroundStyle(palette.textSecondary)
            }
        }
    }

    @ViewBuilder
    private func unavailablePanel(
        playlistName: String,
        hasRequest: Bool,
        palette: ThemePalette
    ) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Aperçu indisponible", systemImage: "music.note.list")
                .font(.headline)
                .foregroundStyle(palette.statusWarning)
            Text("La session «\(playlistName)» n'a pas d'aperçu enregistré exploitable.")
                .foregroundStyle(palette.textSecondary)
            if hasRequest {
                Button("Modifier le formulaire", action: onEditForm)
                    .buttonStyle(.borderedProminent)
                    .tint(palette.accentPrimary)
                    .disabled(isBusy)
                    .opacity(isBusy ? 0.55 : 1)
            } else {
                Text("La requête originale n'est pas disponible pour cette session.")
                    .font(.caption)
                    .foregroundStyle(palette.textTertiary)
            }
        }
        .padding(16)
        .background(palette.backgroundSecondary)
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    @ViewBuilder
    private func architectSection(for detail: SessionHistoryDetail, palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Diagnostic")
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(palette.textSecondary)

            VStack(alignment: .leading, spacing: 4) {
                Text("Requête : \(detail.generationRequest.isEmpty ? "indisponible" : "enregistrée")")
                Text("Aperçu : \(detail.generationResult.isEmpty ? "indisponible" : "enregistré")")
                Text("Import : \(detail.importResult.isEmpty ? "non exécuté" : "rapport enregistré")")
                if !detail.summary.jsonReportPath.isEmpty {
                    Text("Rapport JSON : \(detail.summary.jsonReportPath)")
                } else if !detail.summary.textReportPath.isEmpty {
                    Text("Rapport texte : \(detail.summary.textReportPath)")
                }
            }
            .font(.caption)
            .foregroundStyle(palette.textTertiary)
            .textSelection(.enabled)

            Button("Exporter le rapport", action: onExport)
                .buttonStyle(.bordered)
                .disabled(isBusy)
                .opacity(isBusy ? 0.55 : 1)
        }
        .padding(.top, 8)
    }

    private func statusTint(for status: SessionHistoryStatus, palette: ThemePalette) -> Color {
        switch status {
        case .generated: return palette.accentPrimary
        case .imported: return palette.statusSuccess
        case .partialSuccess, .waitingForManualAcquisition: return palette.statusWarning
        case .failed: return palette.statusError
        }
    }
}
