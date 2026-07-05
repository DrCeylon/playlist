import AppKit
import ResonanceCore
import ResonanceDesign
import SwiftUI

@main
struct ResonanceMacApp: App {
    @StateObject private var themeManager: ThemeManager
    @StateObject private var workflowCoordinator: AppWorkflowCoordinator

    init() {
        let manager: ThemeManager
        do {
            manager = try ThemeManager()
        } catch {
            fatalError("Impossible de charger les thèmes embarqués : \(error)")
        }
        _themeManager = StateObject(wrappedValue: manager)
        _workflowCoordinator = StateObject(wrappedValue: AppWorkflowCoordinator())
    }

    var body: some Scene {
        WindowGroup {
            AppShellView()
                .environmentObject(themeManager)
                .environmentObject(workflowCoordinator)
                .onAppear {
                    NSApp.setActivationPolicy(.regular)
                    ApplicationIconConfigurator.applyIfNeeded()
                    NSApp.activate(ignoringOtherApps: true)
                }
        }
        .defaultSize(width: 1100, height: 720)
    }
}
