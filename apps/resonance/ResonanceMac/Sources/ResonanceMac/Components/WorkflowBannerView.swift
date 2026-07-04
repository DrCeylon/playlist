import ResonanceDesign
import SwiftUI

struct WorkflowBannerView: View {
    let presentation: AppWorkflowCoordinator.BannerPresentation
    let palette: ThemePalette
    let onTap: () -> Void
    let onDismiss: () -> Void

    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 12) {
                    leadingIcon
                    VStack(alignment: .leading, spacing: 3) {
                        Text(title)
                            .font(.subheadline.weight(.semibold))
                            .foregroundStyle(palette.textPrimary)
                        Text(presentation.step)
                            .font(.callout)
                            .foregroundStyle(palette.textPrimary.opacity(0.92))
                            .lineLimit(2)
                        if !presentation.detail.isEmpty {
                            Text(presentation.detail)
                                .font(.caption)
                                .foregroundStyle(palette.textSecondary)
                                .lineLimit(1)
                        }
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
                            .controlSize(.regular)
                            .tint(accentColor)
                    }
                }

                if let progressRatio = presentation.progressRatio, presentation.phase == .inProgress {
                    ProgressView(value: progressRatio)
                        .tint(accentColor)
                }

                if !presentation.progressLabel.isEmpty {
                    Text(presentation.progressLabel)
                        .font(.caption.weight(.medium))
                        .foregroundStyle(accentColor)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(backgroundColor)
            .overlay(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .stroke(borderColor, lineWidth: 1.5)
            )
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
            .shadow(color: accentColor.opacity(0.12), radius: 8, y: 2)
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
            return palette.statusInfo.opacity(0.2)
        case .completed:
            return palette.statusSuccess.opacity(0.16)
        case .failed:
            return palette.statusWarning.opacity(0.16)
        }
    }

    private var borderColor: Color {
        accentColor.opacity(0.5)
    }

    @ViewBuilder
    private var leadingIcon: some View {
        switch presentation.phase {
        case .inProgress:
            Image(systemName: presentation.kind == .generation ? "sparkles" : "arrow.down.circle.fill")
                .font(.title3)
                .foregroundStyle(palette.statusInfo)
        case .completed:
            Image(systemName: "checkmark.circle.fill")
                .font(.title3)
                .foregroundStyle(palette.statusSuccess)
        case .failed:
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.title3)
                .foregroundStyle(palette.statusWarning)
        }
    }
}
