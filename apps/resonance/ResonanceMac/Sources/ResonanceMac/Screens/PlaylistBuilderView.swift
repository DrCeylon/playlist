import ResonanceCore
import ResonanceDesign
import SwiftUI

struct PlaylistBuilderView: View {
    @Binding var selection: SidebarItem?
    @EnvironmentObject private var workflow: AppWorkflowCoordinator

    init(selection: Binding<SidebarItem?>) {
        _selection = selection
    }

    var body: some View {
        PlaylistBuilderScreen(selection: $selection, workflow: workflow)
    }
}

private struct PlaylistBuilderScreen: View {
    @Binding var selection: SidebarItem?
    @ObservedObject var viewModel: PlaylistBuilderViewModel
    @ObservedObject var importViewModel: ImportViewModel
    @ObservedObject var smartInputEngines: SmartInputFormEngines
    @ObservedObject var workflow: AppWorkflowCoordinator
    @EnvironmentObject private var themeManager: ThemeManager

    @State private var draftName = ""
    @State private var draftTrackCount = ""
    @State private var draftDescription = ""
    @State private var draftDuration = ""
    @State private var showAdvancedOptions = false
    @State private var showExclusions = false

    init(selection: Binding<SidebarItem?>, workflow: AppWorkflowCoordinator) {
        _selection = selection
        _viewModel = ObservedObject(wrappedValue: workflow.playlistBuilder)
        _importViewModel = ObservedObject(wrappedValue: workflow.importWorkflow)
        _smartInputEngines = ObservedObject(wrappedValue: workflow.smartInputEngines)
        _workflow = ObservedObject(wrappedValue: workflow)
    }

    private var isImportWorkflowVisible: Bool {
        switch importViewModel.screenState {
        case .importing, .waitingForManualAcquisition, .report, .failed:
            return true
        case .idle:
            return false
        }
    }

    var body: some View {
        let palette = ThemePalette(theme: themeManager.active)

        Group {
            switch importViewModel.screenState {
            case .importing, .waitingForManualAcquisition:
                ImportProgressView(
                    progress: importViewModel.progress,
                    manualPrompt: importViewModel.manualPrompt,
                    manualPollStatus: importViewModel.manualPollStatus,
                    manualAcquisitionStatus: importViewModel.manualAcquisitionStatus,
                    architectErrorDetail: importViewModel.architectErrorDetail,
                    architectManualDiagnostics: importViewModel.architectManualDiagnostics,
                    isContinueInProgress: importViewModel.isContinuingManual,
                    embeddedInPanel: true,
                    onConfirmManual: {
                        Task { await importViewModel.confirmManualAcquisition() }
                    }
                )
            case .report:
                if let report = importViewModel.report {
                    BoundedScrollScreen {
                        ImportReportView(report: report, onRetryTrack: { index in
                            Task { await importViewModel.retryImportTrack(at: index) }
                        }) {
                            importViewModel.reset()
                            viewModel.screenState = .editing
                            syncDraftFromViewModel()
                        }
                    }
                }
            case .failed(let message):
                ImportFailureView(
                    message: message,
                    architectErrorDetail: importViewModel.architectErrorDetail,
                    palette: palette
                ) {
                    importViewModel.reset()
                }
            case .idle:
                builderOrPreview(palette: palette)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .background {
            if isImportWorkflowVisible {
                palette.backgroundPrimary
            } else {
                InspirationArtworkBackdrop(
                    artworkURL: effectiveArtworkURL,
                    palette: palette
                )
            }
        }
        .navigationTitle("Nouvelle Playlist")
        .onAppear {
            workflow.applyPendingEditIfNeeded()
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

    private var effectiveArtworkURL: URL? {
        smartInputEngines.trackHolder.selectedArtworkURL
            ?? smartInputEngines.artistHolder.selectedArtworkURL
            ?? viewModel.inspirationArtworkURL
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
                        viewModel.screenState = .editing
                        syncDraftFromViewModel()
                    },
                    onImport: {
                        guard workflow.canStartProcess() else { return }
                        workflow.activeRoute = .newPlaylist
                        selection = .newPlaylist
                        Task { await importViewModel.importPlaylist(result) }
                    }
                )
            }
        case .editing, .generating:
            PlaylistBuilderFormView(
                viewModel: viewModel,
                smartInputEngines: smartInputEngines,
                palette: palette,
                draftName: $draftName,
                draftTrackCount: $draftTrackCount,
                draftDescription: $draftDescription,
                draftDuration: $draftDuration,
                showAdvancedOptions: $showAdvancedOptions,
                showExclusions: $showExclusions,
                validationErrors: viewModel.validationErrors,
                bridgeFallbackMessage: viewModel.bridgeFallbackMessage,
                canStartProcess: workflow.canStartProcess(),
                onCommitDraft: commitDraftAndValidate,
                onPushDraft: pushDraftToViewModel,
                onGenerate: {
                    guard workflow.canStartProcess() else { return }
                    workflow.activeRoute = .newPlaylist
                    selection = .newPlaylist
                    commitDraftAndValidate()
                    pushDraftToViewModel()
                    Task { await viewModel.generate() }
                }
            )
        }
    }

    private func syncDraftFromViewModel() {
        draftName = viewModel.name
        draftTrackCount = viewModel.targetTrackCountText
        draftDescription = viewModel.descriptionText
        draftDuration = viewModel.targetDurationText
        smartInputEngines.syncFromViewModel(viewModel)
    }

    private func pushDraftToViewModel() {
        viewModel.name = draftName
        viewModel.targetTrackCountText = draftTrackCount
        viewModel.descriptionText = draftDescription
        viewModel.targetDurationText = draftDuration
        smartInputEngines.pushToViewModel(viewModel)
    }

    private func commitDraftAndValidate() {
        pushDraftToViewModel()
        viewModel.validateForm()
    }
}

// MARK: - Form

private struct PlaylistBuilderFormView: View {
    @ObservedObject var viewModel: PlaylistBuilderViewModel
    @ObservedObject var smartInputEngines: SmartInputFormEngines
    let palette: ThemePalette

    @Binding var draftName: String
    @Binding var draftTrackCount: String
    @Binding var draftDescription: String
    @Binding var draftDuration: String
    @Binding var showAdvancedOptions: Bool
    @Binding var showExclusions: Bool
    let validationErrors: [ValidationError]
    let bridgeFallbackMessage: String?
    let canStartProcess: Bool

    let onCommitDraft: () -> Void
    let onPushDraft: () -> Void
    let onGenerate: () -> Void

    private var draftsLookComplete: Bool {
        let trimmedName = draftName.trimmingCharacters(in: .whitespacesAndNewlines)
        return !trimmedName.isEmpty && viewModel.hasSeedOrKeywords
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                if ResonanceFeatureFlags.keyboardDebugEnabled {
                    DebugInputSection()
                }
                BuilderHelpSection(palette: palette)
                ValidationSection(errors: validationErrors, palette: palette)
                BridgeMessageSection(message: bridgeFallbackMessage, palette: palette)
                EssentialFieldsSection(
                    palette: palette,
                    draftName: $draftName,
                    draftTrackCount: $draftTrackCount,
                    viewModel: viewModel,
                    smartInputEngines: smartInputEngines,
                    onCommitDraft: onCommitDraft,
                    onPushDraft: onPushDraft
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
                    smartInputEngines: smartInputEngines,
                    palette: palette,
                    isExpanded: $showExclusions,
                    onPushDraft: onPushDraft
                )
            }
            .padding(24)
            .frame(maxWidth: .infinity, alignment: .topLeading)
        }
        .scrollIndicators(.visible)
        .scrollContentBackground(.hidden)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .safeAreaInset(edge: .bottom, spacing: 0) {
            VStack(spacing: 0) {
                Divider()
                GenerateFooterSection(
                    viewModel: viewModel,
                    palette: palette,
                    canGenerateFromDrafts: draftsLookComplete,
                    canStartProcess: canStartProcess,
                    onGenerate: onGenerate
                )
                .padding(.horizontal, 24)
                .padding(.vertical, 16)
                .background(palette.backgroundPrimary.opacity(0.82))
            }
        }
        .onChange(of: viewModel.energyProfile) { _, _ in
            onPushDraft()
            viewModel.validateForm()
        }
        .onChange(of: viewModel.exclusions) { _, _ in
            onPushDraft()
            viewModel.validateForm()
        }
    }
}

private struct BuilderHelpSection: View {
    let palette: ThemePalette

    var body: some View {
        Text("Remplis au minimum un nom et une graine ou des mots-clés.")
            .font(.callout)
            .foregroundStyle(palette.textSecondary)
    }
}

private struct ValidationSection: View {
    let errors: [ValidationError]
    let palette: ThemePalette

    var body: some View {
        if !errors.isEmpty {
            VStack(alignment: .leading, spacing: 8) {
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
            Text(message)
                .font(.caption)
                .foregroundStyle(palette.textTertiary)
        }
    }
}

private struct EssentialFieldsSection: View {
    let palette: ThemePalette
    @Binding var draftName: String
    @Binding var draftTrackCount: String
    @ObservedObject var viewModel: PlaylistBuilderViewModel
    @ObservedObject var smartInputEngines: SmartInputFormEngines
    let onCommitDraft: () -> Void
    let onPushDraft: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Essentiel")
                .font(.headline)
            NativeFormTextField(title: "Nom de la playlist", text: $draftName)

            SmartAutocompleteField(
                title: "Artiste d'inspiration",
                placeholder: "Rechercher un artiste…",
                engineHolder: smartInputEngines.artistHolder,
                palette: palette,
                rowContent: { artist, highlighted in
                    AnyView(ArtistResultRow(artist: artist, isHighlighted: highlighted, palette: palette))
                },
                onCommit: {
                    smartInputEngines.pushToViewModel(viewModel)
                    if let artist = viewModel.seedArtist {
                        smartInputEngines.trackHolder.engine.setContext(
                            AutocompleteContext(artistName: artist.displayName, artistID: artist.id)
                        )
                    } else {
                        smartInputEngines.trackHolder.engine.setContext(nil)
                    }
                    onPushDraft()
                    onCommitDraft()
                }
            )

            SmartAutocompleteField(
                title: "Morceau d'inspiration",
                placeholder: "Rechercher un morceau…",
                engineHolder: smartInputEngines.trackHolder,
                palette: palette,
                rowContent: { track, highlighted in
                    AnyView(TrackResultRow(track: track, isHighlighted: highlighted, palette: palette))
                },
                onCommit: {
                    smartInputEngines.pushToViewModel(viewModel)
                    onPushDraft()
                    onCommitDraft()
                }
            )

            KeywordTagField(
                title: "Mots-clés",
                keywords: $viewModel.keywords,
                engineHolder: smartInputEngines.keywordHolder,
                palette: palette,
                onCommit: {
                    onPushDraft()
                    onCommitDraft()
                }
            )

            NativeFormTextField(title: "Nombre de morceaux", text: $draftTrackCount)
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
        DisclosureGroup("Options avancées", isExpanded: $isExpanded) {
            VStack(alignment: .leading, spacing: 16) {
                NativeFormTextField(
                    title: "Description",
                    text: $draftDescription,
                    isMultiline: true
                )
                NativeFormTextField(title: "Durée cible (min)", text: $draftDuration)
                EnergyProfilePicker(selection: $viewModel.energyProfile)
                if !viewModel.selectableProviders.isEmpty {
                    Picker("Source musicale", selection: $viewModel.selectedProviderID) {
                        ForEach(viewModel.selectableProviders) { provider in
                            Text(provider.displayName).tag(provider.providerID)
                        }
                    }
                } else if let provider = viewModel.selectedProvider {
                    LabeledContent("Source musicale", value: provider.displayName)
                }
            }
            .padding(.top, 12)
        }
        .font(.headline)
        .foregroundStyle(palette.textPrimary)
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
    @ObservedObject var smartInputEngines: SmartInputFormEngines
    let palette: ThemePalette
    @Binding var isExpanded: Bool
    let onPushDraft: () -> Void

    var body: some View {
        DisclosureGroup("Exclusions", isExpanded: $isExpanded) {
            ExclusionsList(
                viewModel: viewModel,
                smartInputEngines: smartInputEngines,
                palette: palette,
                onPushDraft: onPushDraft
            )
                .padding(.top, 12)
        }
        .font(.headline)
        .foregroundStyle(palette.textPrimary)
    }
}

private struct ExclusionsList: View {
    @ObservedObject var viewModel: PlaylistBuilderViewModel
    @ObservedObject var smartInputEngines: SmartInputFormEngines
    let palette: ThemePalette
    let onPushDraft: () -> Void

    var body: some View {
        if viewModel.exclusions.isEmpty {
            Text("Aucune exclusion pour le moment.")
                .foregroundStyle(palette.textSecondary)
        } else {
            ForEach(viewModel.exclusions) { rule in
                ExclusionEditorRow(
                    rule: binding(for: rule),
                    palette: palette,
                    autocompleteService: smartInputEngines.autocompleteService,
                    seedArtistName: viewModel.seedArtist?.displayName ?? "",
                    seedArtistID: viewModel.seedArtist?.id ?? "",
                    onRemove: { viewModel.removeExclusion(rule) }
                )
            }
        }
        Button("Ajouter une exclusion") {
            viewModel.addExclusion()
            onPushDraft()
            viewModel.validateForm()
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
            }
        )
    }
}

private struct GenerateFooterSection: View {
    @ObservedObject var viewModel: PlaylistBuilderViewModel
    let palette: ThemePalette
    let canGenerateFromDrafts: Bool
    let canStartProcess: Bool
    let onGenerate: () -> Void

    var body: some View {
        HStack(alignment: .center) {
            VStack(alignment: .leading, spacing: 4) {
                Text("Génération")
                    .font(.headline)
                if !canGenerateFromDrafts {
                    Text("Complète le nom et une inspiration ou des mots-clés pour activer Générer.")
                        .font(.caption)
                        .foregroundStyle(palette.textTertiary)
                } else if !canStartProcess {
                    Text("Processus en cours — consulte le bandeau en haut de l'app.")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(palette.statusWarning)
                }
            }
            Spacer()
            GenerateButton(
                viewModel: viewModel,
                palette: palette,
                canGenerateFromDrafts: canGenerateFromDrafts,
                canStartProcess: canStartProcess,
                onGenerate: onGenerate
            )
        }
    }
}

private struct GenerateButton: View {
    @ObservedObject var viewModel: PlaylistBuilderViewModel
    let palette: ThemePalette
    let canGenerateFromDrafts: Bool
    let canStartProcess: Bool
    let onGenerate: () -> Void

    private var isDisabled: Bool {
        !canGenerateFromDrafts || viewModel.screenState == .generating || !canStartProcess
    }

    var body: some View {
        Button(action: onGenerate) {
            GenerateButtonLabel(isGenerating: viewModel.screenState == .generating)
        }
        .buttonStyle(.borderedProminent)
        .tint(palette.accentPrimary)
        .disabled(isDisabled)
        .opacity(isDisabled ? 0.55 : 1)
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
    var isMultiline: Bool = false

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
            AppKitTextField(
                placeholder: title,
                text: $text,
                isMultiline: isMultiline
            )
            .frame(maxWidth: .infinity, minHeight: isMultiline ? 64 : 28, alignment: .leading)
        }
    }
}

private struct ImportFailureView: View {
    let message: String
    let architectErrorDetail: String?
    let palette: ThemePalette
    let onReset: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Label("Import impossible", systemImage: "exclamationmark.triangle")
                .font(.title3.weight(.semibold))
                .foregroundStyle(palette.statusWarning)
            Text(message)
                .foregroundStyle(palette.textPrimary)
                .textSelection(.enabled)
            if ResonanceFeatureFlags.architectModeEnabled, let architectErrorDetail {
                Text(architectErrorDetail)
                    .font(.caption.monospaced())
                    .foregroundStyle(palette.textSecondary)
                    .textSelection(.enabled)
            }
            Button("Revenir à l'aperçu", action: onReset)
                .buttonStyle(.borderedProminent)
                .tint(palette.accentPrimary)
        }
        .padding(24)
        .background(palette.surface.opacity(0.98))
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        .overlay {
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .strokeBorder(palette.borderSubtle, lineWidth: 1)
        }
        .padding(24)
    }
}

private struct ExclusionEditorRow: View {
    @Binding var rule: ExclusionRule
    let palette: ThemePalette
    let autocompleteService: any AutocompleteServing
    let seedArtistName: String
    let seedArtistID: String
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
            ExclusionAutocompleteField(
                rule: $rule,
                palette: palette,
                autocompleteService: autocompleteService,
                seedArtistName: seedArtistName,
                seedArtistID: seedArtistID
            )
        }
    }
}
