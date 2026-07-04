import ResonanceDesign
import SwiftUI

struct WorkflowBannerView: View {
    let presentation: AppWorkflowCoordinator.BannerPresentation
    let palette: ThemePalette
    let onTap: () -> Void
    let onDismiss: () -> Void

    var body: some View {
        Button(action: onTap) {
            HStack(spacing: 12) {
                leadingIcon
                VStack(alignment: .leading, spacing: 2) {
                    Text(title)
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(palette.textPrimary)
                    Text(presentation.step)
                        .font(.caption)
                        .foregroundStyle(palette.textSecondary)
                        .lineLimit(2)
                }
                Spacer(minLength: 0)
                if presentation.phase == .completed || presentation.phase == .failed {
                    Button(action: onDismiss) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(palette.textTertiary)
                    }
                    .buttonStyle(.borderless)
                } else {
                    ProgressView()
                        .controlSize(.small)
                        .tint(accentColor)
                }
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 10)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(backgroundColor)
            .overlay(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .stroke(borderColor, lineWidth: 1)
            )
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
        }
        .buttonStyle(.plain)
    }

    private var title: String {
        let kindLabel = presentation.kind == .generation ? "Génération" : "Import"
        return "\(kindLabel) — \(presentation.playlistName)"
    }

    private var accentColor: Color {
        switch presentation.phase {
        case .inProgress:
            return palette.statusInfo
        case .completed:
            return palette.statusSuccess
        case .failed:
            return palette.statusWarning
        }
    }

    private var backgroundColor: Color {
        switch presentation.phase {
        case .inProgress:
            return palette.statusInfo.opacity(0.14)
        case .completed:
            return palette.statusSuccess.opacity(0.12)
        case .failed:
            return palette.statusWarning.opacity(0.12)
        }
    }

    private var borderColor: Color {
        accentColor.opacity(0.35)
    }

    @ViewBuilder
    private var leadingIcon: some View {
        switch presentation.phase {
        case .inProgress:
            Image(systemName: presentation.kind == .generation ? "sparkles" : "arrow.down.circle")
                .foregroundStyle(palette.statusInfo)
        case .completed:
            Image(systemName: "checkmark.circle.fill")
                .foregroundStyle(palette.statusSuccess)
        case .failed:
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundStyle(palette.statusWarning)
        }
    }
}
