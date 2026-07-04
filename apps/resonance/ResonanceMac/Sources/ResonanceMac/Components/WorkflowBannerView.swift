import ResonanceDesign
import SwiftUI

struct WorkflowBannerView: View {
    let presentation: AppWorkflowCoordinator.BannerPresentation
    let palette: ThemePalette
    let onTap: () -> Void
    let onDismiss: () -> Void

    @State private var isExpanded = false

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
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
                                .foregroundStyle(palette.textPrimary)
                                .lineLimit(isExpanded ? nil : 2)
                            if !presentation.detail.isEmpty {
                                Text(presentation.detail)
                                    .font(.caption)
                                    .foregroundStyle(palette.textSecondary)
                                    .lineLimit(isExpanded ? nil : 1)
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
                        ProgressView(value: max(0.02, progressRatio))
                            .tint(accentColor)
                    }

                    if !presentation.progressLabel.isEmpty {
                        Text(presentation.progressLabel)
                            .font(.caption.weight(.semibold))
                            .foregroundStyle(accentColor)
                    }
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
            }
            .buttonStyle(.plain)

            if !presentation.substeps.isEmpty {
                Button {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        isExpanded.toggle()
                    }
                } label: {
                    HStack(spacing: 6) {
                        Image(systemName: isExpanded ? "chevron.down" : "chevron.right")
                            .font(.caption.weight(.semibold))
                        Text(isExpanded ? "Masquer le détail des étapes" : "Voir le détail des étapes (\(presentation.substeps.count))")
                            .font(.caption.weight(.medium))
                    }
                    .foregroundStyle(palette.textSecondary)
                    .padding(.horizontal, 16)
                    .padding(.bottom, 10)
                }
                .buttonStyle(.plain)
            }

            if isExpanded, !presentation.substeps.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    ForEach(Array(presentation.substeps.enumerated()), id: \.offset) { index, step in
                        HStack(alignment: .top, spacing: 8) {
                            Text("\(index + 1).")
                                .font(.caption2.monospacedDigit())
                                .foregroundStyle(palette.textTertiary)
                                .frame(width: 18, alignment: .trailing)
                            Text(step)
                                .font(.caption)
                                .foregroundStyle(palette.textSecondary)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }
                }
                .padding(.horizontal, 16)
                .padding(.bottom, 12)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(backgroundColor)
        .overlay(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .stroke(borderColor, lineWidth: 1.5)
        )
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
        .shadow(color: accentColor.opacity(0.14), radius: 8, y: 2)
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
        palette.surface.opacity(0.96)
    }

    private var borderColor: Color {
        accentColor.opacity(0.55)
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
