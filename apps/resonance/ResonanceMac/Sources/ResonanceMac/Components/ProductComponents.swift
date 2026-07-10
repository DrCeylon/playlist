import ResonanceDesign
import SwiftUI

struct ProductSectionCard<Content: View>: View {
    let title: String
    let palette: ThemePalette
    @ViewBuilder let content: () -> Content

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.headline)
                .foregroundStyle(palette.textPrimary)
            content()
        }
        .themedSurfaceCard(fill: palette.surface, border: palette.borderSubtle)
    }
}

struct StatusChip: View {
    let label: String
    let color: Color

    var body: some View {
        Text(label)
            .font(.caption2.weight(.semibold))
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(color.opacity(0.14), in: Capsule())
            .foregroundStyle(color)
    }
}

struct ProductEmptyState: View {
    let title: String
    let message: String
    let systemImage: String
    let palette: ThemePalette

    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: systemImage)
                .font(.largeTitle)
                .foregroundStyle(palette.textSecondary)
            Text(title)
                .font(.headline)
                .foregroundStyle(palette.textPrimary)
            Text(message)
                .font(.callout)
                .multilineTextAlignment(.center)
                .foregroundStyle(palette.textSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(24)
    }
}

struct ProductMetricRow: View {
    let title: String
    let value: String
    let palette: ThemePalette

    var body: some View {
        HStack {
            Text(title)
                .foregroundStyle(palette.textSecondary)
            Spacer()
            Text(value)
                .foregroundStyle(palette.textPrimary)
        }
        .font(.callout)
    }
}
