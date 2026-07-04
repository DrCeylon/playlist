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
            VStack(spacing: 0) {
                workflowBanner
                detailView
                    .focusSection()
            }
        }
        .navigationSplitViewStyle(.balanced)
        .onAppear {
            themeManager.updateColorScheme(colorScheme)
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
                onTap: { workflow.openActiveWorkflow(selection: $selection) },
                onDismiss: { workflow.dismissBanner() }
            )
            .padding(.horizontal, 16)
            .padding(.top, 10)
            .padding(.bottom, 4)
        }
    }

    @ViewBuilder
    private var detailView: some View {
        switch selection ?? .home {
        case .home:
            HomeView(selection: $selection)
        case .newPlaylist:
            PlaylistBuilderView(selection: $selection)
        case .history:
            HistoryView(selection: $selection)
        case .laboratory:
            DiagnosticsView()
        case .settings:
            SettingsView()
        }
    }
}
