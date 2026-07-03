import AppKit
import Foundation

enum MusicAppLink {
    static func searchTerm(artist: String, title: String, album: String = "") -> String {
        let artist = artist.trimmingCharacters(in: .whitespacesAndNewlines)
        let title = title.trimmingCharacters(in: .whitespacesAndNewlines)
        let album = album.trimmingCharacters(in: .whitespacesAndNewlines)
        if !album.isEmpty {
            return [artist, title, album].filter { !$0.isEmpty }.joined(separator: " ")
        }
        if artist.isEmpty { return title }
        if title.isEmpty { return artist }
        return "\(artist) \(title)"
    }

    static func searchURL(artist: String, title: String, album: String = "") -> URL? {
        let term = searchTerm(artist: artist, title: title, album: album)
        guard !term.isEmpty else { return nil }
        var components = URLComponents()
        components.scheme = "music"
        components.host = "music.apple.com"
        components.path = "/search"
        components.queryItems = [URLQueryItem(name: "term", value: term)]
        return components.url
    }

    static func openSearch(artist: String, title: String, album: String = "") {
        if let url = searchURL(artist: artist, title: title, album: album) {
            openURL(url)
            return
        }
        openApp()
    }

    static func openURLString(_ urlString: String) {
        let trimmed = urlString.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            openApp()
            return
        }
        if let url = URL(string: trimmed) {
            openURL(url)
            return
        }
        openApp()
    }

    static func openURL(_ url: URL) {
        NSWorkspace.shared.open(url)
    }

    static func openApp() {
        ClipboardSupport.openMusicApp()
    }
}
