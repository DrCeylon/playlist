import Foundation

/// Human-readable labels for product UI — hides technical enums from end users.
public enum ProductDisplay {
    public static func mappingStatusLabel(_ status: PlaylistTrackMappingStatus) -> String {
        switch status {
        case .matched: return "Correspondance trouvée"
        case .missingLocally: return "Absent localement"
        case .missingOnProvider: return "Absent sur le service"
        case .duplicate: return "Doublon"
        case .metadataMismatch: return "Informations différentes"
        case .unresolved: return "À vérifier"
        }
    }

    public static func conflictKindLabel(_ kind: String) -> String {
        switch kind {
        case "duplicate_local": return "Doublon local"
        case "duplicate_remote": return "Doublon distant"
        case "metadata_mismatch": return "Informations différentes"
        case "order_mismatch": return "Ordre différent"
        case "rename_mismatch": return "Nom différent"
        case "deletion_local": return "Suppression locale"
        case "deletion_remote": return "Suppression distante"
        case "missing_local": return "Nouveau morceau distant"
        case "missing_remote": return "Morceau local uniquement"
        case "concurrent_modification": return "Modification simultanée"
        case "provider_link_mismatch": return "Liaison incorrecte"
        case "version_local_stale": return "Playlist modifiée"
        case "version_remote_stale": return "Service modifié"
        default: return "À résoudre"
        }
    }

    public static func conflictSeverityLabel(_ severity: String) -> String {
        switch severity {
        case "blocking": return "Bloquant"
        case "warning": return "Attention"
        case "info": return "Information"
        default: return "À vérifier"
        }
    }

    public static func resolutionStrategyLabel(_ strategy: String) -> String {
        switch strategy {
        case "keep_local": return "Garder la version locale"
        case "keep_remote": return "Garder la version du service"
        case "merge": return "Fusionner"
        case "ignore": return "Ignorer"
        case "defer": return "Décider plus tard"
        default: return strategy
        }
    }

    public static func syncActionKindLabel(_ kind: PlaylistSyncActionKind) -> String {
        switch kind {
        case .addTrack: return "Ajout"
        case .removeTrack: return "Retrait"
        case .reorder: return "Réorganisation"
        case .mapTrack: return "Mise à jour"
        case .renamePlaylist: return "Renommage"
        }
    }

    public static func syncModeLabel(_ mode: SyncMode) -> String {
        switch mode {
        case .dryRun: return "Aperçu"
        case .appendOnly: return "Ajouts uniquement"
        case .mirror: return "Copie exacte"
        case .manualResolve: return "Validation manuelle"
        }
    }

    public static func syncDirectionLabel(_ direction: PlaylistSyncDirection) -> String {
        switch direction {
        case .pullFromProvider: return "Récupérer depuis le service"
        case .pushToProvider: return "Envoyer vers le service"
        case .bidirectionalPreview: return "Comparer les deux versions"
        }
    }

    public static func providerCapabilityLabel(_ capability: ProviderCapability) -> String {
        switch capability {
        case .catalogSearch: return "Recherche"
        case .libraryResolve: return "Bibliothèque"
        case .playlistDelivery: return "Création de playlists"
        case .playlistLibraryBrowse: return "Playlists du service"
        case .playlistSync: return "Synchronisation"
        case .publicPlaylistImport: return "Playlists publiques"
        case .authentication: return "Connexion de compte"
        case .experimental: return "Expérimental"
        }
    }

    public static func providerAuthStateLabel(_ state: ProviderAuthState) -> String {
        switch state {
        case .connected: return "Connecté"
        case .configured: return "Configuré"
        case .disconnected: return "Non connecté"
        case .expired: return "Session expirée"
        case .error: return "Erreur de connexion"
        case .experimentalUnavailable: return "Indisponible"
        }
    }

    public static func operationStatusLabel(_ status: String) -> String {
        switch status {
        case "pending": return "En attente"
        case "running": return "En cours"
        case "completed": return "Terminée"
        case "failed": return "Échec"
        case "blocked_conflict": return "Bloquée — conflits"
        case "cancelled": return "Annulée"
        default: return "Inconnu"
        }
    }
}
