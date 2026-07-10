import ResonanceCore
import ResonanceDesign
import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var themeManager: ThemeManager
    @EnvironmentObject private var workflow: AppWorkflowCoordinator
    @State private var selectedThemeID: String = ThemeManager.defaultThemeID
    @State private var errorMessage: String?
    @State private var showLaboratory = false

    var body: some View {
        ThemedScreen {
            let palette = ThemePalette(theme: themeManager.active)

            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    ProductSectionCard(title: "Apparence", palette: palette) {
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

                    ProductSectionCard(title: "Bibliothèque", palette: palette) {
                        ProductMetricRow(
                            title: "Playlists enregistrées",
                            value: "\(workflow.libraryStore.playlists.count)",
                            palette: palette
                        )
                        ProductMetricRow(
                            title: "À synchroniser",
                            value: "\(workflow.libraryStore.playlistsNeedingAttention.count)",
                            palette: palette
                        )
                    }

                    ProductSectionCard(title: "Avancé", palette: palette) {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Outils de diagnostic pour le développement et le support.")
                                .font(.caption)
                                .foregroundStyle(palette.textSecondary)
                            Button("Ouvrir le laboratoire") { showLaboratory = true }
                                .buttonStyle(.bordered)
                        }
                    }

                    ProductSectionCard(title: "À propos", palette: palette) {
                        ProductMetricRow(title: "Version", value: "Resonance 1.0.0", palette: palette)
                        ProductMetricRow(title: "Thème actif", value: themeManager.activeDisplayName, palette: palette)
                    }
                }
                .padding(24)
            }
            .onAppear {
                selectedThemeID = themeManager.selectedThemeID
            }
            .navigationDestination(isPresented: $showLaboratory) {
                DiagnosticsView()
                    .navigationTitle("Laboratoire")
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
