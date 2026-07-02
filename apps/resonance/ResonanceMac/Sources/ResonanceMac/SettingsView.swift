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

            Form {
                Section("Apparence") {
                    Picker("Thème", selection: $selectedThemeID) {
                        ForEach(themeManager.themeOptions) { option in
                            HStack(spacing: 12) {
                                ThemePreviewSwatch(option: option)
                                Text(option.displayName)
                            }
                            .tag(option.themeID)
                        }
                    }
                    .onChange(of: selectedThemeID) { _, newValue in
                        applyTheme(newValue)
                    }

                    if let errorMessage {
                        Text(errorMessage)
                            .font(.callout)
                            .foregroundStyle(palette.statusError)
                    }
                }

                Section("À propos") {
                    LabeledContent("Version shell", value: "4.8 Preview")
                    LabeledContent("Thème actif", value: themeManager.active.displayName)
                }
            }
            .formStyle(.grouped)
            .scrollContentBackground(.hidden)
            .onAppear {
                selectedThemeID = themeManager.active.id
            }
        }
        .navigationTitle("Paramètres")
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

private struct ThemePreviewSwatch: View {
    let option: ThemeOption

    var body: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(Color(tokenHex: option.previewBackground))
                .frame(width: 14, height: 14)
            Circle()
                .fill(Color(tokenHex: option.previewAccent))
                .frame(width: 14, height: 14)
        }
    }
}
