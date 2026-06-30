import SwiftUI

public extension Color {
  init(tokenHex hex: String) {
    self = Color(hex: hex) ?? .clear
  }

  init?(hex: String) {
    var value = hex.trimmingCharacters(in: .whitespacesAndNewlines)
    if value.hasPrefix("#") {
      value.removeFirst()
    }
    guard value.count == 6 || value.count == 8 else {
      return nil
    }
    guard let numeric = UInt64(value, radix: 16) else {
      return nil
    }

    let red, green, blue, alpha: Double
    if value.count == 6 {
      red = Double((numeric & 0xFF0000) >> 16) / 255.0
      green = Double((numeric & 0x00FF00) >> 8) / 255.0
      blue = Double(numeric & 0x0000FF) / 255.0
      alpha = 1.0
    } else {
      red = Double((numeric & 0xFF000000) >> 24) / 255.0
      green = Double((numeric & 0x00FF0000) >> 16) / 255.0
      blue = Double((numeric & 0x0000FF00) >> 8) / 255.0
      alpha = Double(numeric & 0x000000FF) / 255.0
    }

    self.init(.sRGB, red: red, green: green, blue: blue, opacity: alpha)
  }
}

public struct ThemePalette {
  public let backgroundPrimary: Color
  public let backgroundSecondary: Color
  public let backgroundElevated: Color
  public let textPrimary: Color
  public let textSecondary: Color
  public let textTertiary: Color
  public let accentPrimary: Color
  public let accentSecondary: Color
  public let borderSubtle: Color
  public let statusSuccess: Color
  public let statusWarning: Color
  public let statusError: Color
  public let statusInfo: Color
  public let labAccent: Color

  public init(theme: Theme) {
    let colors = theme.tokens.colors
    backgroundPrimary = Self.color(for: "color.background.primary", in: colors)
    backgroundSecondary = Self.color(for: "color.background.secondary", in: colors)
    backgroundElevated = Self.color(for: "color.background.elevated", in: colors)
    textPrimary = Self.color(for: "color.text.primary", in: colors)
    textSecondary = Self.color(for: "color.text.secondary", in: colors)
    textTertiary = Self.color(for: "color.text.tertiary", in: colors)
    accentPrimary = Self.color(for: "color.accent.primary", in: colors)
    accentSecondary = Self.color(for: "color.accent.secondary", in: colors)
    borderSubtle = Self.color(for: "color.border.subtle", in: colors)
    statusSuccess = Self.color(for: "color.status.success", in: colors)
    statusWarning = Self.color(for: "color.status.warning", in: colors)
    statusError = Self.color(for: "color.status.error", in: colors)
    statusInfo = Self.color(for: "color.status.info", in: colors)
    labAccent = Self.color(for: "color.lab.accent", in: colors)
  }

  private static func color(for key: String, in colors: [String: String]) -> Color {
    guard let hex = colors[key], let parsed = Color(hex: hex) else {
      return .clear
    }
    return parsed
  }
}

private struct ThemeManagerKey: EnvironmentKey {
  @MainActor static var defaultValue: ThemeManager {
    fatalError("ThemeManager missing from environment")
  }
}

public extension EnvironmentValues {
  var themeManager: ThemeManager {
    get { self[ThemeManagerKey.self] }
    set { self[ThemeManagerKey.self] = newValue }
  }
}

public struct ThemedScreen<Content: View>: View {
  @EnvironmentObject private var themeManager: ThemeManager
  private let content: Content

  public init(@ViewBuilder content: () -> Content) {
    self.content = content()
  }

  public var body: some View {
    let palette = ThemePalette(theme: themeManager.active)
    content
      .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
      .background(palette.backgroundPrimary)
      .foregroundStyle(palette.textPrimary)
      .animation(.easeOut(duration: 0.3), value: themeManager.active.id)
  }
}
