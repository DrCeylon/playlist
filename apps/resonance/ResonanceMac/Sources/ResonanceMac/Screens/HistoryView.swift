import ResonanceCore
import ResonanceDesign
import SwiftUI

struct HistoryView: View {
    @StateObject private var viewModel: HistoryViewModel
    @EnvironmentObject private var themeManager: ThemeManager
    @State private var showClearConfirmation = false

    init(service: any SessionHistoryServing = PythonEngineBridgeService()) {
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
        HStack {
            Text("Sessions locales")
                .font(.title2.weight(.semibold))
                .foregroundStyle(palette.textPrimary)
            Spacer()
            Button("Vider") { showClearConfirmation = true }
                .buttonStyle(.bordered)
                .disabled(viewModel.isBusy)
            Button("Rafraîchir") { Task { await viewModel.refresh() } }
                .buttonStyle(.borderedProminent)
                .tint(palette.accentPrimary)
                .disabled(viewModel.isBusy)
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
                Text("Aucune session pour le moment.")
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

                    SessionDetailView(
                        detail: viewModel.selectedDetail,
                        canReplay: viewModel.canReplaySelectedSession,
                        canReimport: viewModel.canReimportSelectedSession,
                        isBusy: viewModel.isBusy,
                        replayDescription: viewModel.replayActionDescription,
                        reimportDescription: viewModel.reimportActionDescription,
                        exportDescription: viewModel.exportActionDescription,
                        replayDisabledReason: viewModel.replayDisabledReason,
                        reimportDisabledReason: viewModel.reimportDisabledReason,
                        onReplay: { Task { await viewModel.replayGeneration() } },
                        onReimport: { Task { await viewModel.reimportSelected() } },
                        onExport: { Task { await viewModel.exportSelection() } }
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
            Text(badgeLabel(for: session))
                .font(.caption.weight(.medium))
                .foregroundStyle(badgeColor(for: session, palette: palette))
            Text("+\(session.addedCount) · skip \(session.skippedCount) · nf \(session.notFoundCount) · err \(session.errorCount)")
                .font(.caption2.monospaced())
                .foregroundStyle(palette.textTertiary)
        }
        .contentShape(Rectangle())
    }

    private func badgeLabel(for session: SessionHistorySummary) -> String {
        switch session.status {
        case .generated: return "generated"
        case .imported: return "imported"
        case .partialSuccess: return "partial"
        case .failed: return "failed"
        case .waitingForManualAcquisition: return "manual"
        }
    }

    private func badgeColor(for session: SessionHistorySummary, palette: ThemePalette) -> Color {
        switch session.status {
        case .generated: return palette.accentPrimary
        case .imported: return palette.statusSuccess
        case .partialSuccess, .waitingForManualAcquisition: return palette.statusWarning
        case .failed: return palette.statusError
        }
    }
}
