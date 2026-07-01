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
        .onChange(of: viewModel.name) { _, _ in viewModel.validateForm() }
        .onChange(of: viewModel.seedArtist) { _, _ in viewModel.validateForm() }
        .onChange(of: viewModel.seedTrack) { _, _ in viewModel.validateForm() }
        .onChange(of: viewModel.keywordsText) { _, _ in viewModel.validateForm() }
        .onChange(of: viewModel.targetTrackCountText) { _, _ in viewModel.validateForm() }
        .onChange(of: viewModel.targetDurationText) { _, _ in viewModel.validateForm() }
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
            builderForm
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

    private var builderForm: some View {
        let palette = ThemePalette(theme: themeManager.active)

        return ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                if !viewModel.validationErrors.isEmpty {
                    ValidationBanner(errors: viewModel.validationErrors, palette: palette)
                }

                if let bridgeMessage = viewModel.bridgeFallbackMessage {
                    Text(bridgeMessage)
                        .font(.caption)
                        .foregroundStyle(palette.textTertiary)
                }

                formSection(title: "Identité", palette: palette) {
                    BuilderTextField(title: "Nom", text: $viewModel.name, palette: palette)
                    BuilderTextField(
                        title: "Description",
                        text: $viewModel.descriptionText,
                        palette: palette,
                        axis: .vertical
                    )
                }

                formSection(title: "Provider", palette: palette) {
                    if let provider = viewModel.selectedProvider {
                        HStack {
                            Label(provider.displayName, systemImage: "music.note")
                            Spacer()
                            Text("Sélectionné")
                                .font(.caption)
                                .foregroundStyle(palette.textSecondary)
                        }
                        .padding(12)
                        .background(palette.backgroundElevated.opacity(0.65))
                        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                        .overlay(
                            RoundedRectangle(cornerRadius: 10, style: .continuous)
                                .stroke(palette.borderSubtle, lineWidth: 1)
                        )
                        .opacity(0.72)
                    }
                }

                formSection(title: "Graines", palette: palette) {
                    BuilderTextField(title: "Artiste seed", text: $viewModel.seedArtist, palette: palette)
                    BuilderTextField(title: "Morceau seed", text: $viewModel.seedTrack, palette: palette)
                }

                formSection(title: "Ambiance & taille", palette: palette) {
                    BuilderTextField(
                        title: "Mots-clés (séparés par des virgules)",
                        text: $viewModel.keywordsText,
                        palette: palette
                    )
                    HStack(spacing: 16) {
                        BuilderTextField(
                            title: "Nombre de morceaux",
                            text: $viewModel.targetTrackCountText,
                            palette: palette
                        )
                        BuilderTextField(
                            title: "Durée cible (min)",
                            text: $viewModel.targetDurationText,
                            palette: palette
                        )
                    }
                    Picker("Courbe d'énergie", selection: $viewModel.energyProfile) {
                        ForEach(EnergyCurveProfile.allCases) { profile in
                            Text(profile.displayName).tag(profile)
                        }
                    }
                    .pickerStyle(.menu)
                }

                formSection(title: "Exclusions", palette: palette) {
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

                HStack {
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
        .padding(16)
        .background(palette.backgroundSecondary)
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .stroke(palette.borderSubtle, lineWidth: 1)
        )
    }
}

private struct BuilderTextField: View {
    let title: String
    @Binding var text: String
    let palette: ThemePalette
    var axis: Axis = .horizontal

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.caption)
                .foregroundStyle(palette.textSecondary)
            TextField(title, text: $text, axis: axis)
                .textFieldStyle(.plain)
                .padding(10)
                .background(palette.backgroundElevated)
                .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 8, style: .continuous)
                        .stroke(palette.borderSubtle, lineWidth: 1)
                )
        }
    }
}

private struct ExclusionEditorRow: View {
    @Binding var rule: ExclusionRule
    let palette: ThemePalette
    let onRemove: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Picker("Type", selection: $rule.kind) {
                    ForEach(ExclusionKind.allCases) { kind in
                        Text(kind.displayName).tag(kind)
                    }
                }
                .pickerStyle(.menu)
                Spacer()
                Button(role: .cancel, action: onRemove) {
                    Image(systemName: "minus.circle")
                }
                .buttonStyle(.borderless)
                .foregroundStyle(palette.textSecondary)
            }
            TextField("Valeur", text: $rule.value)
                .textFieldStyle(.plain)
                .padding(10)
                .background(palette.backgroundElevated)
                .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
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
                    .foregroundStyle(palette.textSecondary)
            }
        }
        .padding(12)
        .background(palette.statusWarning.opacity(0.12))
        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
    }
}
