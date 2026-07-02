import ResonanceCore
import ResonanceDesign
import SwiftUI

struct SidebarView: View {
    @Binding var selection: SidebarItem?
    @EnvironmentObject private var themeManager: ThemeManager

    var body: some View {
        let palette = ThemePalette(theme: themeManager.active)

        ScrollView {
            VStack(alignment: .leading, spacing: 4) {
                ForEach(SidebarItem.allCases) { item in
                    sidebarButton(item: item, palette: palette)
                }
            }
            .padding(.vertical, 8)
            .padding(.horizontal, 10)
        }
        .navigationTitle("Resonance")
        .foregroundStyle(palette.sidebarText)
        .background(palette.sidebarBackground)
        .focusEffectDisabled()
    }

    private func sidebarButton(item: SidebarItem, palette: ThemePalette) -> some View {
        let isSelected = (selection ?? .home) == item
        return Button {
            selection = item
        } label: {
            Label(item.title, systemImage: item.systemImage)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.horizontal, 10)
                .padding(.vertical, 8)
                .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .background(
            RoundedRectangle(cornerRadius: 8, style: .continuous)
                .fill(isSelected ? palette.accentPrimary.opacity(0.18) : .clear)
        )
        .foregroundStyle(isSelected ? palette.accentPrimary : palette.sidebarText)
    }
}
