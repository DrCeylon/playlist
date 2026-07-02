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
        screenState = .importing
        architectErrorDetail = nil
        progress = ImportProgressSnapshot(
            playlistName: generationResult.playlistName,
            totalTracks: generationResult.trackCount,
            currentStep: "Préparation de l'import…",
            diagnostics: ["Envoi de la commande import_playlist au moteur Python…"]
        )
        manualPrompt = nil
        importSessionID = nil
        report = nil

        do {
            let result = try await service.importPlaylist(generationResult) { [weak self] event in
                Task { @MainActor in
                    self?.handle(event: event)
                }
            }
            if result.phase == .waitingForManualAcquisition {
                screenState = .waitingForManualAcquisition
                report = result
                return
            }
            applyFinalCounts(from: result)
            report = result
            screenState = .report
        } catch let error as PlaylistImportError {
            architectErrorDetail = ImportErrorHumanizer.architectDetail(for: error)
            screenState = .failed(ImportErrorHumanizer.message(for: error))
        } catch {
            architectErrorDetail = ImportErrorHumanizer.architectDetail(for: error)
            screenState = .failed(ImportErrorHumanizer.userMessage(for: error))
        }
    }

    func confirmManualAcquisition() async {
        guard let importSessionID else {
            screenState = .failed("Session d'import introuvable.")
            return
        }
        screenState = .importing
        progress.currentStep = "Reprise après ajout manuel…"
        do {
            let result = try await service.continueManualAcquisition(importSessionID: importSessionID)
            if result.phase == .waitingForManualAcquisition {
                screenState = .waitingForManualAcquisition
                report = result
                return
            }
            applyFinalCounts(from: result)
            report = result
            screenState = .report
        } catch let error as PlaylistImportError {
            architectErrorDetail = ImportErrorHumanizer.architectDetail(for: error)
            screenState = .failed(ImportErrorHumanizer.message(for: error))
        } catch {
            architectErrorDetail = ImportErrorHumanizer.architectDetail(for: error)
            screenState = .failed(ImportErrorHumanizer.userMessage(for: error))
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

    private func handle(event: BridgeEventMessage) {
        switch event.event {
        case .started:
            let message = startedMessage(from: event.payload)
            progress.currentStep = message
            appendDiagnostic(message)
        case .progress:
            if let phaseRaw = event.payload["phase"]?.stringValue,
               let phase = ImportPhase(rawValue: phaseRaw) {
                progress.phase = phase
                progress.currentStep = stepLabel(for: phase)
            }
            progress.totalTracks = event.payload["total_tracks"]?.intValue ?? progress.totalTracks
            progress.processedTracks = event.payload["processed_tracks"]?.intValue ?? progress.processedTracks
            progress.currentTrackLabel = event.payload["current_track_label"]?.stringValue ?? progress.currentTrackLabel
            if let playlistName = event.payload["playlist_name"]?.stringValue, !playlistName.isEmpty {
                progress.playlistName = playlistName
            }
            if let sessionID = event.payload["import_session_id"]?.stringValue {
                importSessionID = sessionID
            }
            progress.addedCount = event.payload["added_count"]?.intValue ?? progress.addedCount
            progress.skippedCount = event.payload["skipped_count"]?.intValue ?? progress.skippedCount
            progress.notFoundCount = event.payload["not_found_count"]?.intValue ?? progress.notFoundCount
            progress.errorCount = event.payload["error_count"]?.intValue ?? progress.errorCount
        case .diagnostic:
            if let message = event.payload["message"]?.stringValue {
                progress.currentStep = message
                updateRunningCounts(from: message)
                if shouldSurfaceDiagnostic(message) {
                    appendDiagnostic(message)
                }
            }
        case .error:
            if let message = event.payload["message"]?.stringValue, !message.isEmpty {
                progress.errorCount += 1
                appendDiagnostic(message, force: true)
                architectErrorDetail = message
                screenState = .failed(ImportErrorHumanizer.humanizeBridgeMessage(message))
            }
        case .manualAcquisitionRequired:
            importSessionID = event.payload["import_session_id"]?.stringValue
            manualPrompt = ManualAcquisitionPrompt(
                token: event.payload["token"]?.stringValue ?? "",
                artist: event.payload["artist"]?.stringValue ?? "",
                title: event.payload["title"]?.stringValue ?? "",
                instructions: event.payload["instructions"]?.stringValue ?? "",
                catalogLabel: event.payload["catalog_label"]?.stringValue ?? ""
            )
            progress.currentStep = "En attente d'ajout manuel dans Music.app"
            screenState = .waitingForManualAcquisition
        default:
            break
        }
    }

    private func applyFinalCounts(from result: ImportResultState) {
        progress.addedCount = result.addedCount
        progress.skippedCount = result.skippedCount
        progress.notFoundCount = result.notFoundCount
        progress.errorCount = result.errorCount
        progress.currentStep = finalStepLabel(for: result)
    }

    private func appendDiagnostic(_ message: String, force: Bool = false) {
        guard !message.isEmpty else { return }
        if !force, progress.diagnostics.last == message {
            return
        }
        if progress.diagnostics.count >= ImportProgressSnapshot.maxVisibleDiagnostics {
            progress.diagnostics.removeFirst(progress.diagnostics.count - ImportProgressSnapshot.maxVisibleDiagnostics + 1)
        }
        progress.diagnostics.append(message)
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

    private func updateRunningCounts(from message: String) {
        let lowered = message.lowercased()
        if lowered.contains("introuvable") || lowered.contains("not found") {
            progress.notFoundCount += 1
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
