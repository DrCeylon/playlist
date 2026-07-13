import Foundation
import ResonanceCore

@MainActor
final class RemoteImportViewModel: ObservableObject {
    @Published var selectedProviderID: ProviderID = .appleMusic
    @Published private(set) var remotePlaylists: [RemotePlaylist] = []
    @Published private(set) var selectedSnapshot: RemotePlaylistSnapshot?
    @Published private(set) var importedDetail: ManagedPlaylistDetail?
    @Published private(set) var isBusy = false
    @Published var actionFeedback: String?

    private let libraryService: any PlaylistLibraryServing

    init(libraryService: any PlaylistLibraryServing) {
        self.libraryService = libraryService
    }

    var importableProviders: [ProviderOption] {
        DefaultProviders.options.filter { option in
            option.capabilities.contains(.playlistLibraryBrowse)
                || option.capabilities.contains(.publicPlaylistImport)
        }
    }

    func refreshRemotePlaylists() async {
        isBusy = true
        defer { isBusy = false }
        selectedSnapshot = nil
        importedDetail = nil
        do {
            remotePlaylists = try await libraryService.listRemotePlaylists(providerID: selectedProviderID)
            actionFeedback = remotePlaylists.isEmpty
                ? "Aucune playlist distante trouvée pour ce service."
                : nil
        } catch {
            remotePlaylists = []
            actionFeedback = "Impossible de charger les playlists distantes."
        }
    }

    func preview(remotePlaylistID: String) async {
        isBusy = true
        defer { isBusy = false }
        importedDetail = nil
        do {
            guard let snapshot = try await libraryService.getRemotePlaylist(
                providerID: selectedProviderID,
                remotePlaylistID: remotePlaylistID
            ) else {
                selectedSnapshot = nil
                actionFeedback = "Playlist distante introuvable."
                return
            }
            selectedSnapshot = snapshot
            actionFeedback = nil
        } catch {
            selectedSnapshot = nil
            actionFeedback = "Impossible de lire cette playlist distante."
        }
    }

    func importSelected() async {
        guard let snapshot = selectedSnapshot else { return }
        isBusy = true
        defer { isBusy = false }
        do {
            guard let detail = try await libraryService.importRemotePlaylist(
                remotePlaylist: snapshot,
                origin: .providerLibrary
            ) else {
                actionFeedback = "Import distant indisponible."
                return
            }
            importedDetail = detail
            actionFeedback = "Playlist importée dans votre bibliothèque locale."
        } catch {
            actionFeedback = "Import distant impossible."
        }
    }
}
