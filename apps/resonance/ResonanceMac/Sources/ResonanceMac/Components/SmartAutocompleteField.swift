import AppKit
import ResonanceCore
import ResonanceDesign
import SwiftUI

struct SmartAutocompleteField<Provider: SuggestionProvider>: View where Provider.Entity: CanonicalEntity & Codable {
    let title: String
    let placeholder: String
  @ObservedObject var engineHolder: AutocompleteEngineHolder<Provider>
    let palette: ThemePalette
    let rowContent: (Provider.Entity, Bool) -> AnyView
    let onCommit: () -> Void

    @FocusState private var isFocused: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.caption)
                .foregroundStyle(palette.textSecondary)

            ZStack(alignment: .topLeading) {
                fieldContent
                if engineHolder.engine.session.isPanelVisible {
                    suggestionPanel
                        .offset(y: 36)
                        .zIndex(10)
                }
            }
        }
    }

    @ViewBuilder
    private var fieldContent: some View {
        if let selected = engineHolder.engine.selection.selected, !engineHolder.engine.selection.isEditing {
            selectedChip(selected)
        } else {
            queryField
        }
    }

    private func selectedChip(_ entity: Provider.Entity) -> some View {
        HStack(spacing: 8) {
            rowContent(entity, true)
            Spacer(minLength: 0)
            Button {
                engineHolder.engine.clearSelection()
                engineHolder.syncText()
                engineHolder.engine.beginEditing()
                isFocused = true
                onCommit()
            } label: {
                Image(systemName: "xmark.circle.fill")
                    .foregroundStyle(palette.textTertiary)
            }
            .buttonStyle(.borderless)
            .help("Effacer la sélection")
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(palette.backgroundSecondary)
        .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 8, style: .continuous)
                .stroke(palette.borderSubtle, lineWidth: 1)
        )
        .onTapGesture {
            engineHolder.engine.beginEditing()
            isFocused = true
        }
    }

    private var queryField: some View {
        SmartSearchTextField(
            placeholder: placeholder,
            text: $engineHolder.queryText,
            onTextChange: { value in
                engineHolder.engine.updateQuery(value)
            },
            onMoveHighlight: { delta in
                engineHolder.engine.moveHighlight(delta: delta)
            },
            onSelectHighlighted: {
                if engineHolder.engine.selectHighlighted() != nil {
                    engineHolder.syncText()
                    onCommit()
                }
            },
            onDismiss: {
                engineHolder.engine.dismiss()
            },
            onBeginEditing: {
                engineHolder.engine.beginEditing()
            },
            onEndEditing: {
                engineHolder.engine.endEditing()
            },
            onClearWithCommand: {
                engineHolder.engine.clearSelection()
                engineHolder.syncText()
            }
        )
        .focused($isFocused)
        .frame(maxWidth: .infinity, minHeight: 28, alignment: .leading)
        .onChange(of: isFocused) { _, focused in
            if focused {
                engineHolder.engine.beginEditing()
            } else {
                engineHolder.engine.endEditing()
            }
        }
    }

    private var suggestionPanel: some View {
        let items = engineHolder.engine.session.visibleItems
        let highlighted = engineHolder.engine.session.highlightedIndex
        let showsRecents = engineHolder.engine.session.showsRecents

        return VStack(alignment: .leading, spacing: 0) {
            if showsRecents {
                panelHeader("Recherches récentes")
            } else if engineHolder.engine.session.phase == .searching {
                panelHeader("Recherche…")
            } else if case .error(let message) = engineHolder.engine.session.phase {
                panelHeader(message)
            }

            ScrollView {
                LazyVStack(alignment: .leading, spacing: 0) {
                    ForEach(Array(items.enumerated()), id: \.offset) { index, item in
                        Button {
                            engineHolder.engine.select(item)
                            engineHolder.syncText()
                            isFocused = false
                            onCommit()
                        } label: {
                            rowContent(item, highlighted == index)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(.horizontal, 10)
                                .padding(.vertical, 8)
                                .background(
                                    highlighted == index
                                        ? palette.accentPrimary.opacity(0.12)
                                        : Color.clear
                                )
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
            .frame(maxHeight: 280)
        }
        .background(palette.backgroundPrimary)
        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 10, style: .continuous)
                .stroke(palette.borderSubtle, lineWidth: 1)
        )
        .shadow(color: .black.opacity(0.12), radius: 12, y: 4)
    }

    private func panelHeader(_ text: String) -> some View {
        Text(text)
            .font(.caption.weight(.semibold))
            .foregroundStyle(palette.textTertiary)
            .padding(.horizontal, 10)
            .padding(.top, 8)
            .padding(.bottom, 4)
    }
}

@MainActor
final class AutocompleteEngineHolder<Provider: SuggestionProvider>: ObservableObject where Provider.Entity: CanonicalEntity & Codable {
    let engine: AutocompleteEngine<Provider>
    @Published var queryText = ""
    @Published private(set) var selectedArtworkURL: URL?

    init(engine: AutocompleteEngine<Provider>) {
        self.engine = engine
        syncText()
    }

    func syncText() {
        queryText = engine.selection.query
        if let artist = engine.selection.selected as? ArtistRef {
            selectedArtworkURL = artist.artworkURL
        } else if let track = engine.selection.selected as? TrackRef {
            selectedArtworkURL = track.artworkURL
        } else {
            selectedArtworkURL = nil
        }
    }
}

struct ArtistResultRow: View {
    let artist: ArtistRef
    let isHighlighted: Bool
    let palette: ThemePalette

    var body: some View {
        HStack(spacing: 10) {
            ArtworkThumbnail(url: artist.artworkURL, palette: palette)
            VStack(alignment: .leading, spacing: 2) {
                Text(artist.displayName)
                    .font(.body.weight(.medium))
                    .foregroundStyle(palette.textPrimary)
                HStack(spacing: 8) {
                    if let albumCount = artist.albumCount {
                        Text("\(albumCount) albums")
                    }
                    if let artistType = artist.artistType, !artistType.isEmpty {
                        Text(artistType.capitalized)
                    }
                }
                .font(.caption)
                .foregroundStyle(palette.textSecondary)
            }
            Spacer(minLength: 0)
        }
    }
}

struct TrackResultRow: View {
    let track: TrackRef
    let isHighlighted: Bool
    let palette: ThemePalette

    var body: some View {
        HStack(spacing: 10) {
            ArtworkThumbnail(url: track.artworkURL, palette: palette)
            VStack(alignment: .leading, spacing: 2) {
                Text(track.title)
                    .font(.body.weight(.medium))
                    .foregroundStyle(palette.textPrimary)
                Text(track.artistName)
                    .font(.caption)
                    .foregroundStyle(palette.textSecondary)
                HStack(spacing: 8) {
                    if let album = track.albumTitle, !album.isEmpty {
                        Text(album)
                    }
                    if let year = track.releaseYear {
                        Text(String(year))
                    }
                    if let duration = track.formattedDuration {
                        Text(duration)
                    }
                }
                .font(.caption2)
                .foregroundStyle(palette.textTertiary)
            }
            Spacer(minLength: 0)
        }
    }
}

private struct ArtworkThumbnail: View {
    let url: URL?
    let palette: ThemePalette

    var body: some View {
        Group {
            if let url {
                AsyncImage(url: url) { phase in
                    switch phase {
                    case .success(let image):
                        image
                            .resizable()
                            .scaledToFill()
                    default:
                        placeholder
                    }
                }
            } else {
                placeholder
            }
        }
        .frame(width: 36, height: 36)
        .clipShape(RoundedRectangle(cornerRadius: 6, style: .continuous))
    }

    private var placeholder: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 6, style: .continuous)
                .fill(palette.backgroundSecondary)
            Image(systemName: "music.note")
                .foregroundStyle(palette.textTertiary)
        }
    }
}

struct SmartSearchTextField: NSViewRepresentable {
    let placeholder: String
    @Binding var text: String
    var onTextChange: (String) -> Void
    var onMoveHighlight: (Int) -> Void
    var onSelectHighlighted: () -> Void
    var onDismiss: () -> Void
    var onBeginEditing: () -> Void
    var onEndEditing: () -> Void
    var onClearWithCommand: () -> Void

    func makeNSView(context: Context) -> KeyableNSTextField {
        let field = KeyableNSTextField()
        field.placeholderString = placeholder
        field.isEditable = true
        field.isSelectable = true
        field.isBordered = true
        field.isBezeled = true
        field.bezelStyle = .roundedBezel
        field.focusRingType = .exterior
        field.font = NSFont.systemFont(ofSize: NSFont.systemFontSize)
        field.delegate = context.coordinator
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
        var parent: SmartSearchTextField
        var lastSyncedText = ""

        init(parent: SmartSearchTextField) {
            self.parent = parent
        }

        func controlTextDidChange(_ notification: Notification) {
            guard let field = notification.object as? NSTextField else { return }
            let value = field.stringValue
            lastSyncedText = value
            if parent.text != value {
                parent.text = value
            }
            parent.onTextChange(value)
        }

        func controlTextDidBeginEditing(_ notification: Notification) {
            parent.onBeginEditing()
        }

        func controlTextDidEndEditing(_ notification: Notification) {
            parent.onEndEditing()
        }

        func control(_ control: NSControl, textView: NSTextView, doCommandBy commandSelector: Selector) -> Bool {
            switch commandSelector {
            case #selector(NSResponder.moveUp(_:)):
                parent.onMoveHighlight(-1)
                return true
            case #selector(NSResponder.moveDown(_:)):
                parent.onMoveHighlight(1)
                return true
            case #selector(NSResponder.insertNewline(_:)):
                parent.onSelectHighlighted()
                return true
            case #selector(NSResponder.cancelOperation(_:)):
                parent.onDismiss()
                return true
            case #selector(NSResponder.deleteBackward(_:)):
                guard NSEvent.modifierFlags.contains(.command) else { return false }
                parent.onClearWithCommand()
                if let field = control as? NSTextField {
                    field.stringValue = ""
                    lastSyncedText = ""
                    parent.text = ""
                    parent.onTextChange("")
                }
                return true
            default:
                return false
            }
        }
    }
}
