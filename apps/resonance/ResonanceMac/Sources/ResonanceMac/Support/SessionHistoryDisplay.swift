import Foundation
import ResonanceCore

enum SessionHistoryDisplay {
    static func statusLabel(for status: SessionHistoryStatus) -> String {
        switch status {
        case .generated: return "Générée"
        case .imported: return "Importée"
        case .partialSuccess: return "Partielle"
        case .failed: return "Échec"
        case .waitingForManualAcquisition: return "Action manuelle requise"
        }
    }

    static func rowSubtitle(for session: SessionHistorySummary) -> String {
        switch session.status {
        case .generated:
            return "\(session.trackCount) morceau(x) généré(s)"
        case .imported:
            return "\(session.addedCount) ajouté(s) dans Apple Music"
        case .partialSuccess:
            return "Import partiel — \(session.addedCount) ajouté(s), \(session.notFoundCount) introuvable(s)"
        case .failed:
            return "La génération ou l'import a échoué"
        case .waitingForManualAcquisition:
            return "Ajout manuel requis dans Music.app"
        }
    }
}
