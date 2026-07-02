import ResonanceCore
import ResonanceDesign
import SwiftUI

struct PlaylistBuilderView: View {
    @StateObject private var viewModel: PlaylistBuilderViewModel
    @StateObject private var importViewModel: ImportViewModel
    @EnvironmentObject private var themeManager: ThemeManager

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
                ImportFailureView(message: message, palette: palette) {
                    importViewModel.reset()
                }
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
            PlaylistBuilderFormView(
                viewModel: viewModel,
                palette: palette,
                draftName: $draftName,
                draftSeedArtist: $draftSeedArtist,
                draftSeedTrack: $draftSeedTrack,
                draftKeywords: $draftKeywords,
                draftTrackCount: $draftTrackCount,
                draftDescription: $draftDescription,
                draftDuration: $draftDuration,
                showAdvancedOptions: $showAdvancedOptions,
                showExclusions: $showExclusions,
                onCommitDraft: commitDraftAndValidate,
                onPushDraft: pushDraftToViewModel
            )
        }
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
}

// MARK: - Form

private struct PlaylistBuilderFormView: View {
    @ObservedObject var viewModel: PlaylistBuilderViewModel
    let palette: ThemePalette

    @Binding var draftName: String
    @Binding var draftSeedArtist: String
    @Binding var draftSeedTrack: String
    @Binding var draftKeywords: String
    @Binding var draftTrackCount: String
    @Binding var draftDescription: String
    @Binding var draftDuration: String
    @Binding var showAdvancedOptions: Bool
    @Binding var showExclusions: Bool

    let onCommitDraft: () -> Void
    let onPushDraft: () -> Void

    var body: some View {
        Form {
            BuilderHelpSection(palette: palette)
            ValidationSection(errors: viewModel.validationErrors, palette: palette)
            BridgeMessageSection(message: viewModel.bridgeFallbackMessage, palette: palette)
            EssentialFieldsSection(
                palette: palette,
                draftName: $draftName,
                draftSeedArtist: $draftSeedArtist,
                draftSeedTrack: $draftSeedTrack,
                draftKeywords: $draftKeywords,
                draftTrackCount: $draftTrackCount
            )
            AdvancedOptionsSection(
                viewModel: viewModel,
                palette: palette,
                draftDescription: $draftDescription,
                draftDuration: $draftDuration,
                isExpanded: $showAdvancedOptions
            )
            ExclusionsSection(
                viewModel: viewModel,
                palette: palette,
                isExpanded: $showExclusions,
                onPushDraft: onPushDraft
            )
            GenerateSection(
                viewModel: viewModel,
                palette: palette,
                onPushDraft: onPushDraft
            )
        }
        .formStyle(.grouped)
        .scrollContentBackground(.hidden)
        .onChange(of: draftName) { _, _ in onCommitDraft() }
        .onChange(of: draftSeedArtist) { _, _ in onCommitDraft() }
        .onChange(of: draftSeedTrack) { _, _ in onCommitDraft() }
        .onChange(of: draftKeywords) { _, _ in onCommitDraft() }
        .onChange(of: draftTrackCount) { _, _ in onCommitDraft() }
        .onChange(of: draftDescription) { _, _ in onCommitDraft() }
        .onChange(of: draftDuration) { _, _ in onCommitDraft() }
        .onChange(of: viewModel.energyProfile) { _, _ in viewModel.validateForm() }
        .onChange(of: viewModel.exclusions) { _, _ in
            onPushDraft()
            viewModel.validateForm()
        }
    }
}

private struct BuilderHelpSection: View {
    let palette: ThemePalette

    var body: some View {
        Section {
            Text("Remplis au minimum un nom et une graine ou des mots-clés.")
                .font(.callout)
                .foregroundStyle(palette.textSecondary)
        }
    }
}

private struct ValidationSection: View {
    let errors: [ValidationError]
    let palette: ThemePalette

    var body: some View {
        if errors.isEmpty {
            EmptyView()
        } else {
            Section {
                ForEach(errors, id: \.self) { error in
                    ValidationRow(error: error, palette: palette)
                }
            }
        }
    }
}

private struct ValidationRow: View {
    let error: ValidationError
    let palette: ThemePalette

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(error.field)
            Text(error.message)
        }
        .font(.callout)
        .foregroundStyle(palette.statusWarning)
    }
}

private struct BridgeMessageSection: View {
    let message: String?
    let palette: ThemePalette

    var body: some View {
        if let message {
            Section {
                Text(message)
                    .font(.caption)
                    .foregroundStyle(palette.textTertiary)
            }
        }
    }
}

private struct EssentialFieldsSection: View {
    let palette: ThemePalette
    @Binding var draftName: String
    @Binding var draftSeedArtist: String
    @Binding var draftSeedTrack: String
    @Binding var draftKeywords: String
    @Binding var draftTrackCount: String

    var body: some View {
        Section("Essentiel") {
            NativeFormTextField(title: "Nom de la playlist", text: $draftName, palette: palette)
            NativeFormTextField(title: "Artiste seed", text: $draftSeedArtist, palette: palette)
            NativeFormTextField(title: "Morceau seed", text: $draftSeedTrack, palette: palette)
            NativeFormTextField(
                title: "Mots-clés (séparés par des virgules)",
                text: $draftKeywords,
                palette: palette
            )
            NativeFormTextField(title: "Nombre de morceaux", text: $draftTrackCount, palette: palette)
        }
    }
}

private struct AdvancedOptionsSection: View {
    @ObservedObject var viewModel: PlaylistBuilderViewModel
    let palette: ThemePalette
    @Binding var draftDescription: String
    @Binding var draftDuration: String
    @Binding var isExpanded: Bool

    var body: some View {
        Section {
            DisclosureGroup("Options avancées", isExpanded: $isExpanded) {
                NativeFormTextField(
                    title: "Description",
                    text: $draftDescription,
                    palette: palette,
                    axis: .vertical
                )
                NativeFormTextField(title: "Durée cible (min)", text: $draftDuration, palette: palette)
                EnergyProfilePicker(selection: $viewModel.energyProfile)
                if let provider = viewModel.selectedProvider {
                    LabeledContent("Provider", value: provider.displayName)
                }
            }
        }
    }
}

private struct EnergyProfilePicker: View {
    @Binding var selection: EnergyCurveProfile

    var body: some View {
        Picker("Courbe d'énergie", selection: $selection) {
            ForEach(EnergyCurveProfile.allCases) { profile in
                Text(profile.displayName).tag(profile)
            }
        }
    }
}

private struct ExclusionsSection: View {
    @ObservedObject var viewModel: PlaylistBuilderViewModel
    let palette: ThemePalette
    @Binding var isExpanded: Bool
    let onPushDraft: () -> Void

    var body: some View {
        Section {
            DisclosureGroup("Exclusions", isExpanded: $isExpanded) {
                ExclusionsList(viewModel: viewModel, palette: palette, onPushDraft: onPushDraft)
            }
        }
    }
}

private struct ExclusionsList: View {
    @ObservedObject var viewModel: PlaylistBuilderViewModel
    let palette: ThemePalette
    let onPushDraft: () -> Void

    var body: some View {
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
            onPushDraft()
            viewModel.validateForm()
        }
    }
}

private struct GenerateSection: View {
    @ObservedObject var viewModel: PlaylistBuilderViewModel
    let palette: ThemePalette
    let onPushDraft: () -> Void

    var body: some View {
        Section {
            if !viewModel.canGenerate {
                Text("Complète le nom et une graine ou des mots-clés pour activer Générer.")
                    .font(.caption)
                    .foregroundStyle(palette.textTertiary)
            }
            GenerateButton(viewModel: viewModel, onPushDraft: onPushDraft)
        }
    }
}

private struct GenerateButton: View {
    @ObservedObject var viewModel: PlaylistBuilderViewModel
    let onPushDraft: () -> Void

    var body: some View {
        Button {
            onPushDraft()
            Task { await viewModel.generate() }
        } label: {
            GenerateButtonLabel(isGenerating: viewModel.screenState == .generating)
        }
        .disabled(!viewModel.canGenerate)
    }
}

private struct GenerateButtonLabel: View {
    let isGenerating: Bool

    var body: some View {
        if isGenerating {
            ProgressView()
                .controlSize(.small)
        } else {
            Label("Générer", systemImage: "sparkles")
        }
    }
}

private struct NativeFormTextField: View {
    let title: String
    @Binding var text: String
    let palette: ThemePalette
    var axis: Axis = .horizontal

    var body: some View {
        TextField(title, text: $text, axis: axis)
            .textFieldStyle(.roundedBorder)
            .foregroundStyle(palette.inputText)
    }
}

private struct ImportFailureView: View {
    let message: String
    let palette: ThemePalette
    let onReset: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Label("Import impossible", systemImage: "exclamationmark.triangle")
                .font(.title3.weight(.semibold))
                .foregroundStyle(palette.statusWarning)
            Text(message)
                .foregroundStyle(palette.textSecondary)
            Button("Revenir à l'aperçu", action: onReset)
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
