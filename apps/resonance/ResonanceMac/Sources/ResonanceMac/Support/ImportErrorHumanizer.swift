import Foundation
import ResonanceCore

enum ImportErrorHumanizer {
    static let importPreparationFailure = """
    L'importation a échoué pendant la préparation. Vous pouvez réessayer ou consulter le détail technique.
    """

    static let genericFailure = """
    Une erreur interne s'est produite. Réessayez ou consultez le diagnostic technique.
    """

    static func userMessage(for error: Error) -> String {
        if let importError = error as? PlaylistImportError {
            return message(for: importError)
        }
        if let bridgeError = error as? BridgeClientError {
            return message(for: bridgeError)
        }
        if error is DecodingError {
            return "Réponse bridge invalide. Relance l'import ou vérifie que Music.app répond correctement."
        }
        let nsError = error as NSError
        if nsError.domain == NSCocoaErrorDomain && nsError.code == 3840 {
            return "Réponse bridge invalide (format JSON incorrect)."
        }
        if nsError.domain == NSCocoaErrorDomain {
            return genericFailure
        }
        return "L'import a échoué. Vérifie Music.app et les autorisations Automatisation."
    }

    static func architectDetail(for error: Error) -> String? {
        if let importError = error as? PlaylistImportError {
            return String(describing: importError)
        }
        if let bridgeError = error as? BridgeClientError {
            return String(describing: bridgeError)
        }
        return String(describing: error)
    }

    static func message(for error: PlaylistImportError) -> String {
        switch error {
        case .bridgeUnavailable:
            return "Le moteur Python est indisponible. Vérifie l'installation du projet."
        case .timeout:
            return "Music.app n'a pas répondu à temps. Ouvre Music.app et autorise Resonance dans Réglages Système > Confidentialité et sécurité > Automatisation."
        case .invalidResponse:
            return "Réponse bridge invalide. Relance l'import ; si le problème persiste, passe en mode Architecte pour le détail technique."
        case .bridge(let payload):
            return humanizeBridgeMessage(payload.message)
        }
    }

    private static func message(for error: BridgeClientError) -> String {
        switch error {
        case .processUnavailable, .bridgeUnavailable:
            return "Le moteur Python est indisponible."
        case .timeout:
            return "Music.app n'a pas répondu à temps."
        case .invalidResponse:
            return "Réponse bridge invalide."
        case .bridge(let payload):
            return humanizeBridgeMessage(payload.message)
        }
    }

    static func humanizeBridgeMessage(_ message: String) -> String {
        if isTechnicalErrorMessage(message) {
            return importPreparationFailure
        }

        let lowered = message.lowercased()
        if lowered.contains("not found") || lowered.contains("introuvable") {
            return "Morceau introuvable dans Apple Music."
        }
        if lowered.contains("already") || lowered.contains("déjà") || lowered.contains("skipped") {
            return "Morceau déjà présent ou ignoré."
        }
        if lowered.contains("not authorized")
            || lowered.contains("automation")
            || lowered.contains("-1743")
            || lowered.contains("autorisation") {
            return "Autorise Resonance ou Python à contrôler Music dans Réglages Système > Confidentialité et sécurité > Automatisation."
        }
        if lowered.contains("timeout") || lowered.contains("timed out") {
            return "Music.app n'a pas répondu à temps. Ouvre Music.app puis relance l'import."
        }
        if lowered.contains("importation a échoué") || lowered.contains("erreur interne") {
            return message
        }
        return message
    }

    static func isTechnicalErrorMessage(_ message: String) -> Bool {
        let lowered = message.lowercased()
        let markers = [
            "cannot access local variable",
            "unboundlocalerror",
            "traceback",
            "nameerror",
            "attributeerror",
            "typeerror",
            "file \"",
            "line ",
            "where it is not associated with a value",
        ]
        return markers.contains { lowered.contains($0) }
    }
}
