import Combine
import Foundation
import ResonanceCore

@MainActor
final class AppWorkflowCoordinator: ObservableObject {
    struct BannerPresentation: Equatable {
        enum Phase: Equatable {
            case inProgress
            case completed
            case failed
        }

        enum ProcessKind: Equatable {
            case generation
            case importProcess
        }

        let phase: Phase
        let kind: ProcessKind
        let playlistName: String
        let step: String
        let detail: String
        let progressLabel: String
        let progressRatio: Double?
        let substeps: [String]
    }

    @Published private(set) var banner: BannerPresentation?
    @Published var activeRoute: SidebarItem = .newPlaylist
    @Published var pendingEditRequest: PlaylistGenerationRequest?

    let playlistBuilder: PlaylistBuilderViewModel
    let importWorkflow: ImportViewModel
    let smartInputEngines: SmartInputFormEngines

    private var cancellables = Set<AnyCancellable>()

    init(
        generationService: any PlaylistGenerationServing = PythonEngineBridgeService(),
        importService: any PlaylistImportServing = PythonEngineBridgeService(),
        autocompleteService: (any AutocompleteServing)? = nil
    ) {
        let resolvedAutocomplete: any AutocompleteServing = autocompleteService
            ?? (generationService as? AutocompleteServing)
            ?? MockAutocompleteService()
        playlistBuilder = PlaylistBuilderViewModel(service: generationService)
        importWorkflow = ImportViewModel(service: importService)
        smartInputEngines = SmartInputFormEngines(autocompleteService: resolvedAutocomplete)
        bindWorkflowObservation()
    }

    var isProcessRunning: Bool {
        if playlistBuilder.screenState == .generating {
            return true
        }
        switch importWorkflow.screenState {
        case .importing, .waitingForManualAcquisition:
            return true
        default:
            return false
        }
    }

    func canStartProcess() -> Bool {
        !isProcessRunning
    }

    var processBlockingLabel: String? {
        isProcessRunning ? "Processus en cours" : nil
    }

    func isManagingSession(_ detail: SessionHistoryDetail) -> Bool {
        matchesActivePlaylist(detail.summary.playlistName)
    }

    func matchesActivePlaylist(_ playlistName: String) -> Bool {
        let trimmed = playlistName.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return false }

        if importWorkflow.progress.playlistName == trimmed {
            return isImportWorkflowActive
        }
        if importWorkflow.report?.playlistName == trimmed, isImportWorkflowActive {
            return true
        }
        if playlistBuilder.screenState == .generating,
           (playlistBuilder.name == trimmed || playlistBuilder.previewResult?.playlistName == trimmed) {
            return true
        }
        return false
    }

    private var isImportWorkflowActive: Bool {
        switch importWorkflow.screenState {
        case .importing, .waitingForManualAcquisition, .report, .failed:
            return true
        case .idle:
            return false
        }
    }

    func requestEditFromHistory(_ request: PlaylistGenerationRequest) {
        pendingEditRequest = request
        activeRoute = .newPlaylist
    }

    func startImport(from generation: PlaylistGenerationResult) async {
        guard canStartProcess() else { return }
        activeRoute = .newPlaylist
        await importWorkflow.importPlaylist(generation)
    }

    func applyPendingEditIfNeeded() {
        guard let request = pendingEditRequest else { return }
        playlistBuilder.loadFromHistory(request)
        smartInputEngines.syncFromViewModel(playlistBuilder)
        pendingEditRequest = nil
        activeRoute = .newPlaylist
    }

    func dismissBanner() {
        banner = nil
    }

    private func bindWorkflowObservation() {
        importWorkflow.$screenState
            .combineLatest(importWorkflow.$progress, importWorkflow.$report)
            .receive(on: RunLoop.main)
            .sink { [weak self] state, progress, report in
                self?.syncBannerFromImport(state: state, progress: progress, report: report)
            }
            .store(in: &cancellables)

        playlistBuilder.$screenState
            .combineLatest(playlistBuilder.$previewResult, playlistBuilder.$name)
            .receive(on: RunLoop.main)
            .sink { [weak self] state, preview, name in
                self?.syncBannerFromBuilder(state: state, preview: preview, name: name)
            }
            .store(in: &cancellables)
    }

    private func syncBannerFromImport(
        state: ImportViewModel.ScreenState,
        progress: ImportProgressSnapshot,
        report: ImportResultState?
    ) {
        let playlistName = progress.playlistName.isEmpty
            ? (report?.playlistName ?? "Playlist")
            : progress.playlistName

        switch state {
        case .importing:
            banner = BannerPresentation(
                phase: .inProgress,
                kind: .importProcess,
                playlistName: playlistName,
                step: progress.currentStep.isEmpty ? "Import en cours…" : progress.currentStep,
                detail: importDetail(from: progress),
                progressLabel: importProgressLabel(from: progress),
                progressRatio: progress.totalTracks > 0 ? progress.progressRatio : nil,
                substeps: progress.diagnostics
            )
        case .waitingForManualAcquisition:
            banner = BannerPresentation(
                phase: .inProgress,
                kind: .importProcess,
                playlistName: playlistName,
                step: "Ajout manuel requis — ouvrez Music.app manuellement",
                detail: progress.currentTrackLabel.isEmpty
                    ? "Resonance n'ouvre plus Music.app automatiquement."
                    : progress.currentTrackLabel,
                progressLabel: importProgressLabel(from: progress),
                progressRatio: progress.totalTracks > 0 ? progress.progressRatio : nil,
                substeps: progress.diagnostics
            )
        case .report:
            banner = BannerPresentation(
                phase: .completed,
                kind: .importProcess,
                playlistName: playlistName,
                step: "Import terminé — touche pour voir le rapport",
                detail: importSummary(from: report),
                progressLabel: "",
                progressRatio: 1,
                substeps: []
            )
        case .failed(let message):
            banner = BannerPresentation(
                phase: .failed,
                kind: .importProcess,
                playlistName: playlistName,
                step: ImportErrorHumanizer.humanizeBridgeMessage(message),
                detail: progress.currentTrackLabel,
                progressLabel: importProgressLabel(from: progress),
                progressRatio: nil,
                substeps: progress.diagnostics
            )
        case .idle:
            if importWorkflow.screenState == .idle {
                clearImportBannerIfNeeded()
            }
        }
    }

    private func syncBannerFromBuilder(
        state: PlaylistBuilderViewModel.ScreenState,
        preview: PlaylistGenerationResult?,
        name: String
    ) {
        guard !isImportBannerActive else { return }

        let playlistName = preview?.playlistName ?? (name.isEmpty ? "Playlist" : name)
        switch state {
        case .generating:
            banner = BannerPresentation(
                phase: .inProgress,
                kind: .generation,
                playlistName: playlistName,
                step: "Génération en cours…",
                detail: "Le moteur Python compose la playlist.",
                progressLabel: "",
                progressRatio: nil,
                substeps: []
            )
        case .preview:
            banner = BannerPresentation(
                phase: .completed,
                kind: .generation,
                playlistName: playlistName,
                step: "Aperçu prêt — touche pour reprendre",
                detail: preview.map { "\($0.trackCount) morceau(x) · score moyen \(String(format: "%.2f", $0.averageScore))" } ?? "",
                progressLabel: "",
                progressRatio: 1,
                substeps: []
            )
        case .editing:
            if playlistBuilder.screenState == .editing, importWorkflow.screenState == .idle {
                clearGenerationBannerIfNeeded()
            }
        }
    }

    private var isImportBannerActive: Bool {
        switch importWorkflow.screenState {
        case .importing, .waitingForManualAcquisition, .report, .failed:
            return true
        case .idle:
            return false
        }
    }

    private func clearImportBannerIfNeeded() {
        guard banner?.kind == .importProcess else { return }
        if playlistBuilder.screenState != .generating {
            banner = nil
        }
    }

    private func clearGenerationBannerIfNeeded() {
        guard banner?.kind == .generation else { return }
        banner = nil
    }

    private func importProgressLabel(from progress: ImportProgressSnapshot) -> String {
        guard progress.totalTracks > 0 else { return "" }
        if progress.phase == .delivering {
            return "Étape 2/2 · \(progress.addedCount + progress.skippedCount + progress.notFoundCount + progress.errorCount)/\(progress.totalTracks) synchronisé(s)"
        }
        return "Étape 1/2 · \(progress.processedTracks)/\(progress.totalTracks) morceau(x)"
    }

    private func importDetail(from progress: ImportProgressSnapshot) -> String {
        if !progress.currentTrackLabel.isEmpty {
            return progress.currentTrackLabel
        }
        return progress.phaseLabel
    }

    private func importSummary(from report: ImportResultState?) -> String {
        guard let report else { return "" }
        return "+\(report.addedCount) ajouté(s) · \(report.notFoundCount) introuvable(s) · \(report.errorCount) erreur(s)"
    }
}
