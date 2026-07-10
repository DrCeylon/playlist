import ResonanceCore
import ResonanceDesign
import SwiftUI

struct HistoryView: View {
    @StateObject private var viewModel: HistoryViewModel
    @Binding var selection: SidebarItem?
    @EnvironmentObject private var themeManager: ThemeManager
    @EnvironmentObject private var workflow: AppWorkflowCoordinator
    @State private var showClearConfirmation = false

    init(
        selection: Binding<SidebarItem?>,
        bridgeService: PythonEngineBridgeService = PythonEngineBridgeService()
    ) {
        _selection = selection
        _viewModel = StateObject(
            wrappedValue: HistoryViewModel(
                service: bridgeService,
                importService: bridgeService
            )
        )
    }

    var body: some View {
        ThemedScreen {
            let palette = ThemePalette(theme: themeManager.active)
            VStack(alignment: .leading, spacing: 16) {
                header(palette: palette)
                actionFeedbackBanner(palette: palette)
                content(palette: palette)
            }
            .padding(24)
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        }
        .navigationTitle("Historique")
        .task {
            await viewModel.refresh()
        }
        .confirmationDialog(
            clearHistoryDialogTitle,
            isPresented: $showClearConfirmation,
            titleVisibility: .visible
        ) {
            Button(clearHistoryConfirmLabel, role: .destructive) {
                Task {
                    await viewModel.clearAll(preservingSessionID: workflow.activeHistorySessionID)
                }
            }
            Button("Annuler", role: .cancel) {}
        } message: {
            Text(clearHistoryDialogMessage)
        }
    }

    private var clearHistoryDialogTitle: String {
        workflow.isProcessRunning ? "Vider l'historique (session active conservée) ?" : "Vider tout l'historique ?"
    }

    private var clearHistoryConfirmLabel: String {
        workflow.isProcessRunning ? "Vider les autres sessions" : "Vider l'historique"
    }

    private var clearHistoryDialogMessage: String {
        if workflow.isProcessRunning {
            return "Un processus est en cours. Seules les autres sessions seront supprimées — la session active restera visible jusqu'à la fin du workflow."
        }
        return "Cette action supprime toutes les sessions locales enregistrées par Resonance."
    }

    private func header(palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text("Sessions locales")
                    .font(.title2.weight(.semibold))
                    .foregroundStyle(palette.textPrimary)
                Spacer()
                Button("Vider") { showClearConfirmation = true }
                    .buttonStyle(.bordered)
                    .disabled(viewModel.isBusy)
                    .opacity(viewModel.isBusy ? 0.55 : 1)
                if workflow.isProcessRunning {
                    Text("Processus en cours — la session active sera conservée")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(palette.statusWarning)
                }
                Button("Rafraîchir") { Task { await viewModel.refresh() } }
                    .buttonStyle(.borderedProminent)
                    .tint(palette.accentPrimary)
                    .disabled(viewModel.isBusy)
                    .opacity(viewModel.isBusy ? 0.55 : 1)
            }
            Text("Retrouve tes playlists et reprends le workflow là où tu t'étais arrêté.")
                .font(.callout)
                .foregroundStyle(palette.textSecondary)
        }
    }

    @ViewBuilder
    private func actionFeedbackBanner(palette: ThemePalette) -> some View {
        switch viewModel.actionFeedback {
        case .none:
            EmptyView()
        case .inProgress(let message):
            HStack(spacing: 8) {
                ProgressView().controlSize(.small)
                Text(message)
            }
            .font(.callout)
            .foregroundStyle(palette.textSecondary)
            .padding(10)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(palette.backgroundSecondary)
            .clipShape(RoundedRectangle(cornerRadius: 10))
        case .success(let message):
            Label(message, systemImage: "checkmark.circle")
                .font(.callout)
                .foregroundStyle(palette.statusSuccess)
                .padding(10)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(palette.backgroundSecondary)
                .clipShape(RoundedRectangle(cornerRadius: 10))
        case .failure(let message):
            Label(message, systemImage: "exclamationmark.triangle")
                .font(.callout)
                .foregroundStyle(palette.statusWarning)
                .padding(10)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(palette.backgroundSecondary)
                .clipShape(RoundedRectangle(cornerRadius: 10))
        }
    }

    @ViewBuilder
    private func content(palette: ThemePalette) -> some View {
        switch viewModel.screenState {
        case .idle, .loading:
            ProgressView("Chargement de l'historique…")
                .foregroundStyle(palette.textSecondary)
        case .failed(let message):
            Text(message).foregroundStyle(palette.statusWarning)
        case .ready:
            if viewModel.sessions.isEmpty {
                Text("Aucune session pour le moment. Génère une playlist pour commencer.")
                    .foregroundStyle(palette.textSecondary)
            } else {
                HStack(alignment: .top, spacing: 16) {
                    List(viewModel.sessions) { session in
                        sessionRow(session: session, palette: palette)
                            .listRowBackground(palette.surface)
                            .listRowSeparatorTint(palette.borderSubtle)
                            .onTapGesture { Task { await viewModel.select(session: session) } }
                            .contextMenu {
                                Button("Supprimer") {
                                    Task {
                                        await viewModel.delete(
                                            session: session,
                                            isProtected: workflow.isProtectedHistorySession
                                        )
                                    }
                                }
                                .disabled(workflow.isProtectedHistorySession(session))
                            }
                    }
                    .listStyle(.inset(alternatesRowBackgrounds: false))
                    .scrollContentBackground(.hidden)
                    .background(palette.backgroundPrimary)
                    .frame(minWidth: 360)
                    .focusEffectDisabled()

                    HistoryWorkflowResumeView(
                        detail: viewModel.selectedDetail,
                        resumeContent: viewModel.resumeContent,
                        isBusy: historyActionsDisabled,
                        actionsDisabledReason: historyActionsDisabledReason,
                        onEditForm: {
                            if let request = viewModel.editRequestForSelectedSession() {
                                workflow.requestEditFromHistory(request)
                                selection = workflow.activeRoute
                            }
                        },
                        onImport: { result in
                            Task {
                                await workflow.startImport(from: result)
                                selection = workflow.activeRoute
                            }
                        },
                        onRetryTrack: { index in
                            Task { await viewModel.retryImportTrack(at: index) }
                        },
                        onRetryImport: { result in
                            Task {
                                await workflow.startImport(from: result)
                                selection = workflow.activeRoute
                            }
                        },
                        onExport: {
                            Task { await viewModel.exportSelection() }
                        },
                        onConfirmManual: {
                            Task { await workflow.importWorkflow.confirmManualAcquisition() }
                        },
                        onResumeManualImport: {
                            if let detail = viewModel.selectedDetail {
                                workflow.resumeManualImportFromHistory(detail: detail)
                                selection = workflow.activeRoute
                            }
                        },
                        onDismissLiveImport: {
                            workflow.importWorkflow.reset()
                        },
                        onOpenNewPlaylist: {
                            workflow.activeRoute = .newPlaylist
                            selection = .newPlaylist
                        }
                    )
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
                }
                .frame(maxHeight: .infinity)
            }
        }
    }

    private func sessionRow(session: SessionHistorySummary, palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(session.playlistName)
                .font(.headline)
                .foregroundStyle(palette.textPrimary)
            Text("\(session.startedAtISO) · \(PlaylistLibraryDisplay.providerLabel(session.providerID))")
                .font(.caption)
                .foregroundStyle(palette.textTertiary)
            Text(SessionHistoryDisplay.statusLabel(for: session.status))
                .font(.caption.weight(.medium))
                .foregroundStyle(statusColor(for: session.status, palette: palette))
            Text(SessionHistoryDisplay.rowSubtitle(for: session))
                .font(.caption2)
                .foregroundStyle(palette.textSecondary)
        }
        .contentShape(Rectangle())
    }

    private var isManagingSelectedSession: Bool {
        guard let detail = viewModel.selectedDetail else { return false }
        return workflow.isManagingSession(detail)
    }

    private var historyActionsDisabled: Bool {
        if viewModel.isBusy { return true }
        if workflow.canStartProcess() { return false }
        return !isManagingSelectedSession
    }

    private var historyActionsDisabledReason: String? {
        if viewModel.isBusy { return nil }
        if workflow.canStartProcess() { return nil }
        if isManagingSelectedSession { return nil }
        return workflow.processBlockingLabel
    }

    private func statusColor(for status: SessionHistoryStatus, palette: ThemePalette) -> Color {
        switch status {
        case .generated: return palette.accentPrimary
        case .imported: return palette.statusSuccess
        case .partialSuccess, .waitingForManualAcquisition: return palette.statusWarning
        case .failed: return palette.statusError
        }
    }
}
