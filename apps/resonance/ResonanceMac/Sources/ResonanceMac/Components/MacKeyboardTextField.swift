import AppKit
import SwiftUI

/// AppKit-backed text field for reliable macOS keyboard focus and typing.
struct MacKeyboardTextField: NSViewRepresentable {
    let placeholder: String
    @Binding var text: String
    var isMultiline: Bool = false
    var onCommit: (() -> Void)?

    func makeNSView(context: Context) -> NSTextField {
        let field: NSTextField
        if isMultiline {
            let wrapped = NSTextField(wrappingLabelWithString: "")
            wrapped.maximumNumberOfLines = 0
            field = wrapped
        } else {
            field = NSTextField(string: "")
        }
        field.placeholderString = placeholder
        field.isBordered = true
        field.isBezeled = true
        field.bezelStyle = .roundedBezel
        field.focusRingType = .default
        field.delegate = context.coordinator
        field.target = context.coordinator
        field.action = #selector(Coordinator.commitEditing)
        field.stringValue = text
        return field
    }

    func updateNSView(_ nsView: NSTextField, context: Context) {
        if nsView.stringValue != text {
            nsView.stringValue = text
        }
        context.coordinator.parent = self
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(parent: self)
    }

    final class Coordinator: NSObject, NSTextFieldDelegate {
        var parent: MacKeyboardTextField

        init(parent: MacKeyboardTextField) {
            self.parent = parent
        }

        func controlTextDidChange(_ notification: Notification) {
            guard let field = notification.object as? NSTextField else { return }
            parent.text = field.stringValue
        }

        @objc func commitEditing() {
            parent.onCommit?()
        }
    }
}
