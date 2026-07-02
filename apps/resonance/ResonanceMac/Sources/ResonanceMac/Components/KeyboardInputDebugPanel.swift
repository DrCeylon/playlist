import AppKit
import SwiftUI

/// Temporary macOS keyboard diagnostics — helps isolate responder-chain issues.
struct KeyboardInputDebugPanel: View {
    @Binding var swiftUIText: String
    @Binding var appKitText: String
    @State private var firstResponderDescription = "—"
    @State private var isKeyWindow = false

    private let timer = Timer.publish(every: 0.4, on: .main, in: .common).autoconnect()

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Debug clavier (temporaire)")
                .font(.caption.weight(.semibold))
            Text("Fenêtre clé : \(isKeyWindow ? "oui" : "non") · First responder : \(firstResponderDescription)")
                .font(.caption2.monospaced())
                .foregroundStyle(.secondary)
            HStack(spacing: 16) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("SwiftUI TextField natif")
                        .font(.caption2)
                    TextField("Tape ici (SwiftUI)", text: $swiftUIText)
                        .textFieldStyle(.roundedBorder)
                        .frame(width: 220)
                }
                VStack(alignment: .leading, spacing: 4) {
                    Text("NSTextField (AppKit)")
                        .font(.caption2)
                    MacKeyboardTextField(placeholder: "Tape ici (AppKit)", text: $appKitText)
                        .frame(width: 220, height: 26)
                }
            }
            Text("SwiftUI: «\(swiftUIText)» · AppKit: «\(appKitText)»")
                .font(.caption2.monospaced())
        }
        .padding(12)
        .background(Color(nsColor: .controlBackgroundColor).opacity(0.35))
        .clipShape(RoundedRectangle(cornerRadius: 8))
        .onReceive(timer) { _ in
            refreshResponderState()
        }
        .onAppear {
            refreshResponderState()
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
