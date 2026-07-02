import SwiftUI

public extension View {
    /// Card chrome that keeps decorative borders out of the hit-test path (macOS text fields).
    func themedSurfaceCard(
        fill: Color,
        border: Color,
        cornerRadius: CGFloat = 14,
        padding: CGFloat = 16
    ) -> some View {
        self
            .padding(padding)
            .background(fill, in: RoundedRectangle(cornerRadius: cornerRadius, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                    .strokeBorder(border, lineWidth: 1)
                    .allowsHitTesting(false)
            }
    }

    /// Input chrome with themed fill/border behind editable controls.
    func themedInputChrome(
        fill: Color,
        border: Color,
        focusBorder: Color,
        isFocused: Bool,
        cornerRadius: CGFloat = 8
    ) -> some View {
        self
            .padding(10)
            .background(fill, in: RoundedRectangle(cornerRadius: cornerRadius, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                    .strokeBorder(isFocused ? focusBorder : border, lineWidth: 1)
                    .allowsHitTesting(false)
            }
    }
}
