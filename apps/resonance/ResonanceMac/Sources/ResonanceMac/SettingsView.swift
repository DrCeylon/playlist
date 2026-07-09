import ResonanceCore
import ResonanceDesign
import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var themeManager: ThemeManager
    @State private var selectedThemeID: String = ThemeManager.defaultThemeID
    @State private var errorMessage: String?

    var body: some View {
        ThemedScreen {
            let palette = ThemePalette(theme: themeManager.active)

            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    VStack(alignment: .leading, spacing: 16) {
                        Text("Apparence")
                            .font(.headline)
                            .foregroundStyle(palette.textPrimary)

                        ThemedThemePicker(
                            selection: $selectedThemeID,
                            options: themeManager.themeOptions,
                            palette: palette
                        )
                        .onChange(of: selectedThemeID) { _, newValue in
                            applyTheme(newValue)
                        }

                        if let errorMessage {
                            Text(errorMessage)
                                .font(.callout)
                                .foregroundStyle(palette.statusError)
                        }
                    }
                    .themedSurfaceCard(fill: palette.surface, border: palette.borderSubtle)

                    VStack(alignment: .leading, spacing: 12) {
                        Text("À propos")
                            .font(.headline)
                            .foregroundStyle(palette.textPrimary)
                        infoRow(title: "Version shell", value: "Playlist Manager (preview)", palette: palette)
                        infoRow(title: "Thème actif", value: themeManager.activeDisplayName, palette: palette)
                    }
                    .themedSurfaceCard(fill: palette.surface, border: palette.borderSubtle)
                }
                .padding(24)
            }
            .onAppear {
                selectedThemeID = themeManager.selectedThemeID
            }
        }
        .navigationTitle("Paramètres")
    }

    private func infoRow(title: String, value: String, palette: ThemePalette) -> some View {
        HStack {
            Text(title)
                .foregroundStyle(palette.textSecondary)
            Spacer()
            Text(value)
                .foregroundStyle(palette.textPrimary)
        }
        .font(.callout)
    }

    private func applyTheme(_ themeID: String) {
        do {
            try themeManager.apply(themeID: themeID)
            errorMessage = nil
        } catch {
            errorMessage = "Impossible d'appliquer le thème."
        }
    }
}
