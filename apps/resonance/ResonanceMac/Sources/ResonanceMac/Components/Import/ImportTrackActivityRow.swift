import ResonanceCore
import ResonanceDesign
import SwiftUI

struct ImportTrackActivityRow: View {
    let activity: ImportTrackActivity
    let palette: ThemePalette

    var body: some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: iconName)
                .foregroundStyle(iconColor)
                .frame(width: 18)

            VStack(alignment: .leading, spacing: 4) {
                SelectableText(
                    text: activity.displayLabel,
                    font: activity.isCurrent ? .body.weight(.semibold) : .body,
                    foreground: palette.textPrimary
                )
                if !activity.album.isEmpty {
                    SelectableText(
                        text: activity.album,
                        font: .caption,
                        foreground: palette.textSecondary
                    )
                }
                SelectableText(
                    text: stepLabel,
                    font: .caption,
                    foreground: activity.isCurrent ? palette.accentPrimary : palette.textSecondary
                )
                if !activity.message.isEmpty, activity.message != stepLabel {
                    SelectableText(
                        text: activity.message,
                        font: .caption2,
                        foreground: palette.textTertiary
                    )
                }
            }
            Spacer(minLength: 0)
        }
        .padding(.vertical, 6)
        .opacity(activity.isCurrent ? 1 : 0.82)
    }

    private var stepLabel: String {
        ImportTrackActivityFormatter.stepLabel(activity.step, status: activity.status)
    }

    private var iconName: String {
        ImportTrackActivityFormatter.iconName(status: activity.status, step: activity.step)
    }

    private var iconColor: Color {
        ImportTrackActivityFormatter.iconColor(
            status: activity.status,
            step: activity.step,
            palette: palette
        )
    }
}

enum ImportTrackActivityFormatter {
    static func stepLabel(_ step: ImportTrackStep, status: ImportTrackStatus) -> String {
        switch status {
        case .added: return "✓ Ajouté"
        case .skipped: return "Ignoré"
        case .notFound: return "Introuvable"
        case .error: return "Erreur"
        case .acquiring: return "Acquisition manuelle"
        case .pending:
            break
        }
        switch step {
        case .searching: return "Recherche…"
        case .resolving: return "Résolution…"
        case .acquiring: return "Acquisition…"
        case .adding: return "Ajout…"
        case .completed: return "Terminé"
        case .pending: return "En attente"
        }
    }

    static func iconName(status: ImportTrackStatus, step: ImportTrackStep) -> String {
        switch status {
        case .added: return "checkmark.circle.fill"
        case .skipped: return "arrow.uturn.right.circle"
        case .notFound: return "questionmark.circle"
        case .error: return "xmark.octagon.fill"
        case .acquiring: return "hand.point.up.left.fill"
        case .pending:
            break
        }
        switch step {
        case .searching, .resolving: return "magnifyingglass"
        case .acquiring, .adding: return "arrow.down.circle"
        case .completed: return "checkmark.circle"
        case .pending: return "circle"
        }
    }

    static func iconColor(status: ImportTrackStatus, step: ImportTrackStep, palette: ThemePalette) -> Color {
        switch status {
        case .added: return palette.statusSuccess
        case .skipped: return palette.textSecondary
        case .notFound: return palette.statusWarning
        case .error: return palette.statusWarning
        case .acquiring: return palette.accentPrimary
        case .pending:
            break
        }
        return step == .completed ? palette.statusSuccess : palette.accentPrimary
    }
}
