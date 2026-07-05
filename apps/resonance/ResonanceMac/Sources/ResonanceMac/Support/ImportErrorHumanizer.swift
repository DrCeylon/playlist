import Foundation
import ResonanceCore

enum ImportErrorHumanizer {
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
            return "Erreur inattendue pendant l'import."
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
        let lowered = message.lowercased()
        if lowered.contains("resolution outcomes")
            || lowered.contains("do not match playlist track count")
            || lowered.contains("ne correspondent pas à la playlist") {
            return "L'import n'a pas pu finaliser tous les morceaux. Relance l'import ou régénère la playlist depuis le formulaire."
        }
        if lowered.contains("not found") || lowered.contains("introuvable") {
            return "Morceau introuvable dans Apple Music : \(message)"
        }
        if lowered.contains("already") || lowered.contains("déjà") || lowered.contains("skipped") {
            return "Morceau déjà présent ou ignoré : \(message)"
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
        return message
    }
}
