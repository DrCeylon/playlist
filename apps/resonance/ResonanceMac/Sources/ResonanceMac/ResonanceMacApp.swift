import ResonanceCore
import ResonanceDesign
import SwiftUI

@main
struct ResonanceMacApp: App {
    @StateObject private var themeManager: ThemeManager

    init() {
        let manager: ThemeManager
        do {
            manager = try ThemeManager()
        } catch {
            fatalError("Impossible de charger les thèmes embarqués : \(error)")
        }
        _themeManager = StateObject(wrappedValue: manager)
    }

    var body: some Scene {
        WindowGroup {
            AppShellView()
                .environmentObject(themeManager)
        }
        .defaultSize(width: 1100, height: 720)
    }
}
