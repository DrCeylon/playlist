import ResonanceCore
import ResonanceDesign
import SwiftUI

struct ProvidersView: View {
    @StateObject private var viewModel: ProvidersViewModel
    @EnvironmentObject private var themeManager: ThemeManager

    init(service: any DiagnosticsServing = MockDiagnosticsService()) {
        _viewModel = StateObject(wrappedValue: ProvidersViewModel(service: service))
    }

    var body: some View {
        ThemedScreen {
            let palette = ThemePalette(theme: themeManager.active)
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    header(palette: palette)
                    providerSection(
                        title: "Providers principaux",
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
        .navigationTitle("Providers")
        .task { await viewModel.refresh() }
    }

    @ViewBuilder
    private func header(palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Providers musicaux")
                .font(.title2.weight(.semibold))
                .foregroundStyle(palette.textPrimary)
            Text("Resonance reste provider-neutral : l'UI ne doit pas supposer Apple Music comme seul backend.")
                .font(.callout)
                .foregroundStyle(palette.textSecondary)
        }
        .themedSurfaceCard(fill: palette.surface, border: palette.borderSubtle)
    }

    @ViewBuilder
    private func providerSection(
        title: String,
        providers: [ProviderOption],
        palette: ThemePalette
    ) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.headline)
            if providers.isEmpty {
                Text("Aucun provider dans cette catégorie.")
                    .font(.callout)
                    .foregroundStyle(palette.textSecondary)
            } else {
                ForEach(providers) { provider in
                    providerRow(provider, palette: palette)
                }
            }
        }
        .themedSurfaceCard(fill: palette.surface, border: palette.borderSubtle)
    }

    @ViewBuilder
    private func providerRow(_ provider: ProviderOption, palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(provider.displayName)
                    .font(.callout.weight(.semibold))
                Spacer()
                statusBadge(provider, palette: palette)
            }
            if !provider.capabilities.isEmpty {
                Text(provider.capabilities.map(\.rawValue).joined(separator: ", "))
                    .font(.caption2)
                    .foregroundStyle(palette.textSecondary)
            }
            if !provider.unavailableReason.isEmpty {
                Text(provider.unavailableReason)
                    .font(.caption)
                    .foregroundStyle(palette.textSecondary)
            }
        }
        .padding(.vertical, 4)
    }

    @ViewBuilder
    private func statusBadge(_ provider: ProviderOption, palette: ThemePalette) -> some View {
        let label: String
        let color: Color
        if provider.isAvailable {
            label = provider.isConnected ? "Connecté" : "Disponible"
            color = palette.statusSuccess
        } else if provider.isExperimental {
            label = "Expérimental"
            color = palette.statusWarning
        } else {
            label = "Indisponible"
            color = palette.textSecondary
        }
        Text(label)
            .font(.caption2.weight(.semibold))
            .foregroundStyle(color)
    }
}
