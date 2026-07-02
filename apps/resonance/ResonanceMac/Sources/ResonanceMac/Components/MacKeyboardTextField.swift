import AppKit
import SwiftUI

/// AppKit text field hosted in a focusable container for reliable macOS keyboard input.
struct MacKeyboardTextField: NSViewRepresentable {
    let placeholder: String
    @Binding var text: String
    var isMultiline: Bool = false
    var onCommit: (() -> Void)?

    func makeNSView(context: Context) -> FocusableTextFieldContainer {
        let container = FocusableTextFieldContainer(isMultiline: isMultiline)
        container.textField.placeholderString = placeholder
        container.textField.stringValue = text
        container.textField.delegate = context.coordinator
        container.textField.target = context.coordinator
        container.textField.action = #selector(Coordinator.commitEditing)
        container.onTextChange = { newValue in
            context.coordinator.updateText(newValue)
        }
        container.onCommit = onCommit
        return container
    }

    func updateNSView(_ container: FocusableTextFieldContainer, context: Context) {
        context.coordinator.parent = self
        container.textField.placeholderString = placeholder
        container.onCommit = onCommit

        let isEditing = container.textField.currentEditor() != nil
            || container.window?.firstResponder === container.textField
        guard !isEditing else { return }

        if container.textField.stringValue != text {
            container.textField.stringValue = text
        }
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(parent: self)
    }

    final class Coordinator: NSObject, NSTextFieldDelegate {
        var parent: MacKeyboardTextField

        init(parent: MacKeyboardTextField) {
            self.parent = parent
        }

        func updateText(_ value: String) {
            if parent.text != value {
                parent.text = value
            }
        }

        func controlTextDidChange(_ notification: Notification) {
            guard let field = notification.object as? NSTextField else { return }
            updateText(field.stringValue)
        }

        @objc func commitEditing() {
            parent.onCommit?()
        }
    }
}

final class FocusableTextFieldContainer: NSView {
    let textField: NSTextField
    var onTextChange: ((String) -> Void)?
    var onCommit: (() -> Void)?

    init(isMultiline: Bool) {
        if isMultiline {
            let field = NSTextField()
            field.maximumNumberOfLines = 0
            field.cell?.wraps = true
            field.cell?.isScrollable = false
            textField = field
        } else {
            textField = NSTextField(string: "")
        }
        super.init(frame: .zero)
        configureField()
        installField()
    }

    @available(*, unavailable)
    required init?(coder: NSCoder) {
        nil
    }

    private func configureField() {
        textField.translatesAutoresizingMaskIntoConstraints = false
        textField.isEditable = true
        textField.isSelectable = true
        textField.isEnabled = true
        textField.isBordered = true
        textField.isBezeled = true
        textField.bezelStyle = .roundedBezel
        textField.focusRingType = .exterior
        textField.font = NSFont.systemFont(ofSize: NSFont.systemFontSize)
    }

    private func installField() {
        addSubview(textField)
        NSLayoutConstraint.activate([
            textField.leadingAnchor.constraint(equalTo: leadingAnchor),
            textField.trailingAnchor.constraint(equalTo: trailingAnchor),
            textField.topAnchor.constraint(equalTo: topAnchor),
            textField.bottomAnchor.constraint(equalTo: bottomAnchor),
            textField.heightAnchor.constraint(greaterThanOrEqualToConstant: 24),
        ])
    }

    override var acceptsFirstResponder: Bool { true }

    override func mouseDown(with event: NSEvent) {
        window?.makeFirstResponder(textField)
    }

    override func becomeFirstResponder() -> Bool {
        window?.makeFirstResponder(textField) ?? false
    }

    override func performKeyEquivalent(with event: NSEvent) -> Bool {
        if window?.firstResponder === textField {
            return textField.performKeyEquivalent(with: event)
        }
        return super.performKeyEquivalent(with: event)
    }
}
