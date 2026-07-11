import ResonanceCore
import ResonanceDesign
import SwiftUI

struct AppShellView: View {
    @State private var selection: SidebarItem? = .home
    @EnvironmentObject private var themeManager: ThemeManager
    @EnvironmentObject private var workflow: AppWorkflowCoordinator
    @Environment(\.colorScheme) private var colorScheme

    var body: some View {
        NavigationSplitView {
            SidebarView(selection: $selection)
        } detail: {
            NavigationStack {
                detailView
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
            .safeAreaInset(edge: .top, spacing: 0) {
                workflowBanner
            }
            .focusSection()
        }
        .navigationSplitViewStyle(.balanced)
        .onAppear {
            themeManager.updateColorScheme(colorScheme)
            Task { await workflow.libraryStore.refresh() }
        }
        .onChange(of: colorScheme) { _, newValue in
            themeManager.updateColorScheme(newValue)
        }
        .onChange(of: selection) { _, newValue in
            if newValue == .newPlaylist {
                workflow.applyPendingEditIfNeeded()
            }
        }
    }

    @ViewBuilder
    private var workflowBanner: some View {
        if let banner = workflow.banner {
            let palette = ThemePalette(theme: themeManager.active)
            WorkflowBannerView(
                presentation: banner,
                palette: palette,
                onTap: { selection = workflow.activeRoute },
                onDismiss: { workflow.dismissBanner() }
            )
            .padding(.horizontal, 16)
            .padding(.top, 8)
            .padding(.bottom, 6)
            .background(palette.backgroundPrimary.opacity(0.98))
        }
    }

    @ViewBuilder
    private var detailView: some View {
        switch selection ?? .home {
        case .home:
            HomeView(selection: $selection)
        case .newPlaylist:
            PlaylistBuilderView(selection: $selection)
        case .playlists:
            PlaylistsView(selection: $selection)
        case .sync:
            SyncView(selection: $selection, syncModel: workflow.syncViewModel)
        case .providers:
            ProvidersView(viewModel: workflow.providersViewModel)
        case .history:
            HistoryView(viewModel: workflow.historyViewModel, selection: $selection)
        case .settings:
            SettingsView()
        }
    }
}
