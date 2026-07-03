import ResonanceDesign
import SwiftUI

struct SelectableText: View {
    let text: String
    var font: Font = .body
    var foreground: Color = .primary
    var lineLimit: Int?

    var body: some View {
        Text(text)
            .font(font)
            .foregroundStyle(foreground)
            .textSelection(.enabled)
            .lineLimit(lineLimit)
    }
}
