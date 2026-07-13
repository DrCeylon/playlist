import ResonanceCore
import ResonanceDesign
import SwiftUI
import UniformTypeIdentifiers

struct ProvidersView: View {
    @ObservedObject var viewModel: ProvidersViewModel
    @EnvironmentObject private var themeManager: ThemeManager
    @State private var youtubeHeadersImporter: ProviderID?
    @State private var selectedHeadersURL: URL?

    var body: some View {
        ThemedScreen {
            let palette = ThemePalette(theme: themeManager.active)
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    ProductSectionCard(title: "Services musicaux", palette: palette) {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Connecte tes comptes pour importer et synchroniser tes playlists.")
                                .font(.callout)
                                .foregroundStyle(palette.textSecondary)
                            Text("YouTube Music utilise un fichier d'en-têtes exporté via ytmusicapi. L'API n'est pas officielle — fonctionnalité expérimentale.")
                                .font(.caption)
                                .foregroundStyle(palette.textSecondary)
                        }
                    }
                    providerSection(
                        title: "Principaux",
                        providers: viewModel.primaryProviders,
                        palette: palette
                    )
                    providerSection(
                        title: "Expérimental",
                        providers: viewModel.experimentalProviders,
                        palette: palette
                    )
                    if let feedback = viewModel.actionFeedback {
                        Text(feedback)
                            .font(.caption)
                            .foregroundStyle(palette.textSecondary)
                    }
                }
                .padding(24)
            }
        }
        .navigationTitle("Services musicaux")
        .task { await viewModel.refresh() }
        .refreshable { await viewModel.refresh() }
        .fileImporter(
            isPresented: Binding(
                get: { youtubeHeadersImporter != nil },
                set: { if !$0 { youtubeHeadersImporter = nil } }
            ),
            allowedContentTypes: [.json],
            allowsMultipleSelection: false
        ) { result in
            guard let providerID = youtubeHeadersImporter else { return }
            switch result {
            case .success(let urls):
                guard let url = urls.first else { return }
                guard url.startAccessingSecurityScopedResource() else { return }
                defer { url.stopAccessingSecurityScopedResource() }
                Task {
                    await viewModel.connect(
                        providerID: providerID,
                        params: [
                            "headers_file_path": url.path,
                            "display_name": "YouTube Music",
                        ]
                    )
                }
            case .failure:
                viewModel.actionFeedback = "Sélection du fichier d'en-têtes annulée."
            }
        }
    }

    @ViewBuilder
    private func providerSection(
        title: String,
        providers: [ProviderOption],
        palette: ThemePalette
    ) -> some View {
        ProductSectionCard(title: title, palette: palette) {
            if providers.isEmpty {
                Text("Aucun service dans cette catégorie.")
                    .font(.callout)
                    .foregroundStyle(palette.textSecondary)
            } else {
                ForEach(providers) { provider in
                    providerRow(provider, palette: palette)
                }
            }
        }
    }

    @ViewBuilder
    private func providerRow(_ provider: ProviderOption, palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(provider.displayName)
                    .font(.callout.weight(.semibold))
                Spacer()
                StatusChip(label: statusLabel(for: provider), color: statusColor(for: provider, palette: palette))
            }
            if !provider.capabilities.isEmpty {
                Text(provider.capabilities.map(ProductDisplay.providerCapabilityLabel).joined(separator: " · "))
                    .font(.caption2)
                    .foregroundStyle(palette.textSecondary)
            }
            if !provider.unavailableReason.isEmpty {
                Text(provider.unavailableReason)
                    .font(.caption)
                    .foregroundStyle(palette.textSecondary)
            }
            if provider.isAvailable && viewModel.supportsAuthentication(provider) {
                HStack {
                    if provider.isConnected {
                        Button("Déconnecter") {
                            Task { await viewModel.disconnect(providerID: provider.providerID) }
                        }
                        .buttonStyle(.bordered)
                    } else if viewModel.requiresHeadersFile(provider) {
                        Button("Choisir le fichier d'en-têtes") {
                            youtubeHeadersImporter = provider.providerID
                        }
                        .buttonStyle(.borderedProminent)
                    } else {
                        Button("Connecter") {
                            Task { await viewModel.connect(providerID: provider.providerID) }
                        }
                        .buttonStyle(.borderedProminent)
                    }
                }
                .disabled(viewModel.isBusy)
            }
        }
        .padding(.vertical, 4)
    }

    private func statusLabel(for provider: ProviderOption) -> String {
        if provider.isConnected { return "Connecté" }
        if provider.isAvailable { return "Disponible" }
        if provider.isExperimental { return "Expérimental" }
        return "Indisponible"
    }

    private func statusColor(for provider: ProviderOption, palette: ThemePalette) -> Color {
        if provider.isConnected { return palette.statusSuccess }
        if provider.isAvailable { return palette.accentPrimary }
        if provider.isExperimental { return palette.statusWarning }
        return palette.textSecondary
    }
}
