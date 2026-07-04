import ResonanceCore
import ResonanceDesign
import SwiftUI

struct AppShellView: View {
    @State private var selection: SidebarItem? = .home
    @EnvironmentObject private var themeManager: ThemeManager
    @Environment(\.colorScheme) private var colorScheme

    var body: some View {
        NavigationSplitView {
            SidebarView(selection: $selection)
        } detail: {
            detailView
                .focusSection()
        }
        .navigationSplitViewStyle(.balanced)
        .onAppear {
            themeManager.updateColorScheme(colorScheme)
        }
        .onChange(of: colorScheme) { _, newValue in
            themeManager.updateColorScheme(newValue)
        }
    }

    @ViewBuilder
    private var detailView: some View {
        switch selection ?? .home {
        case .home:
            HomeView(selection: $selection)
        case .newPlaylist:
            PlaylistBuilderView()
        case .history:
            HistoryView()
        case .laboratory:
            DiagnosticsView()
        case .settings:
            SettingsView()
        }
    }
}
