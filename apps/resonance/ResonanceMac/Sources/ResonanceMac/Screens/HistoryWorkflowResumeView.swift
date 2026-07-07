import ResonanceCore
import ResonanceDesign
import SwiftUI

struct HistoryWorkflowResumeView: View {
    enum ResumeContent: Equatable {
        case none
        case preview(PlaylistGenerationResult)
        case importReport(ImportResultState)
        case manualAcquisitionWaiting(ImportResultState)
        case manualAcquisitionUnavailable(ImportResultState, hasRequest: Bool, playlistName: String)
        case liveImport
        case liveGeneration(playlistName: String)
        case liveImportFailed(message: String)
        case unavailable(hasRequest: Bool, playlistName: String)
    }

    let detail: SessionHistoryDetail?
    let resumeContent: ResumeContent
    let isBusy: Bool
    let actionsDisabledReason: String?
    let onEditForm: () -> Void
    let onImport: (PlaylistGenerationResult) -> Void
    let onRetryTrack: (Int) -> Void
    let onRetryImport: (PlaylistGenerationResult) -> Void
    let onExport: () -> Void
    let onConfirmManual: () -> Void
    let onResumeManualImport: () -> Void
    let onDismissLiveImport: () -> Void
    let onOpenNewPlaylist: () -> Void
    @EnvironmentObject private var themeManager: ThemeManager
    @EnvironmentObject private var workflow: AppWorkflowCoordinator

    var body: some View {
        let palette = ThemePalette(theme: themeManager.active)

        BoundedScrollScreen {
            VStack(alignment: .leading, spacing: 16) {
                header(palette: palette)

                switch effectiveContent {
                case .none:
                    Text("Sélectionne une session pour reprendre le workflow.")
                        .foregroundStyle(palette.textSecondary)
                case .preview(let result):
                    PlaylistPreviewView(
                        result: result,
                        previewSourceLabel: "Session enregistrée",
                        actionsDisabled: isBusy,
                        actionsDisabledReason: actionsDisabledReason,
                        onEdit: onEditForm,
                        onImport: { onImport(result) }
                    )
                case .importReport(let report):
                    ImportReportView(
                        report: report,
                        showsDismissButton: false,
                        actionsDisabled: isBusy,
                        actionsDisabledReason: actionsDisabledReason,
                        onRetryTrack: { index in onRetryTrack(index) },
                        onClose: {}
                    )
                case .manualAcquisitionWaiting(let report):
                    manualAcquisitionResumePanel(report: report, palette: palette)
                case .manualAcquisitionUnavailable(let report, let hasRequest, let playlistName):
                    manualAcquisitionUnavailablePanel(
                        report: report,
                        hasRequest: hasRequest,
                        playlistName: playlistName,
                        palette: palette
                    )
                case .liveImport:
                    ImportProgressView(
                        progress: workflow.importWorkflow.progress,
                        manualPrompt: workflow.importWorkflow.manualPrompt,
                        manualPollStatus: workflow.importWorkflow.manualPollStatus,
                        manualAcquisitionStatus: workflow.importWorkflow.manualAcquisitionStatus,
                        architectErrorDetail: workflow.importWorkflow.architectErrorDetail,
                        architectManualDiagnostics: workflow.importWorkflow.architectManualDiagnostics,
                        isContinueInProgress: workflow.importWorkflow.isContinuingManual,
                        embeddedInPanel: true,
                        onConfirmManual: onConfirmManual
                    )
                case .liveGeneration(let playlistName):
                    liveGenerationPanel(playlistName: playlistName, palette: palette)
                case .liveImportFailed(let message):
                    liveFailurePanel(message: message, palette: palette)
                case .unavailable(let hasRequest, let playlistName):
                    unavailablePanel(
                        playlistName: playlistName,
                        hasRequest: hasRequest,
                        status: detail?.summary.status,
                        palette: palette
                    )
                }

                if actionsDisabledReason != nil, !isLiveWorkflowContent {
                    processBlockingNote(palette: palette)
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

    private var effectiveContent: ResumeContent {
        guard let detail else { return resumeContent }
        guard workflow.isManagingSession(detail) else { return resumeContent }

        switch workflow.importWorkflow.screenState {
        case .importing, .waitingForManualAcquisition:
            return .liveImport
        case .report:
            if let report = workflow.importWorkflow.report {
                return .importReport(report)
            }
        case .failed(let message):
            return .liveImportFailed(message: message)
        case .idle:
            break
        }

        if workflow.playlistBuilder.screenState == .generating {
            let name = workflow.playlistBuilder.previewResult?.playlistName
                ?? workflow.playlistBuilder.name
            return .liveGeneration(playlistName: name.isEmpty ? detail.summary.playlistName : name)
        }

        if workflow.playlistBuilder.screenState == .preview,
           let preview = workflow.playlistBuilder.previewResult {
            return .preview(preview)
        }

        return resumeContent
    }

    private var isLiveWorkflowContent: Bool {
        switch effectiveContent {
        case .liveImport, .liveGeneration, .liveImportFailed:
            return true
        default:
            return false
        }
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
    private func processBlockingNote(palette: ThemePalette) -> some View {
        if let actionsDisabledReason {
            Label(actionsDisabledReason, systemImage: "hourglass")
                .font(.caption.weight(.semibold))
                .foregroundStyle(palette.statusWarning)
                .padding(10)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(palette.statusWarning.opacity(0.12))
                .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
        }
    }

    @ViewBuilder
    private func liveGenerationPanel(playlistName: String, palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Génération en cours", systemImage: "sparkles")
                .font(.headline)
                .foregroundStyle(palette.statusInfo)
            Text("«\(playlistName)» est en cours de composition par le moteur Python.")
                .foregroundStyle(palette.textSecondary)
            HStack(spacing: 8) {
                ProgressView()
                Text("Processus en cours — suis l'avancement via le bandeau global.")
                    .font(.caption)
                    .foregroundStyle(palette.textSecondary)
            }
        }
        .padding(16)
        .background(palette.backgroundSecondary)
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    @ViewBuilder
    private func liveFailurePanel(message: String, palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            Label("Import interrompu", systemImage: "exclamationmark.triangle")
                .font(.headline)
                .foregroundStyle(palette.statusWarning)
            Text(message)
                .foregroundStyle(palette.textPrimary)
                .textSelection(.enabled)

            if let generation = generationResultForDetail() {
                Button {
                    onRetryImport(generation)
                } label: {
                    Label("Relancer l'import", systemImage: "arrow.clockwise")
                }
                .buttonStyle(.borderedProminent)
                .tint(palette.accentPrimary)
                .disabled(isBusy)
                .opacity(isBusy ? 0.55 : 1)
            }

            Button("Modifier le formulaire", action: onEditForm)
                .buttonStyle(.bordered)
                .disabled(isBusy)
                .opacity(isBusy ? 0.55 : 1)

            Button("Fermer le rapport d'échec") {
                onDismissLiveImport()
            }
            .buttonStyle(.borderless)
            .foregroundStyle(palette.textSecondary)
        }
        .padding(16)
        .background(palette.backgroundSecondary)
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    @ViewBuilder
    private func unavailablePanel(
        playlistName: String,
        hasRequest: Bool,
        status: SessionHistoryStatus?,
        palette: ThemePalette
    ) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Aperçu indisponible", systemImage: "music.note.list")
                .font(.headline)
                .foregroundStyle(palette.statusWarning)
            Text(unavailableReason(for: status, playlistName: playlistName))
                .foregroundStyle(palette.textSecondary)
            if hasRequest {
                Button("Modifier le formulaire", action: onEditForm)
                    .buttonStyle(.borderedProminent)
                    .tint(palette.accentPrimary)
                    .disabled(isBusy)
                    .opacity(isBusy ? 0.55 : 1)
            } else {
                Button("Ouvrir Nouvelle Playlist", action: onOpenNewPlaylist)
                    .buttonStyle(.borderedProminent)
                    .tint(palette.accentPrimary)
                    .disabled(isBusy)
                    .opacity(isBusy ? 0.55 : 1)
                Text("La requête originale n'est pas disponible — recréez la playlist manuellement.")
                    .font(.caption)
                    .foregroundStyle(palette.textSecondary)
            }
        }
        .padding(16)
        .background(palette.backgroundSecondary)
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    private func unavailableReason(for status: SessionHistoryStatus?, playlistName: String) -> String {
        let statusLabel = status.map { SessionHistoryDisplay.statusLabel(for: $0) } ?? "inconnue"
        return "La session «\(playlistName)» (\(statusLabel)) n'a pas d'aperçu enregistré exploitable pour reprendre directement l'import ou la génération."
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
            .foregroundStyle(palette.textSecondary)
            .textSelection(.enabled)

            Button("Exporter le rapport", action: onExport)
                .buttonStyle(.bordered)
                .disabled(isBusy)
                .opacity(isBusy ? 0.55 : 1)
        }
        .padding(.top, 8)
    }

    private func generationResultForDetail() -> PlaylistGenerationResult? {
        guard let detail else { return nil }
        guard !detail.generationResult.isEmpty else { return nil }
        return try? HistoryPayloadMapper.generationResult(from: detail.generationResult)
    }

    @ViewBuilder
    private func manualAcquisitionResumePanel(report: ImportResultState, palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            Label("Ajout manuel en attente", systemImage: "hand.raised")
                .font(.headline)
                .foregroundStyle(palette.statusWarning)

            if let prompt = report.manualPrompt {
                ManualAcquisitionCard(
                    prompt: prompt,
                    trackPositionLabel: report.outcomes.first.map { $0.searchLine },
                    status: ManualAcquisitionUIStatus(),
                    isContinueInProgress: isBusy,
                    architectDiagnostics: nil,
                    palette: palette,
                    onConfirmManual: onResumeManualImport
                )
            } else if let outcome = report.outcomes.first {
                CopyableField(label: "Morceau", value: outcome.searchLine, palette: palette)
                SelectableText(
                    text: outcome.message,
                    font: .callout,
                    foreground: palette.textSecondary
                )
            }

            Button {
                onResumeManualImport()
            } label: {
                Label("Reprendre l'ajout manuel", systemImage: "play.fill")
            }
            .buttonStyle(.borderedProminent)
            .tint(palette.accentPrimary)
            .disabled(isBusy)
            .opacity(isBusy ? 0.55 : 1)

            Text("Cette action rouvre le workflow d'import actif — identique à Nouvelle Playlist.")
                .font(.caption)
                .foregroundStyle(palette.textSecondary)
        }
        .padding(16)
        .background(palette.backgroundSecondary)
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    @ViewBuilder
    private func manualAcquisitionUnavailablePanel(
        report: ImportResultState,
        hasRequest: Bool,
        playlistName: String,
        palette: ThemePalette
    ) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Reprise indisponible", systemImage: "exclamationmark.triangle")
                .font(.headline)
                .foregroundStyle(palette.statusWarning)
            Text(
                "La session «\(playlistName)» nécessite un ajout manuel, mais le checkpoint d'import n'est plus disponible."
            )
            .foregroundStyle(palette.textSecondary)

            if let outcome = report.outcomes.first {
                CopyableField(label: "Morceau", value: outcome.searchLine, palette: palette)
            }

            if hasRequest {
                Button("Modifier le formulaire", action: onEditForm)
                    .buttonStyle(.borderedProminent)
                    .tint(palette.accentPrimary)
                    .disabled(isBusy)
            } else if let generation = generationResultForDetail() {
                Button {
                    onRetryImport(generation)
                } label: {
                    Label("Réessayer l'import", systemImage: "arrow.clockwise")
                }
                .buttonStyle(.borderedProminent)
                .tint(palette.accentPrimary)
                .disabled(isBusy)
            } else {
                Button("Ouvrir Nouvelle Playlist", action: onOpenNewPlaylist)
                    .buttonStyle(.borderedProminent)
                    .tint(palette.accentPrimary)
                    .disabled(isBusy)
            }
        }
        .padding(16)
        .background(palette.backgroundSecondary)
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
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
