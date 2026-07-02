import ResonanceCore
import ResonanceDesign
import SwiftUI

struct PlaylistBuilderView: View {
    @StateObject private var viewModel: PlaylistBuilderViewModel
    @StateObject private var importViewModel: ImportViewModel
    @EnvironmentObject private var themeManager: ThemeManager

    // Local draft state — macOS TextField binds reliably to @State, not always to @Published.
    @State private var draftName = ""
    @State private var draftSeedArtist = ""
    @State private var draftSeedTrack = ""
    @State private var draftKeywords = ""
    @State private var draftTrackCount = ""
    @State private var draftDescription = ""
    @State private var draftDuration = ""
    @State private var showAdvancedOptions = false
    @State private var showExclusions = false

    init(
        generationService: any PlaylistGenerationServing = PythonEngineBridgeService(),
        importService: any PlaylistImportServing = PythonEngineBridgeService()
    ) {
        _viewModel = StateObject(wrappedValue: PlaylistBuilderViewModel(service: generationService))
        _importViewModel = StateObject(wrappedValue: ImportViewModel(service: importService))
    }

    var body: some View {
        let palette = ThemePalette(theme: themeManager.active)

        Group {
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
                        syncDraftFromViewModel()
                    }
                }
            case .failed(let message):
                failureView(message: message, palette: palette)
            case .idle:
                builderOrPreview(palette: palette)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .background(palette.backgroundPrimary)
        .navigationTitle("Nouvelle Playlist")
        .onAppear {
            syncDraftFromViewModel()
            pushDraftToViewModel()
            viewModel.validateForm()
        }
        .onChange(of: viewModel.screenState) { _, newState in
            if newState == .editing {
                syncDraftFromViewModel()
            }
        }
    }

    @ViewBuilder
    private func builderOrPreview(palette: ThemePalette) -> some View {
        switch viewModel.screenState {
        case .preview:
            if let result = viewModel.previewResult {
                PlaylistPreviewView(
                    result: result,
                    previewSourceLabel: viewModel.previewSourceLabel,
                    onEdit: {
                        viewModel.backToEditing()
                        syncDraftFromViewModel()
                    },
                    onImport: {
                        Task { await importViewModel.importPlaylist(result) }
                    }
                )
            }
        case .editing, .generating:
            builderForm(palette: palette)
        }
    }

    @ViewBuilder
    private func builderForm(palette: ThemePalette) -> some View {
        Form {
            Section {
                Text("Remplis au minimum un nom et une graine ou des mots-clés.")
                    .font(.callout)
                    .foregroundStyle(palette.textSecondary)
            }

            if !viewModel.validationErrors.isEmpty {
                Section {
                    ForEach(viewModel.validationErrors, id: \.self) { error in
                        Text("\(error.field): \(error.message)")
                            .font(.callout)
                            .foregroundStyle(palette.statusWarning)
                    }
                }
            }

            if let bridgeMessage = viewModel.bridgeFallbackMessage {
                Section {
                    Text(bridgeMessage)
                        .font(.caption)
                        .foregroundStyle(palette.textTertiary)
                }
            }

            Section("Essentiel") {
                nativeTextField("Nom de la playlist", text: $draftName, palette: palette)
                nativeTextField("Artiste seed", text: $draftSeedArtist, palette: palette)
                nativeTextField("Morceau seed", text: $draftSeedTrack, palette: palette)
                nativeTextField("Mots-clés (séparés par des virgules)", text: $draftKeywords, palette: palette)
                nativeTextField("Nombre de morceaux", text: $draftTrackCount, palette: palette)
            }

            Section {
                DisclosureGroup("Options avancées", isExpanded: $showAdvancedOptions) {
                    nativeTextField("Description", text: $draftDescription, palette: palette, axis: .vertical)
                    nativeTextField("Durée cible (min)", text: $draftDuration, palette: palette)
                    Picker("Courbe d'énergie", selection: $viewModel.energyProfile) {
                        ForEach(EnergyCurveProfile.allCases) { profile in
                            Text(profile.displayName).tag(profile)
                        }
                    }
                    if let provider = viewModel.selectedProvider {
                        LabeledContent("Provider", value: provider.displayName)
                    }
                }
            }

            Section {
                DisclosureGroup("Exclusions", isExpanded: $showExclusions) {
                    if viewModel.exclusions.isEmpty {
                        Text("Aucune exclusion pour le moment.")
                            .foregroundStyle(palette.textSecondary)
                    } else {
                        ForEach($viewModel.exclusions) { $rule in
                            ExclusionEditorRow(rule: $rule, palette: palette) {
                                viewModel.removeExclusion(rule.wrappedValue)
                            }
                        }
                    }
                    Button("Ajouter une exclusion") {
                        viewModel.addExclusion()
                        pushDraftToViewModel()
                        viewModel.validateForm()
                    }
                }
            }

            Section {
                if !viewModel.canGenerate {
                    Text("Complète le nom et une graine ou des mots-clés pour activer Générer.")
                        .font(.caption)
                        .foregroundStyle(palette.textTertiary)
                }
                Button {
                    pushDraftToViewModel()
                    Task { await viewModel.generate() }
                } label: {
                    if viewModel.screenState == .generating {
                        ProgressView()
                            .controlSize(.small)
                    } else {
                        Label("Générer", systemImage: "sparkles")
                    }
                }
                .disabled(!viewModel.canGenerate)
            }
        }
        .formStyle(.grouped)
        .scrollContentBackground(.hidden)
        .onChange(of: draftName) { _, _ in commitDraftAndValidate() }
        .onChange(of: draftSeedArtist) { _, _ in commitDraftAndValidate() }
        .onChange(of: draftSeedTrack) { _, _ in commitDraftAndValidate() }
        .onChange(of: draftKeywords) { _, _ in commitDraftAndValidate() }
        .onChange(of: draftTrackCount) { _, _ in commitDraftAndValidate() }
        .onChange(of: draftDescription) { _, _ in commitDraftAndValidate() }
        .onChange(of: draftDuration) { _, _ in commitDraftAndValidate() }
        .onChange(of: viewModel.energyProfile) { _, _ in viewModel.validateForm() }
        .onChange(of: viewModel.exclusions) { _, _ in
            pushDraftToViewModel()
            viewModel.validateForm()
        }
    }

    @ViewBuilder
    private func nativeTextField(
        _ title: String,
        text: Binding<String>,
        palette: ThemePalette,
        axis: Axis = .horizontal
    ) -> some View {
        TextField(title, text: text, axis: axis)
            .textFieldStyle(.roundedBorder)
            .foregroundStyle(palette.inputText)
    }

    private func syncDraftFromViewModel() {
        draftName = viewModel.name
        draftSeedArtist = viewModel.seedArtist
        draftSeedTrack = viewModel.seedTrack
        draftKeywords = viewModel.keywordsText
        draftTrackCount = viewModel.targetTrackCountText
        draftDescription = viewModel.descriptionText
        draftDuration = viewModel.targetDurationText
    }

    private func pushDraftToViewModel() {
        viewModel.name = draftName
        viewModel.seedArtist = draftSeedArtist
        viewModel.seedTrack = draftSeedTrack
        viewModel.keywordsText = draftKeywords
        viewModel.targetTrackCountText = draftTrackCount
        viewModel.descriptionText = draftDescription
        viewModel.targetDurationText = draftDuration
    }

    private func commitDraftAndValidate() {
        pushDraftToViewModel()
        viewModel.validateForm()
    }

    @ViewBuilder
    private func failureView(message: String, palette: ThemePalette) -> some View {
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
                .labelsHidden()
                Spacer()
                Button(role: .cancel, action: onRemove) {
                    Image(systemName: "minus.circle")
                }
                .buttonStyle(.borderless)
            }
            TextField("Valeur", text: $rule.value)
                .textFieldStyle(.roundedBorder)
                .foregroundStyle(palette.inputText)
        }
    }
}
