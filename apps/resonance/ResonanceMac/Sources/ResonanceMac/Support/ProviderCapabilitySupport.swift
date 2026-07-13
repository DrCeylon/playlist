import Foundation
import ResonanceCore

enum ProviderCapabilitySupport {
    static func supports(_ capability: ProviderCapability, providerID: ProviderID) -> Bool {
        if let option = DefaultProviders.options.first(where: { $0.providerID == providerID }) {
            return option.capabilities.contains(capability)
        }
        return false
    }

    static func supportsPushSync(providerID: ProviderID) -> Bool {
        supports(.playlistSync, providerID: providerID)
    }
}
