import ResonanceCore
import ResonanceDesign
import SwiftUI

enum HomeShortcut: String, CaseIterable, Identifiable {
    case newPlaylist
    case history
    case laboratory

    var id: String { rawValue }

    var title: String {
        switch self {
        case .newPlaylist: return "Nouvelle Playlist"
        case .history: return "Historique"
        case .laboratory: return "Laboratoire"
        }
    }

    var systemImage: String {
        switch self {
        case .newPlaylist: return "plus.rectangle.on.rectangle"
        case .history: return "clock"
        case .laboratory: return "flask"
        }
    }

    var destination: SidebarItem {
        switch self {
        case .newPlaylist: return .newPlaylist
        case .history: return .history
        case .laboratory: return .laboratory
        }
    }

    /// Shortcuts that can start generation or import when the destination screen is used.
    var triggersWorkflow: Bool {
        switch self {
        case .newPlaylist, .history:
            return true
        case .laboratory:
            return false
        }
    }
}

struct ThemedTextField: View {
    let title: String
    @Binding var text: String
    let palette: ThemePalette
    var axis: Axis = .horizontal
    @FocusState private var isFocused: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.caption)
                .foregroundStyle(palette.textSecondary)
            TextField(title, text: $text, axis: axis)
                .textFieldStyle(.plain)
                .labelsHidden()
                .foregroundStyle(palette.inputText)
                .tint(palette.accentPrimary)
                .focused($isFocused)
                #if os(macOS)
                .focusable(true)
                #endif
                .themedInputChrome(
                    fill: palette.inputBackground,
                    border: palette.borderSubtle,
                    focusBorder: palette.accentPrimary.opacity(0.65),
                    isFocused: isFocused
                )
        }
    }
}

struct ThemedThemePicker: View {
    @Binding var selection: String
    let options: [ThemeOption]
    let palette: ThemePalette

    private var selectedOption: ThemeOption? {
        options.first { $0.themeID == selection }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Thème")
                .font(.caption)
                .foregroundStyle(palette.textSecondary)

            Menu {
                ForEach(options) { option in
                    Button {
                        selection = option.themeID
                    } label: {
                        HStack {
                            if option.themeID == selection {
                                Image(systemName: "checkmark")
                            }
                            ThemePreviewSwatch(option: option)
                            Text(option.displayName)
                        }
                    }
                }
            } label: {
                HStack(spacing: 12) {
                    if let selectedOption {
                        ThemePreviewSwatch(option: selectedOption)
                        Text(selectedOption.displayName)
                            .foregroundStyle(palette.textPrimary)
                    } else {
                        Text("Choisir un thème")
                            .foregroundStyle(palette.textSecondary)
                    }
                    Spacer()
                    Image(systemName: "chevron.up.chevron.down")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(palette.textSecondary)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 10)
                .background(palette.inputBackground, in: RoundedRectangle(cornerRadius: 8, style: .continuous))
                .overlay {
                    RoundedRectangle(cornerRadius: 8, style: .continuous)
                        .strokeBorder(palette.borderSubtle, lineWidth: 1)
                        .allowsHitTesting(false)
                }
            }
            .menuStyle(.borderlessButton)
            .foregroundStyle(palette.textPrimary)
        }
    }
}

struct ThemedSegmentedPicker<Selection: Hashable>: View {
    let title: String
    @Binding var selection: Selection
    let options: [(Selection, String)]
    let palette: ThemePalette

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            if !title.isEmpty {
                Text(title)
                    .font(.caption)
                    .foregroundStyle(palette.textSecondary)
            }
            HStack(spacing: 0) {
                ForEach(Array(options.enumerated()), id: \.offset) { _, option in
                    let isSelected = selection == option.0
                    Button {
                        selection = option.0
                    } label: {
                        Text(option.1)
                            .font(.callout.weight(isSelected ? .semibold : .regular))
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 8)
                            .foregroundStyle(isSelected ? palette.textPrimary : palette.textSecondary)
                            .background(isSelected ? palette.inputBackground : palette.surface)
                    }
                    .buttonStyle(.plain)
                }
            }
            .background(palette.surface, in: RoundedRectangle(cornerRadius: 8, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: 8, style: .continuous)
                    .strokeBorder(palette.borderSubtle, lineWidth: 1)
                    .allowsHitTesting(false)
            }
        }
    }
}

private struct ThemePreviewSwatch: View {
    let option: ThemeOption

    var body: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(Color(tokenHex: option.previewBackground))
                .frame(width: 14, height: 14)
            Circle()
                .fill(Color(tokenHex: option.previewAccent))
                .frame(width: 14, height: 14)
        }
    }
}
