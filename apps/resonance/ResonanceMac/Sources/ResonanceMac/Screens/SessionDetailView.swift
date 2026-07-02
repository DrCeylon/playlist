import ResonanceCore
import ResonanceDesign
import SwiftUI

struct SessionDetailView: View {
    let detail: SessionHistoryDetail?
    let onReplay: () -> Void
    let onReimport: () -> Void
    let onExport: () -> Void
    @EnvironmentObject private var themeManager: ThemeManager

    var body: some View {
        let palette = ThemePalette(theme: themeManager.active)
        VStack(alignment: .leading, spacing: 12) {
            Text("Détail session")
                .font(.headline)
                .foregroundStyle(palette.textPrimary)

            if let detail {
                Text(detail.summary.playlistName)
                    .font(.title3.weight(.semibold))
                Text("Statut : \(detail.summary.status.rawValue)")
                    .font(.caption)
                    .foregroundStyle(palette.textSecondary)

                Group {
                    Text("Requête : \(detail.generationRequest.isEmpty ? "—" : "disponible")")
                    Text("Preview : \(detail.generationResult.isEmpty ? "—" : "disponible")")
                    Text("Import : \(detail.importResult.isEmpty ? "—" : "disponible")")
                    Text("Rapport texte : \(detail.summary.textReportPath.isEmpty ? "—" : detail.summary.textReportPath)")
                    Text("Rapport JSON : \(detail.summary.jsonReportPath.isEmpty ? "—" : detail.summary.jsonReportPath)")
                }
                .font(.caption)
                .foregroundStyle(palette.textSecondary)

                HStack {
                    Button("Relancer génération", action: onReplay)
                        .buttonStyle(.borderedProminent)
                        .tint(palette.accentPrimary)
                    Button("Réimporter", action: onReimport)
                        .buttonStyle(.bordered)
                    Button("Exporter", action: onExport)
                        .buttonStyle(.bordered)
                }
            } else {
                Text("Sélectionne une session pour afficher les détails.")
                    .foregroundStyle(palette.textSecondary)
            }
        }
        .padding(16)
        .background(palette.backgroundSecondary)
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
    }
}

