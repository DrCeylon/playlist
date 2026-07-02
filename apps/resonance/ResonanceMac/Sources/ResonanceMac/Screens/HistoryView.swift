import ResonanceCore
import ResonanceDesign
import SwiftUI

struct HistoryView: View {
    @StateObject private var viewModel: HistoryViewModel
    @EnvironmentObject private var themeManager: ThemeManager

    init(service: any SessionHistoryServing = PythonEngineBridgeService()) {
        _viewModel = StateObject(wrappedValue: HistoryViewModel(service: service))
    }

    var body: some View {
        ThemedScreen {
            let palette = ThemePalette(theme: themeManager.active)
            VStack(alignment: .leading, spacing: 16) {
                header(palette: palette)
                content(palette: palette)
                if !viewModel.actionMessage.isEmpty {
                    Text(viewModel.actionMessage)
                        .font(.caption)
                        .foregroundStyle(palette.textSecondary)
                }
            }
            .padding(24)
        }
        .navigationTitle("Historique")
        .task {
            await viewModel.refresh()
        }
    }

    private func header(palette: ThemePalette) -> some View {
        HStack {
            Text("Sessions locales")
                .font(.title2.weight(.semibold))
                .foregroundStyle(palette.textPrimary)
            Spacer()
            Button("Vider") { Task { await viewModel.clearAll() } }
                .buttonStyle(.bordered)
            Button("Rafraîchir") { Task { await viewModel.refresh() } }
                .buttonStyle(.borderedProminent)
                .tint(palette.accentPrimary)
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

                    SessionDetailView(
                        detail: viewModel.selectedDetail,
                        onReplay: { Task { _ = await viewModel.replayGeneration() } },
                        onReimport: { viewModel.actionMessage = "Réimport prévu en extension 4.8b." },
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
