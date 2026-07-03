import ResonanceDesign
import SwiftUI

struct ImportMetricsRow: View {
    let resolved: Int?
    let resolvedTotal: Int?
    let added: Int
    let skipped: Int
    let notFound: Int
    let errors: Int
    let palette: ThemePalette

    var body: some View {
        HStack(spacing: 10) {
            if let resolved, let resolvedTotal {
                metricChip("Résolus", value: resolved, total: resolvedTotal)
            }
            metricChip("Ajoutés", value: added)
            if skipped > 0 {
                metricChip("Ignorés", value: skipped)
            }
            metricChip("Introuv.", value: notFound)
            metricChip("Erreurs", value: errors)
        }
    }

    private func metricChip(_ title: String, value: Int, total: Int? = nil) -> some View {
        VStack(spacing: 2) {
            if let total {
                Text("\(value)/\(max(total, 1))")
                    .font(.caption.monospacedDigit().weight(.semibold))
            } else {
                Text("\(value)")
                    .font(.caption.monospacedDigit().weight(.semibold))
            }
            Text(title)
                .font(.caption2)
                .foregroundStyle(palette.textSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 8)
        .background(palette.backgroundSecondary)
        .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
    }
}
