import ResonanceCore
import ResonanceDesign
import SwiftUI

struct RemoteImportView: View {
    @ObservedObject var viewModel: RemoteImportViewModel
    @EnvironmentObject private var themeManager: ThemeManager
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ThemedScreen {
            let palette = ThemePalette(theme: themeManager.active)
            VStack(alignment: .leading, spacing: 16) {
                Text("Importer depuis un service musical")
                    .font(.title3.weight(.semibold))
                    .foregroundStyle(palette.textPrimary)
                Text("Parcourez vos playlists Apple Music ou YouTube Music, puis importez-les dans Resonance.")
                    .font(.callout)
                    .foregroundStyle(palette.textSecondary)

                Picker("Service", selection: $viewModel.selectedProviderID) {
                    ForEach(viewModel.importableProviders) { provider in
                        Text(provider.displayName).tag(provider.providerID)
                    }
                }
                .pickerStyle(.segmented)
                .onChange(of: viewModel.selectedProviderID) { _, _ in
                    Task { await viewModel.refreshRemotePlaylists() }
                }

                if viewModel.isBusy && viewModel.remotePlaylists.isEmpty {
                    ProgressView()
                } else if viewModel.remotePlaylists.isEmpty {
                    ProductEmptyState(
                        title: "Aucune playlist",
                        message: "Connectez le service dans l'onglet Services musicaux, puis réessayez.",
                        systemImage: "arrow.down.circle",
                        palette: palette
                    )
                } else {
                    List(viewModel.remotePlaylists) { playlist in
                        Button {
                            Task { await viewModel.preview(remotePlaylistID: playlist.remotePlaylistID) }
                        } label: {
                            HStack {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(playlist.name)
                                        .font(.callout.weight(.semibold))
                                    Text("\(playlist.trackCount) morceaux")
                                        .font(.caption)
                                        .foregroundStyle(palette.textSecondary)
                                }
                                Spacer()
                                if viewModel.selectedSnapshot?.remotePlaylistID == playlist.remotePlaylistID {
                                    Image(systemName: "checkmark.circle.fill")
                                        .foregroundStyle(palette.statusSuccess)
                                }
                            }
                        }
                        .buttonStyle(.plain)
                    }
                    .frame(minHeight: 220, maxHeight: 320)
                }

                if let snapshot = viewModel.selectedSnapshot {
                    Text("Aperçu : \(snapshot.name) · \(snapshot.trackCount) morceau(x)")
                        .font(.callout)
                        .foregroundStyle(palette.textSecondary)
                    Button("Importer dans Resonance") {
                        Task { await viewModel.importSelected() }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(viewModel.isBusy)
                }

                if let feedback = viewModel.actionFeedback {
                    Text(feedback)
                        .font(.caption)
                        .foregroundStyle(palette.textSecondary)
                }

                HStack {
                    Spacer()
                    Button("Fermer") { dismiss() }
                        .keyboardShortcut(.cancelAction)
                }
            }
            .padding(24)
        }
        .task { await viewModel.refreshRemotePlaylists() }
    }
}
