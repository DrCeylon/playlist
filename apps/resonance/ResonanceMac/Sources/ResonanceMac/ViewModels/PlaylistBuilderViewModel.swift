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
    @Published var seedArtist = ""
    @Published var seedTrack = ""
    @Published var keywordsText = ""
    @Published var targetTrackCountText = "50"
    @Published var targetDurationText = ""
    @Published var energyProfile: EnergyCurveProfile = .rising
    @Published var exclusions: [ExclusionRule] = []
    @Published var validationErrors: [ValidationError] = []
    @Published var screenState: ScreenState = .editing
    @Published var previewResult: PlaylistGenerationResult?

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

    func buildRequest() -> PlaylistGenerationRequest {
        let keywords = keywordsText
            .split { $0 == "," || $0 == ";" || $0 == "\n" }
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }

        let seeds: [SeedReference]
        let trimmedArtist = seedArtist.trimmingCharacters(in: .whitespacesAndNewlines)
        let trimmedTrack = seedTrack.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmedArtist.isEmpty && trimmedTrack.isEmpty {
            seeds = []
        } else {
            seeds = [SeedReference(artist: trimmedArtist, title: trimmedTrack)]
        }

        return PlaylistGenerationRequest(
            name: name,
            providerID: .appleMusic,
            seeds: seeds,
            keywords: keywords,
            description: descriptionText,
            targetTrackCount: Int(targetTrackCountText.trimmingCharacters(in: .whitespacesAndNewlines)),
            targetDurationMinutes: Int(targetDurationText.trimmingCharacters(in: .whitespacesAndNewlines)),
            energyCurve: EnergyCurveOption(profile: energyProfile),
            exclusions: exclusions,
            playlistTheme: keywords.joined(separator: ", ")
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
        do {
            previewResult = try await service.generate(request: request)
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
}