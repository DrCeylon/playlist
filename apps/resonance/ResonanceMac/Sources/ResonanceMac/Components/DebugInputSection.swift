import AppKit
import SwiftUI

enum ResonanceFeatureFlags {
    static var keyboardDebugEnabled: Bool {
        #if DEBUG
        return ProcessInfo.processInfo.environment["RESONANCE_KEYBOARD_DEBUG"] == "1"
        #else
        return ProcessInfo.processInfo.environment["RESONANCE_KEYBOARD_DEBUG"] == "1"
        #endif
    }

    static var architectModeEnabled: Bool {
        ProcessInfo.processInfo.environment["RESONANCE_ARCHITECT_MODE"] == "1"
    }
}

/// Ultra-minimal keyboard probe: local @State only, no ViewModel, no theme, no validation.
struct DebugInputSection: View {
    @State private var isolatedText = ""
    @State private var lastKeyDown = "—"
    @State private var firstResponderDescription = "—"
    @State private var isKeyWindow = false
    @State private var keyMonitor: Any?

    private let timer = Timer.publish(every: 2.0, on: .main, in: .common).autoconnect()

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("DebugInput — tape ici pour valider le clavier AppKit")
                .font(.caption.weight(.semibold))
            AppKitTextField(placeholder: "Tape au clavier (aucun binding ViewModel)", text: $isolatedText)
                .frame(maxWidth: 420, minHeight: 28, alignment: .leading)
            Text("Valeur live : «\(isolatedText)»")
                .font(.caption.monospaced())
                .textSelection(.enabled)
            Text("Dernière touche : \(lastKeyDown)")
                .font(.caption2.monospaced())
            Text("Fenêtre clé : \(isKeyWindow ? "oui" : "non") · First responder : \(firstResponderDescription)")
                .font(.caption2.monospaced())
                .foregroundStyle(.secondary)
        }
        .padding(12)
        .background(Color(nsColor: .textBackgroundColor))
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color.secondary.opacity(0.35), lineWidth: 1)
        )
        .onAppear {
            installKeyMonitor()
            refreshResponderState()
        }
        .onDisappear {
            removeKeyMonitor()
        }
        .onReceive(timer) { _ in
            if ResonanceFeatureFlags.keyboardDebugEnabled {
                refreshResponderState()
            }
        }
    }

    private func installKeyMonitor() {
        guard keyMonitor == nil else { return }
        keyMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { event in
            if let characters = event.charactersIgnoringModifiers, !characters.isEmpty {
                lastKeyDown = characters
            } else {
                lastKeyDown = "keyCode:\(event.keyCode)"
            }
            return event
        }
    }

    private func removeKeyMonitor() {
        if let keyMonitor {
            NSEvent.removeMonitor(keyMonitor)
            self.keyMonitor = nil
        }
    }

    private func refreshResponderState() {
        let window = NSApp.keyWindow
        isKeyWindow = window != nil
        if let responder = window?.firstResponder {
            firstResponderDescription = String(describing: type(of: responder))
        } else {
            firstResponderDescription = "aucun"
        }
    }
}
