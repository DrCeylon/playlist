import Foundation
import ResonanceCore

@MainActor
final class PlaylistBuilderViewModel: ObservableObject {
    enum ScreenState: Equatable {
        case editing
        case generating
        case preview
    }

    @Published var name = ""
    @Published var descriptionText = ""
    @Published var seedArtist: ArtistRef?
    @Published var seedTrack: TrackRef?
    @Published var keywords: [KeywordRef] = []
    @Published var targetTrackCountText = "50"
    @Published var targetDurationText = ""
    @Published var energyProfile: EnergyCurveProfile = .rising
    @Published var exclusions: [ExclusionRule] = []
    @Published var validationErrors: [ValidationError] = []
    @Published var screenState: ScreenState = .editing
    @Published var previewResult: PlaylistGenerationResult?
    @Published var previewSourceLabel = "Aperçu mock"
    @Published var bridgeFallbackMessage: String?

    let providerOptions = DefaultProviders.options
    let selectedProvider = DefaultProviders.options.first { $0.providerID == .appleMusic }

    private let service: any PlaylistGenerationServing

    init(service: any PlaylistGenerationServing = MockPlaylistGenerationService()) {
        self.service = service
    }

    var isValid: Bool {
        validationErrors.isEmpty
    }

    var canGenerate: Bool {
        screenState != .generating && validationErrors.isEmpty
    }

    var hasSeedOrKeywords: Bool {
        seedArtist != nil || seedTrack != nil || !keywords.isEmpty
    }

    func buildRequest() -> PlaylistGenerationRequest {
        let keywordLabels = keywords.map(\.label)

        let seeds: [SeedReference]
        let artistName = seedArtist?.displayName.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        let trackTitle = seedTrack?.title.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        if artistName.isEmpty && trackTitle.isEmpty {
            seeds = []
        } else {
            seeds = [SeedReference(artist: artistName, title: trackTitle)]
        }

        return PlaylistGenerationRequest(
            name: name,
            providerID: .appleMusic,
            seeds: seeds,
            keywords: keywordLabels,
            description: descriptionText,
            targetTrackCount: Int(targetTrackCountText.trimmingCharacters(in: .whitespacesAndNewlines)),
            targetDurationMinutes: Int(targetDurationText.trimmingCharacters(in: .whitespacesAndNewlines)),
            energyCurve: EnergyCurveOption(profile: energyProfile),
            exclusions: exclusions,
            playlistTheme: keywordLabels.joined(separator: ", ")
        )
    }

    func validateForm() {
        validationErrors = service.validate(request: buildRequest()).errors
    }

    func addExclusion() {
        exclusions.append(ExclusionRule())
        validateForm()
    }

    func removeExclusion(_ rule: ExclusionRule) {
        exclusions.removeAll { $0.id == rule.id }
        validateForm()
    }

    func generate() async {
        let request = buildRequest()
        validationErrors = service.validate(request: request).errors
        guard validationErrors.isEmpty else { return }

        screenState = .generating
        bridgeFallbackMessage = nil
        do {
            previewResult = try await service.generate(request: request)
            if service is PythonEngineBridgeService {
                previewSourceLabel = "Aperçu moteur Python"
            } else if let firstTrack = previewResult?.sections.first?.tracks.first, firstTrack.source == "mock" {
                previewSourceLabel = "Aperçu mock — bridge indisponible"
                bridgeFallbackMessage = "Le moteur Python n'a pas répondu ; aperçu local utilisé."
            } else {
                previewSourceLabel = "Aperçu mock"
            }
            screenState = .preview
        } catch let error as PlaylistBuilderError {
            if case .validationFailed(let result) = error {
                validationErrors = result.errors
            }
            screenState = .editing
        } catch {
            validationErrors = [
                ValidationError(field: "generate", message: "La génération a échoué.")
            ]
            screenState = .editing
        }
    }

    func backToEditing() {
        screenState = .editing
    }

    func loadFromHistory(_ request: PlaylistGenerationRequest) {
        name = request.name
        descriptionText = request.description
        targetTrackCountText = request.targetTrackCount.map(String.init) ?? targetTrackCountText
        targetDurationText = request.targetDurationMinutes.map(String.init) ?? ""
        energyProfile = request.energyCurve.profile
        exclusions = request.exclusions
        keywords = request.keywords.map { KeywordRef(id: UUID().uuidString, label: $0) }

        if let seed = request.seeds.first {
            let artistName = seed.artist.trimmingCharacters(in: .whitespacesAndNewlines)
            let trackTitle = seed.title.trimmingCharacters(in: .whitespacesAndNewlines)
            seedArtist = artistName.isEmpty
                ? nil
                : ArtistRef(id: "history:\(artistName)", displayName: artistName)
            seedTrack = trackTitle.isEmpty
                ? nil
                : TrackRef(
                    id: "history:\(trackTitle)",
                    title: trackTitle,
                    artistName: artistName
                )
        } else {
            seedArtist = nil
            seedTrack = nil
        }

        previewResult = nil
        previewSourceLabel = "Aperçu moteur Python"
        bridgeFallbackMessage = nil
        validationErrors = []
        screenState = .editing
    }
}
