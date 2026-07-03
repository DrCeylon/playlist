import ResonanceDesign
import SwiftUI

struct CopyableField: View {
    let label: String
    let value: String
    let palette: ThemePalette
    @State private var copied = false

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label)
                .font(.caption.weight(.semibold))
                .foregroundStyle(palette.textSecondary)
            HStack(alignment: .top, spacing: 8) {
                SelectableText(
                    text: value,
                    font: .callout,
                    foreground: palette.textPrimary
                )
                Spacer(minLength: 0)
                Button {
                    ClipboardSupport.copy(value)
                    copied = true
                } label: {
                    Image(systemName: copied ? "checkmark.circle.fill" : "doc.on.doc")
                }
                .buttonStyle(.borderless)
                .help("Copier")
                .disabled(value.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }
        }
    }
}
