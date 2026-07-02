import ResonanceCore
import ResonanceDesign
import SwiftUI

struct PlaylistBuilderView: View {
    @StateObject private var viewModel: PlaylistBuilderViewModel
    @StateObject private var importViewModel: ImportViewModel
    @EnvironmentObject private var themeManager: ThemeManager

    init(
        generationService: any PlaylistGenerationServing = PythonEngineBridgeService(),
        importService: any PlaylistImportServing = PythonEngineBridgeService()
    ) {
        _viewModel = StateObject(wrappedValue: PlaylistBuilderViewModel(service: generationService))
        _importViewModel = StateObject(wrappedValue: ImportViewModel(service: importService))
    }

    var body: some View {
        ThemedScreen {
            switch importViewModel.screenState {
            case .importing, .waitingForManualAcquisition:
                ImportProgressView(
                    progress: importViewModel.progress,
                    manualPrompt: importViewModel.manualPrompt,
                    onConfirmManual: {
                        Task { await importViewModel.confirmManualAcquisition() }
                    }
                )
            case .report:
                if let report = importViewModel.report {
                    ImportReportView(report: report) {
                        importViewModel.reset()
                        viewModel.backToEditing()
                    }
                }
            case .failed(let message):
                failureView(message: message)
            case .idle:
                builderOrPreview
            }
        }
        .navigationTitle("Nouvelle Playlist")
        .onAppear { viewModel.validateForm() }
    }

    @ViewBuilder
    private var builderOrPreview: some View {
        switch viewModel.screenState {
        case .preview:
            if let result = viewModel.previewResult {
                PlaylistPreviewView(
                    result: result,
                    previewSourceLabel: viewModel.previewSourceLabel,
                    onEdit: viewModel.backToEditing,
                    onImport: {
                        Task { await importViewModel.importPlaylist(result) }
                    }
                )
            }
        case .editing, .generating:
            PlaylistBuilderForm(viewModel: viewModel)
        }
    }

    @ViewBuilder
    private func failureView(message: String) -> some View {
        let palette = ThemePalette(theme: themeManager.active)
        VStack(alignment: .leading, spacing: 16) {
            Label("Import impossible", systemImage: "exclamationmark.triangle")
                .font(.title3.weight(.semibold))
                .foregroundStyle(palette.statusWarning)
            Text(message)
                .foregroundStyle(palette.textSecondary)
            Button("Revenir à l'aperçu") {
                importViewModel.reset()
            }
            .buttonStyle(.borderedProminent)
            .tint(palette.accentPrimary)
        }
        .padding(24)
    }
}

private struct PlaylistBuilderForm: View {
    @ObservedObject var viewModel: PlaylistBuilderViewModel
    @EnvironmentObject private var themeManager: ThemeManager
    @State private var showAdvancedOptions = false
    @State private var showExclusions = false

    var body: some View {
        let palette = ThemePalette(theme: themeManager.active)

        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                helpBanner(palette: palette)

                if !viewModel.validationErrors.isEmpty {
                    ValidationBanner(errors: viewModel.validationErrors, palette: palette)
                }

                if let bridgeMessage = viewModel.bridgeFallbackMessage {
                    Text(bridgeMessage)
                        .font(.caption)
                        .foregroundStyle(palette.textTertiary)
                }

                formSection(title: "Essentiel", palette: palette) {
                    ThemedTextField(title: "Nom de la playlist", text: $viewModel.name, palette: palette)
                    ThemedTextField(title: "Artiste seed", text: $viewModel.seedArtist, palette: palette)
                    ThemedTextField(title: "Morceau seed", text: $viewModel.seedTrack, palette: palette)
                    ThemedTextField(
                        title: "Mots-clés (séparés par des virgules)",
                        text: $viewModel.keywordsText,
                        palette: palette
                    )
                    ThemedTextField(
                        title: "Nombre de morceaux",
                        text: $viewModel.targetTrackCountText,
                        palette: palette
                    )
                }

                DisclosureGroup(isExpanded: $showAdvancedOptions) {
                    VStack(alignment: .leading, spacing: 12) {
                        ThemedTextField(
                            title: "Description",
                            text: $viewModel.descriptionText,
                            palette: palette,
                            axis: .vertical
                        )
                        ThemedTextField(
                            title: "Durée cible (min)",
                            text: $viewModel.targetDurationText,
                            palette: palette
                        )
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Courbe d'énergie")
                                .font(.caption)
                                .foregroundStyle(palette.textSecondary)
                            Menu {
                                ForEach(EnergyCurveProfile.allCases) { profile in
                                    Button(profile.displayName) { viewModel.energyProfile = profile }
                                }
                            } label: {
                                HStack {
                                    Text(viewModel.energyProfile.displayName)
                                        .foregroundStyle(palette.textPrimary)
                                    Spacer()
                                    Image(systemName: "chevron.up.chevron.down")
                                        .font(.caption)
                                        .foregroundStyle(palette.textSecondary)
                                }
                                .padding(.horizontal, 12)
                                .padding(.vertical, 10)
                                .background(palette.inputBackground, in: RoundedRectangle(cornerRadius: 8, style: .continuous))
                                .overlay {
                                    RoundedRectangle(cornerRadius: 8, style: .continuous)
                                        .strokeBorder(palette.borderSubtle, lineWidth: 1)
                                        .allowsHitTesting(false)
                                }
                            }
                            .menuStyle(.borderlessButton)
                        }

                        if let provider = viewModel.selectedProvider {
                            HStack {
                                Label(provider.displayName, systemImage: "music.note")
                                    .foregroundStyle(palette.textSecondary)
                                Spacer()
                                Text("Provider par défaut")
                                    .font(.caption)
                                    .foregroundStyle(palette.textTertiary)
                            }
                        }
                    }
                    .padding(.top, 8)
                } label: {
                    Text("Options avancées")
                        .font(.headline)
                        .foregroundStyle(palette.textPrimary)
                }
                .themedSurfaceCard(fill: palette.surface, border: palette.borderSubtle)

                DisclosureGroup(isExpanded: $showExclusions) {
                    VStack(alignment: .leading, spacing: 12) {
                        if viewModel.exclusions.isEmpty {
                            Text("Aucune exclusion pour le moment.")
                                .font(.callout)
                                .foregroundStyle(palette.textSecondary)
                        } else {
                            ForEach(viewModel.exclusions) { rule in
                                ExclusionEditorRow(
                                    rule: binding(for: rule),
                                    palette: palette,
                                    onRemove: { viewModel.removeExclusion(rule) }
                                )
                            }
                        }
                        Button("Ajouter une exclusion") {
                            viewModel.addExclusion()
                            viewModel.validateForm()
                        }
                        .buttonStyle(.borderless)
                        .foregroundStyle(palette.accentPrimary)
                    }
                    .padding(.top, 8)
                } label: {
                    Text("Exclusions")
                        .font(.headline)
                        .foregroundStyle(palette.textPrimary)
                }
                .themedSurfaceCard(fill: palette.surface, border: palette.borderSubtle)

                HStack {
                    if !viewModel.canGenerate {
                        Text("Complète le nom et une graine ou des mots-clés pour activer Générer.")
                            .font(.caption)
                            .foregroundStyle(palette.textTertiary)
                    }
                    Spacer()
                    Button {
                        Task { await viewModel.generate() }
                    } label: {
                        if viewModel.screenState == .generating {
                            ProgressView()
                                .controlSize(.small)
                                .padding(.horizontal, 8)
                        } else {
                            Label("Générer", systemImage: "sparkles")
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(palette.accentPrimary)
                    .disabled(!viewModel.canGenerate)
                }
            }
            .padding(24)
        }
        .onChange(of: viewModel.name) { _, _ in viewModel.validateForm() }
        .onChange(of: viewModel.seedArtist) { _, _ in viewModel.validateForm() }
        .onChange(of: viewModel.seedTrack) { _, _ in viewModel.validateForm() }
        .onChange(of: viewModel.keywordsText) { _, _ in viewModel.validateForm() }
        .onChange(of: viewModel.targetTrackCountText) { _, _ in viewModel.validateForm() }
        .onChange(of: viewModel.targetDurationText) { _, _ in viewModel.validateForm() }
    }

    private func helpBanner(palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Crée une playlist en quelques champs")
                .font(.headline)
                .foregroundStyle(palette.textPrimary)
            Text("Remplis au minimum un nom et une graine ou des mots-clés.")
                .font(.callout)
                .foregroundStyle(palette.textSecondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .themedSurfaceCard(fill: palette.surface, border: palette.borderSubtle, padding: 14)
    }

    private func binding(for rule: ExclusionRule) -> Binding<ExclusionRule> {
        Binding(
            get: {
                viewModel.exclusions.first(where: { $0.id == rule.id }) ?? rule
            },
            set: { updated in
                guard let index = viewModel.exclusions.firstIndex(where: { $0.id == rule.id }) else {
                    return
                }
                viewModel.exclusions[index] = updated
                viewModel.validateForm()
            }
        )
    }

    @ViewBuilder
    private func formSection<Content: View>(
        title: String,
        palette: ThemePalette,
        @ViewBuilder content: () -> Content
    ) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.headline)
                .foregroundStyle(palette.textPrimary)
            content()
        }
        .themedSurfaceCard(fill: palette.surface, border: palette.borderSubtle)
    }
}

private struct ExclusionEditorRow: View {
    @Binding var rule: ExclusionRule
    let palette: ThemePalette
    let onRemove: () -> Void
    @FocusState private var isFocused: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Menu {
                    ForEach(ExclusionKind.allCases) { kind in
                        Button(kind.displayName) { rule.kind = kind }
                    }
                } label: {
                    HStack {
                        Text(rule.kind.displayName)
                            .foregroundStyle(palette.textPrimary)
                        Image(systemName: "chevron.up.chevron.down")
                            .font(.caption)
                            .foregroundStyle(palette.textSecondary)
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 8)
                    .background(palette.inputBackground, in: RoundedRectangle(cornerRadius: 8, style: .continuous))
                }
                .menuStyle(.borderlessButton)

                Spacer()

                Button(role: .cancel, action: onRemove) {
                    Image(systemName: "minus.circle")
                }
                .buttonStyle(.borderless)
                .foregroundStyle(palette.textSecondary)
            }
            TextField("Valeur", text: $rule.value)
                .textFieldStyle(.plain)
                .labelsHidden()
                .foregroundStyle(palette.inputText)
                .tint(palette.accentPrimary)
                .focused($isFocused)
                .themedInputChrome(
                    fill: palette.inputBackground,
                    border: palette.borderSubtle,
                    focusBorder: palette.accentPrimary.opacity(0.65),
                    isFocused: isFocused
                )
        }
    }
}

private struct ValidationBanner: View {
    let errors: [ValidationError]
    let palette: ThemePalette

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Label("Validation", systemImage: "exclamationmark.triangle")
                .font(.headline)
                .foregroundStyle(palette.statusWarning)
            ForEach(errors, id: \.self) { error in
                Text("\(error.field): \(error.message)")
                    .font(.callout)
                    .foregroundStyle(palette.textPrimary)
            }
        }
        .padding(12)
        .background(palette.statusWarning.opacity(0.12), in: RoundedRectangle(cornerRadius: 10, style: .continuous))
    }
}
