import Foundation
import ResonanceCore

@MainActor
final class SyncViewModel: ObservableObject {
    enum Step: Equatable {
        case selectPlaylist
        case preview
        case resolveConflicts
        case completed
    }

    @Published private(set) var step: Step = .selectPlaylist
    @Published private(set) var selectedPlaylistID: String?
    @Published private(set) var planResult: PlaylistSyncPlanResult?
    @Published private(set) var applyResult: PlaylistSyncApplyResult?
    @Published private(set) var isBusy = false
    @Published var actionFeedback: String?
    @Published var resolutionChoices: [String: String] = [:]

    var syncMode: SyncMode = .manualResolve
    var direction: PlaylistSyncDirection = .pullFromProvider

    private let service: any PlaylistLibraryServing

    init(service: any PlaylistLibraryServing) {
        self.service = service
    }

    func selectPlaylist(_ playlistID: String) {
        selectedPlaylistID = playlistID
        planResult = nil
        applyResult = nil
        resolutionChoices = [:]
        step = .selectPlaylist
        actionFeedback = nil
    }

    func reset() {
        selectedPlaylistID = nil
        planResult = nil
        applyResult = nil
        resolutionChoices = [:]
        step = .selectPlaylist
        actionFeedback = nil
    }

    func previewPlan(for detail: ManagedPlaylistDetail) async {
        isBusy = true
        defer { isBusy = false }
        let summary = detail.summary
        let remoteID = summary.providerPlaylistID.isEmpty
            ? detail.summary.linkedRemoteRefs.first?.remotePlaylistID ?? ""
            : summary.providerPlaylistID
        do {
            guard let result = try await service.planSync(
                PlaylistSyncPlanRequest(
                    localPlaylistID: summary.localPlaylistID,
                    providerID: summary.providerID,
                    direction: direction,
                    syncMode: syncMode,
                    remotePlaylistID: remoteID
                )
            ) else {
                actionFeedback = "L'aperçu de synchronisation n'est pas disponible."
                return
            }
            planResult = result
            resolutionChoices = Dictionary(
                uniqueKeysWithValues: result.plan.conflicts.map { conflict in
                    let strategy = conflict.recommendedResolution.isEmpty ? "defer" : conflict.recommendedResolution
                    return (conflict.id, strategy)
                }
            )
            if result.plan.conflicts.isEmpty {
                step = .preview
            } else {
                step = .resolveConflicts
            }
            actionFeedback = nil
        } catch {
            actionFeedback = "Impossible de préparer la synchronisation."
        }
    }

    func updateResolution(conflictID: String, strategy: String) {
        resolutionChoices[conflictID] = strategy
    }

    func applyResolutions(for detail: ManagedPlaylistDetail) async {
        guard let planResult else { return }
        isBusy = true
        defer { isBusy = false }
        let summary = detail.summary
        let remoteID = summary.providerPlaylistID.isEmpty
            ? summary.linkedRemoteRefs.first?.remotePlaylistID ?? planResult.plan.remotePlaylistID
            : summary.providerPlaylistID
        let resolutions = resolutionChoices.map { ConflictResolutionChoice(conflictID: $0.key, strategy: $0.value) }
        do {
            if !resolutions.isEmpty {
                guard let resolved = try await service.resolveSyncConflicts(
                    PlaylistSyncResolveRequest(
                        localPlaylistID: summary.localPlaylistID,
                        providerID: summary.providerID,
                        direction: direction,
                        syncMode: syncMode,
                        remotePlaylistID: remoteID,
                        resolutions: resolutions
                    )
                ) else {
                    actionFeedback = "La résolution des différences n'est pas disponible."
                    return
                }
                self.planResult = resolved
                if !resolved.plan.conflicts.isEmpty {
                    actionFeedback = "\(resolved.plan.conflicts.count) différence(s) restent à traiter."
                    step = .resolveConflicts
                    return
                }
            }
            step = .preview
            actionFeedback = nil
        } catch {
            actionFeedback = "Impossible d'appliquer vos choix."
        }
    }

    func applyPlan(for detail: ManagedPlaylistDetail) async {
        guard let planResult else { return }
        if direction == .pushToProvider,
           !ProviderCapabilitySupport.supportsPushSync(providerID: detail.summary.providerID) {
            actionFeedback = "Ce service ne supporte pas l'envoi vers le fournisseur distant."
            return
        }
        isBusy = true
        defer { isBusy = false }
        let summary = detail.summary
        let remoteChecksum = summary.linkedRemoteRefs.first?.lastAppliedSnapshotChecksum ?? ""
        let remoteID = summary.providerPlaylistID.isEmpty
            ? summary.linkedRemoteRefs.first?.remotePlaylistID ?? planResult.plan.remotePlaylistID
            : summary.providerPlaylistID
        do {
            guard let result = try await service.applySync(
                PlaylistSyncApplyRequest(
                    localPlaylistID: summary.localPlaylistID,
                    providerID: summary.providerID,
                    direction: direction,
                    syncMode: syncMode,
                    confirmDestructive: false,
                    expectedLocalPlaylistVersion: summary.playlistVersion,
                    expectedRemoteSnapshotChecksum: remoteChecksum,
                    planChecksum: planResult.planChecksum,
                    remotePlaylistID: remoteID
                )
            ) else {
                actionFeedback = "L'application de la synchronisation n'est pas disponible."
                return
            }
            applyResult = result
            step = .completed
            actionFeedback = result.message
        } catch {
            actionFeedback = "La synchronisation n'a pas pu être appliquée."
        }
    }
}
