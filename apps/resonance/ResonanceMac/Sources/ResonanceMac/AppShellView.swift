import ResonanceCore
import ResonanceDesign
import SwiftUI

struct AppShellView: View {
    @State private var selection: SidebarItem? = .home

    var body: some View {
        NavigationSplitView {
            SidebarView(selection: $selection)
        } detail: {
            detailView
        }
        .navigationSplitViewStyle(.balanced)
    }

    @ViewBuilder
    private var detailView: some View {
        switch selection ?? .home {
        case .home:
            HomeView()
        case .newPlaylist:
            PlaylistBuilderView()
        case .history:
            PlaceholderScreenView(
                title: "Historique",
                message: "L'historique des sessions arrive en Phase 4.7."
            )
        case .laboratory:
            PlaceholderScreenView(
                title: "Laboratoire",
                message: "Les diagnostics arrivent en Phase 4.7."
            )
        case .settings:
            SettingsView()
        }
    }
}
