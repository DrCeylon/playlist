import Foundation
import ResonanceCore

@MainActor
final class SmartInputFormEngines: ObservableObject {
    let autocompleteService: any AutocompleteServing
    let artistHolder: AutocompleteEngineHolder<BridgeArtistSuggestionProvider>
    let trackHolder: AutocompleteEngineHolder<BridgeTrackSuggestionProvider>
    let keywordHolder: AutocompleteEngineHolder<LocalKeywordSuggestionProvider>

    init(autocompleteService: any AutocompleteServing = MockAutocompleteService()) {
        self.autocompleteService = autocompleteService
        let artistEngine = AutocompleteEngine(
            provider: BridgeArtistSuggestionProvider(service: autocompleteService),
            entityKind: .artist
        )
        let trackEngine = AutocompleteEngine(
            provider: BridgeTrackSuggestionProvider(service: autocompleteService),
            entityKind: .track
        )
        let keywordEngine = AutocompleteEngine(
            provider: LocalKeywordSuggestionProvider(service: autocompleteService),
            entityKind: .keyword
        )
        artistHolder = AutocompleteEngineHolder(engine: artistEngine)
        trackHolder = AutocompleteEngineHolder(engine: trackEngine)
        keywordHolder = AutocompleteEngineHolder(engine: keywordEngine)
    }

    func syncFromViewModel(_ viewModel: PlaylistBuilderViewModel) {
        artistHolder.engine.setSelected(viewModel.seedArtist)
        trackHolder.engine.setSelected(viewModel.seedTrack)
        artistHolder.syncText()
        trackHolder.syncText()

        if let artist = viewModel.seedArtist {
            trackHolder.engine.setContext(
                AutocompleteContext(artistName: artist.displayName, artistID: artist.id)
            )
        } else {
            trackHolder.engine.setContext(nil)
        }
    }

    func pushToViewModel(_ viewModel: PlaylistBuilderViewModel) {
        viewModel.seedArtist = artistHolder.engine.selection.selected
        viewModel.seedTrack = trackHolder.engine.selection.selected
    }
}
