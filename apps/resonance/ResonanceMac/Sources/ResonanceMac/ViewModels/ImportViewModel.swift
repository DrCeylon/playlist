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
        progress = ImportProgressSnapshot(
            playlistName: generationResult.playlistName,
            totalTracks: generationResult.trackCount,
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
        case .started:
            appendDiagnostic(startedMessage(from: event.payload))
        case .progress:
            if let phaseRaw = event.payload["phase"]?.stringValue,
               let phase = ImportPhase(rawValue: phaseRaw) {
                progress.phase = phase
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
        case .diagnostic:
            if let message = event.payload["message"]?.stringValue {
                appendDiagnostic(message)
            }
        case .error:
            if let message = event.payload["message"]?.stringValue, !message.isEmpty {
                screenState = .failed(message)
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
            screenState = .waitingForManualAcquisition
        default:
            break
        }
    }

    private func appendDiagnostic(_ message: String) {
        guard !message.isEmpty else { return }
        if progress.diagnostics.last != message {
            progress.diagnostics.append(message)
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

    private func message(for error: PlaylistImportError) -> String {
        switch error {
        case .bridgeUnavailable:
            return "Le moteur Python est indisponible. Vérifie l'installation du projet."
        case .timeout:
            return "Le moteur Python n'a pas répondu à temps. Vérifie que Music.app est ouvert et que Resonance est autorisé dans Réglages > Confidentialité > Automatisation."
        case .invalidResponse:
            return "Réponse bridge invalide."
        case .bridge(let payload):
            return humanizeBridgeMessage(payload.message)
        }
    }

    private func humanizeBridgeMessage(_ message: String) -> String {
        let lowered = message.lowercased()
        if lowered.contains("not authorized")
            || lowered.contains("automation")
            || lowered.contains("-1743")
            || lowered.contains("autorisation") {
            return "Autorise Resonance ou Terminal à contrôler Music dans Réglages > Confidentialité > Automatisation."
        }
        return message
    }
}
