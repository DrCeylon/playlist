import Foundation

public enum ThemeContrast {
    /// Minimum relative luminance difference for readable text (WCAG-inspired heuristic).
    public static let minimumLuminanceDelta = 0.35

    public static func relativeLuminance(hex: String) -> Double? {
        guard let rgba = parseRGBA(hex: hex) else { return nil }
        func channel(_ value: Double) -> Double {
            if value <= 0.03928 {
                return value / 12.92
            }
            return pow((value + 0.055) / 1.055, 2.4)
        }
        let red = channel(rgba.red)
        let green = channel(rgba.green)
        let blue = channel(rgba.blue)
        return 0.2126 * red + 0.7152 * green + 0.0722 * blue
    }

    public static func contrastRatio(foregroundHex: String, backgroundHex: String) -> Double? {
        guard let fg = relativeLuminance(hex: foregroundHex),
              let bg = relativeLuminance(hex: backgroundHex) else {
            return nil
        }
        let lighter = max(fg, bg)
        let darker = min(fg, bg)
        return (lighter + 0.05) / (darker + 0.05)
    }

    public static func hasReadableContrast(foregroundHex: String, backgroundHex: String) -> Bool {
        guard let ratio = contrastRatio(foregroundHex: foregroundHex, backgroundHex: backgroundHex) else {
            return false
        }
        return ratio >= 4.5
    }

    private struct RGBA {
        let red: Double
        let green: Double
        let blue: Double
    }

    private static func parseRGBA(hex: String) -> RGBA? {
        var value = hex.trimmingCharacters(in: .whitespacesAndNewlines)
        if value.hasPrefix("#") {
            value.removeFirst()
        }
        guard let numeric = UInt64(value, radix: 16) else { return nil }

        let red, green, blue: Double
        if value.count == 6 {
            red = Double((numeric & 0xFF0000) >> 16) / 255.0
            green = Double((numeric & 0x00FF00) >> 8) / 255.0
            blue = Double(numeric & 0x0000FF) / 255.0
        } else if value.count == 8 {
            red = Double((numeric & 0xFF000000) >> 24) / 255.0
            green = Double((numeric & 0x00FF0000) >> 16) / 255.0
            blue = Double((numeric & 0x0000FF00) >> 8) / 255.0
        } else {
            return nil
        }
        return RGBA(red: red, green: green, blue: blue)
    }
}
