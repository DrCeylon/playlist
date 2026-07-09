import ResonanceCore
import XCTest

private enum AutocompleteTestSupport {
    /// Waits until the engine reaches a terminal search phase instead of relying on wall-clock sleeps.
    static func waitForSearchCompletion<Provider: SuggestionProvider>(
        _ engine: AutocompleteEngine<Provider>,
        timeout: TimeInterval = 2.0,
        file: StaticString = #filePath,
        line: UInt = #line
    ) async {
        let deadline = Date().addingTimeInterval(timeout)
        while Date() < deadline {
            let phase = await MainActor.run { engine.session.phase }
            switch phase {
            case .ready, .error:
                return
            case .idle, .debouncing, .searching:
                try? await Task.sleep(nanoseconds: 5_000_000)
            }
        }
        let phase = await MainActor.run { engine.session.phase }
        XCTFail(
            "Timed out waiting for autocomplete completion; last phase=\(String(describing: phase))",
            file: file,
            line: line
        )
    }
}

final class AutocompleteEngineTests: XCTestCase {
    func testDebounceReturnsResults() async {
        let engine = await MainActor.run {
            AutocompleteEngine(
                provider: MockArtistSuggestionProvider(),
                entityKind: .artist,
                debounceInterval: 0.05
            )
        }
        await MainActor.run {
            engine.updateQuery("ky")
            XCTAssertEqual(engine.session.phase, .debouncing)
        }

        // Debounce must delay the search while the interval has not elapsed.
        try? await Task.sleep(nanoseconds: 25_000_000)
        await MainActor.run {
            XCTAssertEqual(engine.session.phase, .debouncing)
        }

        await AutocompleteTestSupport.waitForSearchCompletion(engine)
        await MainActor.run {
            XCTAssertEqual(engine.session.phase, .ready)
            XCTAssertFalse(engine.session.results.isEmpty)
            XCTAssertTrue(engine.session.results.contains { $0.displayName == "Kygo" })
        }
    }

    func testSelectHighlightedChoosesFirstWhenNoHighlight() async {
        let engine = await MainActor.run {
            AutocompleteEngine(provider: MockArtistSuggestionProvider(), entityKind: .artist, debounceInterval: 0)
        }
        await MainActor.run { engine.updateQuery("mu") }
        await AutocompleteTestSupport.waitForSearchCompletion(engine)
        await MainActor.run {
            XCTAssertEqual(engine.session.phase, .ready)
            XCTAssertFalse(engine.session.results.isEmpty)
            let selected = engine.selectHighlighted()
            XCTAssertEqual(selected?.displayName, "Muse")
            XCTAssertEqual(engine.selection.selected?.displayName, "Muse")
        }
    }

    func testKeyboardHighlightWraps() async {
        let engine = await MainActor.run {
            AutocompleteEngine(provider: MockArtistSuggestionProvider(), entityKind: .artist, debounceInterval: 0)
        }
        await MainActor.run { engine.updateQuery("a") }
        await AutocompleteTestSupport.waitForSearchCompletion(engine)
        await MainActor.run {
            XCTAssertGreaterThanOrEqual(engine.session.visibleItems.count, 3)
            engine.moveHighlight(delta: 1)
            XCTAssertEqual(engine.session.highlightedIndex, 0)
            engine.moveHighlight(delta: -1)
            XCTAssertEqual(engine.session.highlightedIndex, engine.session.visibleItems.count - 1)
        }
    }

    func testRecentSearchRecordedOnSelection() async {
        let recents = InMemoryRecentSearchProvider()
        let engine = await MainActor.run {
            AutocompleteEngine(
                provider: MockArtistSuggestionProvider(),
                entityKind: .artist,
                recentSearchProvider: recents
            )
        }
        let artist = MockAutocompleteFixtures.artists[0]
        await MainActor.run { engine.select(artist) }

        let loaded: [ArtistRef] = recents.load(entityKind: .artist)
        XCTAssertEqual(loaded.first?.id, artist.id)
    }
}

final class AutocompleteCacheTests: XCTestCase {
    func testCacheStoresAndExpires() async {
        let cache = AutocompleteCache(maxEntries: 8, defaultTTL: 0.05)
        let artists = [ArtistRef(id: "muse", displayName: "Muse")]

        await cache.store(artists, entityKind: .artist, query: "muse", context: nil, ttl: 0.05)
        let hit: [ArtistRef]? = await cache.lookup(entityKind: .artist, query: "muse", context: nil)
        XCTAssertEqual(hit?.count, 1)

        try? await Task.sleep(nanoseconds: 80_000_000)
        let miss: [ArtistRef]? = await cache.lookup(entityKind: .artist, query: "muse", context: nil)
        XCTAssertNil(miss)
    }
}

final class AutocompleteBridgeContractsTests: XCTestCase {
    func testParseArtistSuggestion() {
        let payload: BridgeJSONObject = [
            "suggestions": .array([
                .object([
                    "kind": .string("artist"),
                    "id": .string("muse"),
                    "display_name": .string("Muse"),
                    "artwork_url": .string("https://example.com/artwork.jpg"),
                    "album_count": .number(10),
                ]),
            ]),
        ]
        let response = AutocompleteBridgeContracts.parseResponse(payload, entityKind: .artist)
        XCTAssertEqual(response.artists.count, 1)
        XCTAssertEqual(response.artists[0].displayName, "Muse")
        XCTAssertEqual(response.artists[0].albumCount, 10)
    }

    func testRequestDictionaryIncludesContext() {
        let request = AutocompleteRequest(
            entityKind: .track,
            query: "fire",
            context: AutocompleteContext(artistName: "Kygo", artistID: "kygo")
        )
        let dict = AutocompleteBridgeContracts.requestDictionary(request)
        guard case .object(let context) = dict["context"] else {
            return XCTFail("Missing context")
        }
        XCTAssertEqual(context["artist_name"], .string("Kygo"))
    }
}

final class MockTrackSuggestionProviderTests: XCTestCase {
    func testTrackSuggestionsFilterByArtistContext() async throws {
        let provider = MockTrackSuggestionProvider()
        let request = AutocompleteRequest(
            entityKind: .track,
            query: "fire",
            context: AutocompleteContext(artistName: "Kygo", artistID: "kygo")
        )
        let results = try await provider.suggestions(for: request)
        XCTAssertEqual(results.count, 1)
        XCTAssertEqual(results[0].title, "Firestone")
        XCTAssertEqual(results[0].artistName, "Kygo")
    }

    func testSetContextRefreshesTrackResults() async {
        let provider = MockTrackSuggestionProvider()
        let engine = await MainActor.run {
            AutocompleteEngine(provider: provider, entityKind: .track, debounceInterval: 0)
        }
        await MainActor.run { engine.updateQuery("star") }
        await AutocompleteTestSupport.waitForSearchCompletion(engine)
        await MainActor.run {
            XCTAssertEqual(engine.session.results.count, 1)
            XCTAssertEqual(engine.session.results[0].artistName, "Muse")
            engine.setContext(AutocompleteContext(artistName: "Kygo", artistID: "kygo"))
        }
        await AutocompleteTestSupport.waitForSearchCompletion(engine)
        await MainActor.run {
            XCTAssertEqual(engine.session.phase, .ready)
            XCTAssertTrue(engine.session.results.isEmpty)
        }
    }
}
