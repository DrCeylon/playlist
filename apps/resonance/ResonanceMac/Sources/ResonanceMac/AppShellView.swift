import ResonanceCore
import ResonanceDesign
import SwiftUI

struct AppShellView: View {
    @State private var selection: SidebarItem? = .home
    @State private var pendingHistoryEdit: PlaylistGenerationRequest?

    var body: some View {
        NavigationSplitView {
            SidebarView(selection: $selection)
        } detail: {
            detailView
                .focusSection()
        }
        .navigationSplitViewStyle(.balanced)
    }

    @ViewBuilder
    private var detailView: some View {
        switch selection ?? .home {
        case .home:
            HomeView(selection: $selection)
        case .newPlaylist:
            PlaylistBuilderView(pendingEditRequest: $pendingHistoryEdit)
        case .history:
            HistoryView { request in
                pendingHistoryEdit = request
                selection = .newPlaylist
            }
        case .laboratory:
            DiagnosticsView()
        case .settings:
            SettingsView()
        }
    }
}
