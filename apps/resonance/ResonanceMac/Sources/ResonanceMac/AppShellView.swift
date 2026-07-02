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
