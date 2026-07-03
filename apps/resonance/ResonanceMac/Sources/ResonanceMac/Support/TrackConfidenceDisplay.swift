import ResonanceCore

enum TrackConfidenceDisplay {
    static func label(for score: Double) -> String {
        let percent = normalizedPercent(score)
        switch percent {
        case 80...:
            return "Confiance élevée"
        case 50..<80:
            return "Confiance moyenne"
        default:
            return "Faible confiance"
        }
    }

    static func averageLabel(for score: Double) -> String {
        "Pertinence moyenne : \(label(for: score))"
    }

    private static func normalizedPercent(_ score: Double) -> Double {
        score > 1.0 ? score : score * 100
    }
}
