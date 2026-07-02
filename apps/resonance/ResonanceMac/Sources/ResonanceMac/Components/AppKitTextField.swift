import AppKit
import SwiftUI

/// NSTextField-backed editor that keeps typing inside AppKit (no SwiftUI overwrite per keystroke).
struct AppKitTextField: NSViewRepresentable {
    let placeholder: String
    @Binding var text: String
    var isMultiline: Bool = false
    var onCommit: (() -> Void)?

    func makeNSView(context: Context) -> KeyableNSTextField {
        let field = KeyableNSTextField()
        if isMultiline {
            field.maximumNumberOfLines = 0
            field.cell?.wraps = true
            field.cell?.isScrollable = false
        }
        field.placeholderString = placeholder
        field.isEditable = true
        field.isSelectable = true
        field.isEnabled = true
        field.isBordered = true
        field.isBezeled = true
        field.bezelStyle = .roundedBezel
        field.focusRingType = .exterior
        field.font = NSFont.systemFont(ofSize: NSFont.systemFontSize)
        field.delegate = context.coordinator
        field.target = context.coordinator
        field.action = #selector(Coordinator.commitEditing)
        field.stringValue = text
        context.coordinator.lastSyncedText = text
        return field
    }

    func updateNSView(_ field: KeyableNSTextField, context: Context) {
        context.coordinator.parent = self
        field.placeholderString = placeholder

        let isEditing = field.currentEditor() != nil
            || field.window?.firstResponder === field
            || field.window?.firstResponder === field.currentEditor()
        guard !isEditing else { return }

        if context.coordinator.lastSyncedText != text, field.stringValue != text {
            field.stringValue = text
            context.coordinator.lastSyncedText = text
        }
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(parent: self)
    }

    final class Coordinator: NSObject, NSTextFieldDelegate {
        var parent: AppKitTextField
        var lastSyncedText = ""

        init(parent: AppKitTextField) {
            self.parent = parent
        }

        func controlTextDidChange(_ notification: Notification) {
            guard let field = notification.object as? NSTextField else { return }
            let value = field.stringValue
            lastSyncedText = value
            if parent.text != value {
                parent.text = value
            }
        }

        @objc func commitEditing() {
            parent.onCommit?()
        }
    }
}

final class KeyableNSTextField: NSTextField {
    override var acceptsFirstResponder: Bool { true }

    override func mouseDown(with event: NSEvent) {
        window?.makeFirstResponder(self)
        super.mouseDown(with: event)
    }

    override func becomeFirstResponder() -> Bool {
        let accepted = super.becomeFirstResponder()
        if !accepted {
            return window?.makeFirstResponder(self) ?? false
        }
        return accepted
    }
}
