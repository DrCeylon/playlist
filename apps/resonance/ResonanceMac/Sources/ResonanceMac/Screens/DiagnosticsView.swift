import ResonanceCore
import ResonanceDesign
import SwiftUI

struct DiagnosticsView: View {
    @StateObject private var viewModel: DiagnosticsViewModel
    @EnvironmentObject private var themeManager: ThemeManager

    init(service: any DiagnosticsServing = PythonEngineBridgeService()) {
        _viewModel = StateObject(wrappedValue: DiagnosticsViewModel(service: service))
    }

    var body: some View {
        ThemedScreen {
            let palette = ThemePalette(theme: themeManager.active)

            VStack(alignment: .leading, spacing: 20) {
                header(palette: palette)
                content(palette: palette)
            }
            .padding(24)
        }
        .navigationTitle("Laboratoire")
        .task {
            await viewModel.refresh()
        }
        .refreshable {
            await viewModel.refresh()
        }
    }

    @ViewBuilder
    private func header(palette: ThemePalette) -> some View {
        HStack(alignment: .center) {
            Label("Diagnostics Engine Bridge", systemImage: "flask")
                .font(.title2.weight(.semibold))
                .foregroundStyle(palette.textPrimary)
            Spacer()
            Picker("Mode", selection: $viewModel.displayMode) {
                ForEach(DiagnosticsViewModel.DisplayMode.allCases) { mode in
                    Text(mode.title).tag(mode)
                }
            }
            .pickerStyle(.segmented)
            .frame(maxWidth: 260)
        }
    }

    @ViewBuilder
    private func content(palette: ThemePalette) -> some View {
        switch viewModel.screenState {
        case .disconnected, .running:
            HStack(spacing: 12) {
                ProgressView()
                Text("Chargement des diagnostics…")
                    .foregroundStyle(palette.textSecondary)
            }
        case .failed(let message):
            VStack(alignment: .leading, spacing: 12) {
                Label(message, systemImage: "exclamationmark.triangle")
                    .foregroundStyle(palette.statusWarning)
                if viewModel.displayMode == .architect, let detail = viewModel.architectErrorDetail {
                    Text(detail)
                        .font(.caption.monospaced())
                        .foregroundStyle(palette.textTertiary)
                        .textSelection(.enabled)
                }
                Button("Réessayer") {
                    Task { await viewModel.refresh() }
                }
                .buttonStyle(.borderedProminent)
                .tint(palette.accentPrimary)
            }
        case .connected, .completed:
            if let snapshot = viewModel.snapshot {
                summaryCard(snapshot: snapshot, palette: palette)
                providersSection(snapshot: snapshot, palette: palette)
                if !snapshot.summary.recentReports.isEmpty {
                    reportsSection(snapshot: snapshot, palette: palette)
                }
                timelineSection(events: viewModel.filteredEvents(), palette: palette)
                if viewModel.displayMode == .architect {
                    architectDetails(snapshot: snapshot, palette: palette)
                }
            }
        }
    }

    @ViewBuilder
    private func summaryCard(snapshot: DiagnosticsSnapshot, palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Résumé")
                .font(.headline)
                .foregroundStyle(palette.textPrimary)
            HStack(spacing: 16) {
                metric(title: "Bridge", value: snapshot.summary.bridgeStatus, palette: palette)
                metric(title: "Moteur", value: snapshot.engineVersion, palette: palette)
                metric(title: "Plateforme", value: snapshot.summary.platform, palette: palette)
                metric(title: "Durée", value: "\(snapshot.summary.executionMS) ms", palette: palette)
            }
            HStack(spacing: 16) {
                metric(
                    title: "Cache catalogue",
                    value: "\(snapshot.summary.catalogCacheEntries)",
                    palette: palette
                )
                metric(
                    title: "Cache identité",
                    value: "\(snapshot.summary.identityCacheEntries)",
                    palette: palette
                )
                metric(title: "Pays", value: snapshot.summary.countryCode.uppercased(), palette: palette)
            }
        }
        .padding(16)
        .background(palette.backgroundSecondary)
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
    }

    @ViewBuilder
    private func providersSection(snapshot: DiagnosticsSnapshot, palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Providers")
                .font(.headline)
                .foregroundStyle(palette.textPrimary)
            ForEach(snapshot.summary.activeProviders) { provider in
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(provider.displayName)
                            .font(.body.weight(.medium))
                        if !provider.unavailableReason.isEmpty {
                            Text(provider.unavailableReason)
                                .font(.caption)
                                .foregroundStyle(palette.textTertiary)
                        }
                    }
                    Spacer()
                    statusChip(
                        label: provider.isAvailable ? "Disponible" : "Indisponible",
                        isPositive: provider.isAvailable,
                        palette: palette
                    )
                    if provider.isConnected {
                        statusChip(label: "Connecté", isPositive: true, palette: palette)
                    }
                }
                .padding(.vertical, 4)
            }
        }
    }

    @ViewBuilder
    private func reportsSection(snapshot: DiagnosticsSnapshot, palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Derniers rapports d'import")
                .font(.headline)
                .foregroundStyle(palette.textPrimary)
            ForEach(snapshot.summary.recentReports) { report in
                VStack(alignment: .leading, spacing: 4) {
                    Text(report.playlistName)
                        .font(.body.weight(.medium))
                    Text("\(report.generatedAt) · +\(report.added) · introuvables \(report.notFound) · erreurs \(report.errors)")
                        .font(.caption)
                        .foregroundStyle(palette.textSecondary)
                }
                .padding(.vertical, 4)
            }
            Text("Dossier : \(snapshot.summary.reportsDirectory)")
                .font(.caption)
                .foregroundStyle(palette.textTertiary)
        }
    }

    @ViewBuilder
    private func timelineSection(events: [DiagnosticEvent], palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Timeline")
                .font(.headline)
                .foregroundStyle(palette.textPrimary)
            if events.isEmpty {
                Text("Aucun événement pour le moment.")
                    .font(.callout)
                    .foregroundStyle(palette.textSecondary)
            } else {
                ForEach(events) { event in
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text(event.timestampISO.isEmpty ? "—" : event.timestampISO)
                                .font(.caption.monospacedDigit())
                                .foregroundStyle(palette.textTertiary)
                            Text(event.phase)
                                .font(.caption.weight(.semibold))
                                .foregroundStyle(levelColor(event.level, palette: palette))
                            Spacer()
                        }
                        Text(event.message)
                            .font(.callout)
                            .foregroundStyle(palette.textPrimary)
                        if viewModel.displayMode == .architect, !event.payload.isEmpty {
                            Text(
                                event.payload.map { "\($0.key)=\($0.value)" }.joined(separator: " · ")
                            )
                            .font(.caption.monospaced())
                            .foregroundStyle(palette.textTertiary)
                        }
                    }
                    .padding(.vertical, 4)
                }
            }
        }
    }

    @ViewBuilder
    private func architectDetails(snapshot: DiagnosticsSnapshot, palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Détails JSON (architecte)")
                .font(.headline)
                .foregroundStyle(palette.textPrimary)
            Text("Cache catalogue activé : \(snapshot.summary.catalogCacheEnabled ? "oui" : "non")")
                .font(.caption)
                .foregroundStyle(palette.textSecondary)
            Text("\(snapshot.events.count) événements bridge enregistrés")
                .font(.caption)
                .foregroundStyle(palette.textSecondary)
        }
        .padding(16)
        .background(palette.backgroundSecondary)
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
    }

    private func metric(title: String, value: String, palette: ThemePalette) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption)
                .foregroundStyle(palette.textTertiary)
            Text(value)
                .font(.callout.weight(.semibold))
                .foregroundStyle(palette.textPrimary)
        }
    }

    private func statusChip(label: String, isPositive: Bool, palette: ThemePalette) -> some View {
        Text(label)
            .font(.caption.weight(.medium))
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(isPositive ? palette.statusSuccess.opacity(0.15) : palette.statusWarning.opacity(0.15))
            .foregroundStyle(isPositive ? palette.statusSuccess : palette.statusWarning)
            .clipShape(Capsule())
    }

    private func levelColor(_ level: DiagnosticLevel, palette: ThemePalette) -> Color {
        switch level {
        case .debug:
            return palette.textTertiary
        case .info:
            return palette.accentPrimary
        case .warning:
            return palette.statusWarning
        case .error:
            return palette.statusError
        }
    }
}
