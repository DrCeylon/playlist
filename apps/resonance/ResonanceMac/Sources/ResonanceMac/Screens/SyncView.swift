import ResonanceCore
import ResonanceDesign
import SwiftUI

struct SyncView: View {
    @Binding var selection: SidebarItem?
    @EnvironmentObject private var themeManager: ThemeManager
    @EnvironmentObject private var workflow: AppWorkflowCoordinator
    @StateObject private var syncModel = SyncViewModel()

    var body: some View {
        ThemedScreen {
            let palette = ThemePalette(theme: themeManager.active)
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    header(palette: palette)
                    if let feedback = syncModel.actionFeedback ?? workflow.libraryStore.actionFeedback {
                        Text(feedback)
                            .font(.callout)
                            .foregroundStyle(palette.textSecondary)
                    }
                    switch syncModel.step {
                    case .selectPlaylist:
                        playlistPicker(palette: palette)
                    case .resolveConflicts:
                        conflictResolution(palette: palette)
                    case .preview:
                        planPreview(palette: palette)
                    case .completed:
                        completionPanel(palette: palette)
                    }
                }
                .padding(24)
            }
        }
        .navigationTitle("Synchronisation")
        .onAppear {
            syncModel.replaceService(workflow.engineBridge)
            if let selected = workflow.libraryStore.selectedDetail {
                syncModel.selectPlaylist(selected.summary.localPlaylistID)
            }
        }
        .refreshable { await workflow.libraryStore.refresh() }
    }

    @ViewBuilder
    private func header(palette: ThemePalette) -> some View {
        ProductSectionCard(title: "Synchroniser une playlist", palette: palette) {
            Text("Compare ta version locale avec celle du service musical, résous les différences, puis applique les changements.")
                .font(.callout)
                .foregroundStyle(palette.textSecondary)
        }
    }

    @ViewBuilder
    private func playlistPicker(palette: ThemePalette) -> some View {
        ProductSectionCard(title: "Choisir une playlist", palette: palette) {
            if workflow.libraryStore.playlists.isEmpty {
                ProductEmptyState(
                    title: "Aucune playlist",
                    message: "Crée ou importe une playlist avant de synchroniser.",
                    systemImage: "arrow.triangle.2.circlepath",
                    palette: palette
                )
            } else {
                ForEach(workflow.libraryStore.playlists) { playlist in
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(playlist.name)
                                .font(.callout.weight(.semibold))
                            Text("\(PlaylistLibraryDisplay.providerLabel(playlist.providerID)) · \(PlaylistLibraryDisplay.syncStatusLabel(playlist.syncStatus))")
                                .font(.caption)
                                .foregroundStyle(palette.textSecondary)
                        }
                        Spacer()
                        Button("Prévisualiser") {
                            Task {
                                syncModel.selectPlaylist(playlist.localPlaylistID)
                                await workflow.libraryStore.select(localPlaylistID: playlist.localPlaylistID)
                                if let detail = workflow.libraryStore.selectedDetail {
                                    await syncModel.previewPlan(for: detail)
                                }
                            }
                        }
                        .buttonStyle(.bordered)
                        .disabled(syncModel.isBusy)
                    }
                    .padding(.vertical, 4)
                }
            }
        }
    }

    @ViewBuilder
    private func conflictResolution(palette: ThemePalette) -> some View {
        guard let plan = syncModel.planResult?.plan else { return AnyView(EmptyView()) }
        return AnyView(
            ProductSectionCard(title: "Différences détectées", palette: palette) {
                VStack(alignment: .leading, spacing: 12) {
                    Text("\(plan.conflicts.count) élément(s) nécessitent votre attention.")
                        .font(.callout)
                        .foregroundStyle(palette.textSecondary)
                    ForEach(plan.conflicts) { conflict in
                        conflictRow(conflict, palette: palette)
                    }
                    HStack {
                        Button("Continuer") {
                            Task {
                                if let detail = workflow.libraryStore.selectedDetail {
                                    await syncModel.applyResolutions(for: detail)
                                }
                            }
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(syncModel.isBusy)
                        Button("Recommencer") { syncModel.reset() }
                            .buttonStyle(.bordered)
                    }
                }
            }
        )
    }

    @ViewBuilder
    private func conflictRow(_ conflict: PlaylistSyncConflict, palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(ProductDisplay.conflictKindLabel(conflict.conflictKind))
                    .font(.callout.weight(.semibold))
                Spacer()
                StatusChip(
                    label: ProductDisplay.conflictSeverityLabel(conflict.severity),
                    color: palette.statusWarning
                )
            }
            Text(conflict.message)
                .font(.caption)
                .foregroundStyle(palette.textSecondary)
            let options = conflict.availableResolutions.isEmpty
                ? ["keep_local", "keep_remote", "defer"]
                : conflict.availableResolutions
            Picker("Résolution", selection: resolutionBinding(for: conflict)) {
                ForEach(options, id: \.self) { strategy in
                    Text(ProductDisplay.resolutionStrategyLabel(strategy)).tag(strategy)
                }
            }
            .pickerStyle(.menu)
        }
        .padding(10)
        .background(palette.backgroundElevated, in: RoundedRectangle(cornerRadius: 8))
    }

    private func resolutionBinding(for conflict: PlaylistSyncConflict) -> Binding<String> {
        Binding(
            get: { syncModel.resolutionChoices[conflict.id] ?? conflict.recommendedResolution },
            set: { syncModel.updateResolution(conflictID: conflict.id, strategy: $0) }
        )
    }

    @ViewBuilder
    private func planPreview(palette: ThemePalette) -> some View {
        guard let planResult = syncModel.planResult else { return AnyView(EmptyView()) }
        let plan = planResult.plan
        return AnyView(
            VStack(alignment: .leading, spacing: 16) {
                ProductSectionCard(title: "Aperçu des changements", palette: palette) {
                    VStack(alignment: .leading, spacing: 8) {
                        comparisonHeader(plan: plan, palette: palette)
                        ProductMetricRow(title: "Ajouts", value: "\(plan.summary.additions)", palette: palette)
                        ProductMetricRow(title: "Retraits", value: "\(plan.summary.removals)", palette: palette)
                        ProductMetricRow(title: "Réorganisations", value: "\(plan.summary.reorders)", palette: palette)
                        ProductMetricRow(title: "Déjà identiques", value: "\(plan.summary.alreadyPresent)", palette: palette)
                    }
                }
                if !plan.actions.isEmpty {
                    ProductSectionCard(title: "Détail des opérations", palette: palette) {
                        ForEach(plan.actions) { action in
                            HStack {
                                Text(ProductDisplay.syncActionKindLabel(action.kind))
                                    .font(.caption.weight(.semibold))
                                    .frame(width: 100, alignment: .leading)
                                Text(action.title.isEmpty ? action.message : "\(action.artist) — \(action.title)")
                                    .font(.caption)
                                    .foregroundStyle(palette.textSecondary)
                                Spacer()
                            }
                        }
                    }
                }
                HStack {
                    Button("Appliquer") {
                        Task {
                            if let detail = workflow.libraryStore.selectedDetail {
                                await syncModel.applyPlan(for: detail)
                                await workflow.libraryStore.refresh()
                            }
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(syncModel.isBusy)
                    Button("Annuler") { syncModel.reset() }
                        .buttonStyle(.bordered)
                }
            }
        )
    }

    @ViewBuilder
    private func comparisonHeader(plan: PlaylistSyncPlan, palette: ThemePalette) -> some View {
        HStack {
            VStack(alignment: .leading) {
                Text("Locale").font(.caption).foregroundStyle(palette.textSecondary)
                Text(plan.playlistNameLocal).font(.callout.weight(.medium))
            }
            Spacer()
            Image(systemName: "arrow.left.arrow.right")
                .foregroundStyle(palette.textSecondary)
            Spacer()
            VStack(alignment: .trailing) {
                Text("Service").font(.caption).foregroundStyle(palette.textSecondary)
                Text(plan.playlistNameRemote).font(.callout.weight(.medium))
            }
        }
    }

    @ViewBuilder
    private func completionPanel(palette: ThemePalette) -> some View {
        ProductSectionCard(title: "Synchronisation terminée", palette: palette) {
            VStack(alignment: .leading, spacing: 12) {
                if let result = syncModel.applyResult {
                    Text(result.message)
                        .font(.callout)
                    ProductMetricRow(
                        title: "État",
                        value: PlaylistLibraryDisplay.syncStatusLabel(
                            PlaylistSyncStatus(rawValue: result.finalSyncStatus) ?? .pending
                        ),
                        palette: palette
                    )
                }
                HStack {
                    Button("Voir mes playlists") { selection = .playlists }
                        .buttonStyle(.borderedProminent)
                    Button("Synchroniser une autre") { syncModel.reset() }
                        .buttonStyle(.bordered)
                }
            }
        }
    }
}
