import Foundation
import ResonanceCore

@MainActor
final class ImportViewModel: ObservableObject {
    enum ScreenState: Equatable {
        case idle
        case importing
        case waitingForManualAcquisition
        case report
        case failed(String)
    }

    @Published var screenState: ScreenState = .idle
    @Published var progress = ImportProgressSnapshot()
    @Published var manualPrompt: ManualAcquisitionPrompt?
    @Published var report: ImportResultState?
    @Published var architectErrorDetail: String?

    private let service: any PlaylistImportServing
    private var importSessionID: String?

    init(service: any PlaylistImportServing = MockPlaylistImportService()) {
        self.service = service
    }

    func importPlaylist(_ generationResult: PlaylistGenerationResult) async {
        beginImport(playlistName: generationResult.playlistName, totalTracks: generationResult.trackCount)

        do {
            let result = try await service.importPlaylist(generationResult, onEvent: importEventHandler)
            finishImport(with: result)
        } catch let error as PlaylistImportError {
            failImport(error)
        } catch {
            failImport(error)
        }
    }

    func confirmManualAcquisition() async {
        guard let importSessionID else {
            screenState = .failed("Session d'import introuvable.")
            return
        }
        screenState = .importing
        mutateProgress { snapshot in
            snapshot.currentStep = "Reprise après ajout manuel…"
            snapshot.lastActivityAt = .now
        }

        do {
            let result = try await service.continueManualAcquisition(
                importSessionID: importSessionID,
                onEvent: importEventHandler
            )
            finishImport(with: result)
        } catch let error as PlaylistImportError {
            failImport(error)
        } catch {
            failImport(error)
        }
    }

    func reset() {
        screenState = .idle
        progress = ImportProgressSnapshot()
        manualPrompt = nil
        report = nil
        importSessionID = nil
        architectErrorDetail = nil
    }

    private var importEventHandler: @Sendable (BridgeEventMessage) -> Void {
        { [weak self] event in
            Task { @MainActor in
                self?.handle(event: event)
            }
        }
    }

    private func beginImport(playlistName: String, totalTracks: Int) {
        screenState = .importing
        architectErrorDetail = nil
        manualPrompt = nil
        importSessionID = nil
        report = nil
        progress = ImportProgressSnapshot(
            playlistName: playlistName,
            totalTracks: totalTracks,
            currentStep: "Préparation de l'import…",
            diagnostics: ["Envoi de la commande import_playlist au moteur Python…"],
            lastActivityAt: .now
        )
    }

    private func finishImport(with result: ImportResultState) {
        if result.phase == .waitingForManualAcquisition {
            screenState = .waitingForManualAcquisition
            report = result
            return
        }
        mutateProgress { snapshot in
            snapshot.addedCount = result.addedCount
            snapshot.skippedCount = result.skippedCount
            snapshot.notFoundCount = result.notFoundCount
            snapshot.errorCount = result.errorCount
            snapshot.currentStep = finalStepLabel(for: result)
            snapshot.lastActivityAt = .now
        }
        report = result
        screenState = .report
    }

    private func failImport(_ error: PlaylistImportError) {
        architectErrorDetail = ImportErrorHumanizer.architectDetail(for: error)
        screenState = .failed(ImportErrorHumanizer.message(for: error))
    }

    private func failImport(_ error: Error) {
        architectErrorDetail = ImportErrorHumanizer.architectDetail(for: error)
        screenState = .failed(ImportErrorHumanizer.userMessage(for: error))
    }

    private func handle(event: BridgeEventMessage) {
        switch event.event {
        case .started:
            let message = startedMessage(from: event.payload)
            mutateProgress { snapshot in
                snapshot.currentStep = message
                snapshot.lastActivityAt = .now
                appendDiagnostic(message, to: &snapshot)
            }
        case .progress:
            mutateProgress { snapshot in
                if let phaseRaw = event.payload["phase"]?.stringValue,
                   let phase = ImportPhase(rawValue: phaseRaw) {
                    snapshot.phase = phase
                    snapshot.currentStep = stepLabel(for: phase)
                }
                snapshot.totalTracks = event.payload["total_tracks"]?.intValue ?? snapshot.totalTracks
                snapshot.processedTracks = event.payload["processed_tracks"]?.intValue ?? snapshot.processedTracks
                snapshot.currentTrackLabel = event.payload["current_track_label"]?.stringValue ?? snapshot.currentTrackLabel
                if let playlistName = event.payload["playlist_name"]?.stringValue, !playlistName.isEmpty {
                    snapshot.playlistName = playlistName
                }
                snapshot.addedCount = event.payload["added_count"]?.intValue ?? snapshot.addedCount
                snapshot.skippedCount = event.payload["skipped_count"]?.intValue ?? snapshot.skippedCount
                snapshot.notFoundCount = event.payload["not_found_count"]?.intValue ?? snapshot.notFoundCount
                snapshot.errorCount = event.payload["error_count"]?.intValue ?? snapshot.errorCount
                snapshot.lastActivityAt = .now
            }
            if let sessionID = event.payload["import_session_id"]?.stringValue {
                importSessionID = sessionID
            }
        case .diagnostic:
            guard let message = event.payload["message"]?.stringValue else { return }
            mutateProgress { snapshot in
                snapshot.currentStep = message
                updateRunningCounts(from: message, snapshot: &snapshot)
                if shouldSurfaceDiagnostic(message) {
                    appendDiagnostic(message, to: &snapshot)
                }
                snapshot.lastActivityAt = .now
            }
        case .error:
            guard let message = event.payload["message"]?.stringValue, !message.isEmpty else { return }
            mutateProgress { snapshot in
                snapshot.errorCount += 1
                appendDiagnostic(message, to: &snapshot, force: true)
                snapshot.lastActivityAt = .now
            }
            architectErrorDetail = message
            screenState = .failed(ImportErrorHumanizer.humanizeBridgeMessage(message))
        case .manualAcquisitionRequired:
            importSessionID = event.payload["import_session_id"]?.stringValue
            manualPrompt = ManualAcquisitionPrompt(
                token: event.payload["token"]?.stringValue ?? "",
                artist: event.payload["artist"]?.stringValue ?? "",
                title: event.payload["title"]?.stringValue ?? "",
                instructions: event.payload["instructions"]?.stringValue ?? "",
                catalogLabel: event.payload["catalog_label"]?.stringValue ?? ""
            )
            mutateProgress { snapshot in
                snapshot.currentStep = "En attente d'ajout manuel dans Music.app"
                snapshot.lastActivityAt = .now
            }
            screenState = .waitingForManualAcquisition
        default:
            break
        }
    }

    private func mutateProgress(_ block: (inout ImportProgressSnapshot) -> Void) {
        var snapshot = progress
        block(&snapshot)
        progress = snapshot
    }

    private func appendDiagnostic(
        _ message: String,
        to snapshot: inout ImportProgressSnapshot,
        force: Bool = false
    ) {
        guard !message.isEmpty else { return }
        if !force, snapshot.diagnostics.last == message {
            return
        }
        if snapshot.diagnostics.count >= ImportProgressSnapshot.maxVisibleDiagnostics {
            snapshot.diagnostics.removeFirst(
                snapshot.diagnostics.count - ImportProgressSnapshot.maxVisibleDiagnostics + 1
            )
        }
        snapshot.diagnostics.append(message)
    }

    private func shouldSurfaceDiagnostic(_ message: String) -> Bool {
        let lowered = message.lowercased()
        if message.hasPrefix("[stderr]") || message.hasPrefix("[bridge error]") {
            return lowered.contains("failed")
                || lowered.contains("error")
                || lowered.contains("échec")
                || lowered.contains("introuvable")
        }
        return lowered.contains("music.app")
            || lowered.contains("résolution")
            || lowered.contains("resolve")
            || lowered.contains("synchronis")
            || lowered.contains("création")
            || lowered.contains("commande")
            || lowered.contains("livraison")
            || lowered.contains("deliver")
            || lowered.contains("introuvable")
            || lowered.contains("cache")
    }

    private func updateRunningCounts(from message: String, snapshot: inout ImportProgressSnapshot) {
        let lowered = message.lowercased()
        if lowered.contains("introuvable") || lowered.contains("not found") {
            snapshot.notFoundCount += 1
        }
    }

    private func startedMessage(from payload: BridgeJSONObject) -> String {
        if let message = payload["message"]?.stringValue, !message.isEmpty {
            return message
        }
        if let command = payload["command"]?.stringValue, !command.isEmpty {
            return "Commande bridge envoyée : \(command)"
        }
        return "Import démarré"
    }

    private func stepLabel(for phase: ImportPhase) -> String {
        switch phase {
        case .resolving: return "Résolution des morceaux dans Apple Music…"
        case .acquiring: return "Acquisition catalogue…"
        case .delivering: return "Ajout à la playlist Apple Music…"
        case .waitingForManualAcquisition: return "En attente d'ajout manuel"
        default: return "Import en cours…"
        }
    }

    private func finalStepLabel(for result: ImportResultState) -> String {
        switch result.phase {
        case .completed:
            return "Playlist créée — \(result.addedCount) morceau(x) ajouté(s)"
        case .partialSuccess:
            return "Import partiel — \(result.addedCount) ajouté(s), \(result.notFoundCount) introuvable(s), \(result.skippedCount) ignoré(s)"
        case .failed:
            return "Import échoué"
        default:
            return "Import terminé"
        }
    }
}
