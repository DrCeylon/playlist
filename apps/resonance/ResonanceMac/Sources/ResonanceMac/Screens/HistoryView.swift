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
        service: any SessionHistoryServing = PythonEngineBridgeService()
    ) {
        _selection = selection
        _viewModel = StateObject(wrappedValue: HistoryViewModel(service: service))
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
        }
        .navigationTitle("Historique")
        .task {
            await viewModel.refresh()
        }
        .confirmationDialog(
            "Vider tout l'historique ?",
            isPresented: $showClearConfirmation,
            titleVisibility: .visible
        ) {
            Button("Vider l'historique", role: .destructive) {
                Task { await viewModel.clearAll() }
            }
            Button("Annuler", role: .cancel) {}
        } message: {
            Text("Cette action supprime toutes les sessions locales enregistrées par Resonance.")
        }
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
                                Button("Supprimer") { Task { await viewModel.delete(session: session) } }
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
                        isBusy: viewModel.isBusy || !workflow.canStartProcess(),
                        onEditForm: {
                            if let request = viewModel.editRequestForSelectedSession() {
                                workflow.requestEditFromHistory(request, selection: $selection)
                            }
                        },
                        onImport: { result in
                            Task {
                                await workflow.startImport(
                                    from: result,
                                    selection: $selection
                                )
                            }
                        },
                        onRetryTrack: { index in
                            Task { await viewModel.retryImportTrack(at: index) }
                        },
                        onExport: {
                            Task { await viewModel.exportSelection() }
                        }
                    )
                }
            }
        }
    }

    private func sessionRow(session: SessionHistorySummary, palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(session.playlistName)
                .font(.headline)
                .foregroundStyle(palette.textPrimary)
            Text("\(session.startedAtISO) · \(session.providerID.rawValue)")
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

    private func statusColor(for status: SessionHistoryStatus, palette: ThemePalette) -> Color {
        switch status {
        case .generated: return palette.accentPrimary
        case .imported: return palette.statusSuccess
        case .partialSuccess, .waitingForManualAcquisition: return palette.statusWarning
        case .failed: return palette.statusError
        }
    }
}
