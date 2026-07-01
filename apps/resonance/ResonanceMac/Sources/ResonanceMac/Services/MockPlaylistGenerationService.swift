import Foundation
import ResonanceCore

public struct MockPlaylistGenerationService: PlaylistGenerationServing {
    public init() {}

    public func validate(request: PlaylistGenerationRequest) -> ValidationResult {
        PlaylistGenerationValidator.validate(request)
    }

    public func generate(request: PlaylistGenerationRequest) async throws -> PlaylistGenerationResult {
        let validation = validate(request: request)
        guard validation.isValid else {
            throw PlaylistBuilderError.validationFailed(validation)
        }

        try await Task.sleep(nanoseconds: 350_000_000)

        let trackCount = min(max(request.targetTrackCount ?? 12, 3), 24)
        let seed = request.seeds.first ?? SeedReference(artist: "Artiste", title: "Morceau")
        let keyword = request.keywords.first ?? "découverte"
        let sectionName = sectionTitle(for: request.energyCurve.profile)

        let tracks = (1...trackCount).map { index in
            GeneratedTrackPreview(
                artist: seed.artist.isEmpty ? "Artiste \(index)" : seed.artist,
                title: seed.title.isEmpty ? "\(keyword.capitalized) #\(index)" : "\(seed.title) (\(index))",
                section: sectionName,
                score: max(0.55, 0.95 - Double(index) * 0.015),
                confidence: index % 3 == 0 ? .high : .medium,
                source: "mock"
            )
        }

        let average = tracks.map(\.score).reduce(0, +) / Double(tracks.count)
        return PlaylistGenerationResult(
            playlistName: request.name.trimmingCharacters(in: .whitespacesAndNewlines),
            sections: [GeneratedSectionPreview(name: sectionName, tracks: tracks)],
            averageScore: average,
            providerID: request.providerID
        )
    }

    private func sectionTitle(for profile: EnergyCurveProfile) -> String {
        switch profile {
        case .chill:
            return "Warm-up"
        case .steady:
            return "Cruise"
        case .rising:
            return "Montée"
        case .party:
            return "Peak"
        case .maxFromStart:
            return "Impact"
        case .random:
            return "Exploration"
        }
    }
}

public enum PlaylistBuilderError: Error, Equatable {
    case validationFailed(ValidationResult)
}
