import AppKit
import Foundation

enum ClipboardSupport {
    static func copy(_ text: String) {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(trimmed, forType: .string)
    }

    static func openMusicApp() {
        guard let url = NSWorkspace.shared.urlForApplication(withBundleIdentifier: "com.apple.Music") else {
            return
        }
        let configuration = NSWorkspace.OpenConfiguration()
        configuration.activates = true
        NSWorkspace.shared.openApplication(at: url, configuration: configuration)
    }
}
