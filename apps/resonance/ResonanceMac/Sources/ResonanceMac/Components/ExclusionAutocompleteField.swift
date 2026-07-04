import ResonanceCore
import ResonanceDesign
import SwiftUI

struct ExclusionAutocompleteField: View {
    @Binding var rule: ExclusionRule
    let palette: ThemePalette
    let autocompleteService: any AutocompleteServing
    let seedArtistName: String
    let seedArtistID: String

    @StateObject private var artistHolder: AutocompleteEngineHolder<BridgeArtistSuggestionProvider>
    @StateObject private var trackHolder: AutocompleteEngineHolder<BridgeTrackSuggestionProvider>
    @StateObject private var genreHolder: AutocompleteEngineHolder<LocalGenreSuggestionProvider>

    init(
        rule: Binding<ExclusionRule>,
        palette: ThemePalette,
        autocompleteService: any AutocompleteServing,
        seedArtistName: String = "",
        seedArtistID: String = ""
    ) {
        _rule = rule
        self.palette = palette
        self.autocompleteService = autocompleteService
        self.seedArtistName = seedArtistName
        self.seedArtistID = seedArtistID
        _artistHolder = StateObject(
            wrappedValue: AutocompleteEngineHolder(
                engine: AutocompleteEngine(
                    provider: BridgeArtistSuggestionProvider(service: autocompleteService),
                    entityKind: .artist
                )
            )
        )
        _trackHolder = StateObject(
            wrappedValue: AutocompleteEngineHolder(
                engine: AutocompleteEngine(
                    provider: BridgeTrackSuggestionProvider(service: autocompleteService),
                    entityKind: .track
                )
            )
        )
        _genreHolder = StateObject(
            wrappedValue: AutocompleteEngineHolder(
                engine: AutocompleteEngine(
                    provider: LocalGenreSuggestionProvider(service: autocompleteService),
                    entityKind: .genre
                )
            )
        )
    }

    var body: some View {
        Group {
            switch rule.kind {
            case .artist:
                SmartAutocompleteField(
                    title: "Artiste à exclure",
                    placeholder: "Rechercher un artiste…",
                    engineHolder: artistHolder,
                    palette: palette,
                    rowContent: { artist, highlighted in
                        AnyView(ArtistResultRow(artist: artist, isHighlighted: highlighted, palette: palette))
                    },
                    onCommit: { syncArtistValue() }
                )
            case .track:
                SmartAutocompleteField(
                    title: "Morceau à exclure",
                    placeholder: "Rechercher un morceau…",
                    engineHolder: trackHolder,
                    palette: palette,
                    rowContent: { track, highlighted in
                        AnyView(TrackResultRow(track: track, isHighlighted: highlighted, palette: palette))
                    },
                    onCommit: { syncTrackValue() }
                )
            case .genre:
                SmartAutocompleteField(
                    title: "Genre à exclure",
                    placeholder: "Rechercher un genre…",
                    engineHolder: genreHolder,
                    palette: palette,
                    rowContent: { genre, highlighted in
                        AnyView(
                            Text(genre.displayName)
                                .font(.body)
                                .foregroundStyle(highlighted ? palette.accentPrimary : palette.textPrimary)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(.horizontal, 10)
                                .padding(.vertical, 8)
                        )
                    },
                    onCommit: { syncGenreValue() }
                )
            default:
                AppKitTextField(placeholder: placeholderForKind, text: $rule.value)
                    .frame(maxWidth: .infinity, minHeight: 28, alignment: .leading)
            }
        }
        .onAppear(perform: syncFromRule)
        .onChange(of: rule.kind) { _, _ in
            syncFromRule()
        }
    }

    private var placeholderForKind: String {
        switch rule.kind {
        case .album: return "Album à exclure"
        case .mood: return "Ambiance à exclure"
        case .language: return "Langue à exclure"
        default: return "Valeur à exclure"
        }
    }

    private func syncFromRule() {
        let value = rule.value
        switch rule.kind {
        case .artist:
            if value.isEmpty {
                artistHolder.engine.clearSelection()
            } else {
                artistHolder.engine.updateQuery(value)
            }
        case .track:
            if !seedArtistName.isEmpty || !seedArtistID.isEmpty {
                trackHolder.engine.setContext(
                    AutocompleteContext(artistName: seedArtistName, artistID: seedArtistID)
                )
            }
            if value.isEmpty {
                trackHolder.engine.clearSelection()
            } else {
                trackHolder.engine.updateQuery(value)
            }
        case .genre:
            if value.isEmpty {
                genreHolder.engine.clearSelection()
            } else {
                genreHolder.engine.updateQuery(value)
            }
        default:
            break
        }
    }

    private func syncArtistValue() {
        if let artist = artistHolder.engine.selection.selected {
            rule.value = artist.displayName
        } else {
            rule.value = artistHolder.engine.selection.query
        }
    }

    private func syncTrackValue() {
        if let track = trackHolder.engine.selection.selected {
            rule.value = track.title
        } else {
            rule.value = trackHolder.engine.selection.query
        }
    }

    private func syncGenreValue() {
        if let genre = genreHolder.engine.selection.selected {
            rule.value = genre.displayName
        } else {
            rule.value = genreHolder.engine.selection.query
        }
    }
}
