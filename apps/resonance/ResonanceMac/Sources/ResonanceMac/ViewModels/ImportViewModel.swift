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

    private let service: any PlaylistImportServing
    private var importSessionID: String?

    init(service: any PlaylistImportServing = MockPlaylistImportService()) {
        self.service = service
    }

    func importPlaylist(_ generationResult: PlaylistGenerationResult) async {
        screenState = .importing
        progress = ImportProgressSnapshot(playlistName: generationResult.playlistName)
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
            report = result
            screenState = .report
        } catch let error as PlaylistImportError {
            screenState = .failed(message(for: error))
        } catch {
            screenState = .failed("L'import a échoué.")
        }
    }

    func confirmManualAcquisition() async {
        guard let importSessionID else {
            screenState = .failed("Session d'import introuvable.")
            return
        }
        screenState = .importing
        do {
            let result = try await service.continueManualAcquisition(importSessionID: importSessionID)
                if result.phase == .waitingForManualAcquisition {
                    screenState = .waitingForManualAcquisition
                    report = result
                    return
                }
                report = result
                screenState = .report
        } catch let error as PlaylistImportError {
            screenState = .failed(message(for: error))
        } catch {
            screenState = .failed("La reprise d'import a échoué.")
        }
    }

    func reset() {
        screenState = .idle
        progress = ImportProgressSnapshot()
        manualPrompt = nil
        report = nil
        importSessionID = nil
    }

    private func handle(event: BridgeEventMessage) {
        switch event.event {
        case .progress:
            if let phaseRaw = event.payload["phase"] as? String,
               let phase = ImportPhase(rawValue: phaseRaw) {
                progress.phase = phase
            }
            progress.totalTracks = event.payload["total_tracks"] as? Int ?? progress.totalTracks
            progress.processedTracks = event.payload["processed_tracks"] as? Int ?? progress.processedTracks
            progress.currentTrackLabel = event.payload["current_track_label"] as? String ?? progress.currentTrackLabel
            if let sessionID = event.payload["import_session_id"] as? String {
                importSessionID = sessionID
            }
        case .diagnostic:
            if let message = event.payload["message"] as? String {
                progress.diagnostics.append(message)
            }
        case .manualAcquisitionRequired:
            importSessionID = event.payload["import_session_id"] as? String
            manualPrompt = ManualAcquisitionPrompt(
                token: event.payload["token"] as? String ?? "",
                artist: event.payload["artist"] as? String ?? "",
                title: event.payload["title"] as? String ?? "",
                instructions: event.payload["instructions"] as? String ?? "",
                catalogLabel: event.payload["catalog_label"] as? String ?? ""
            )
            screenState = .waitingForManualAcquisition
        default:
            break
        }
    }

    private func message(for error: PlaylistImportError) -> String {
        switch error {
        case .bridgeUnavailable:
            return "Le moteur Python est indisponible. Vérifie l'installation du projet."
        case .timeout:
            return "Le moteur Python n'a pas répondu à temps."
        case .invalidResponse:
            return "Réponse bridge invalide."
        case .bridge(let payload):
            return payload.message
        }
    }
}
