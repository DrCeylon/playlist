import AppKit
import Foundation

enum ApplicationIconConfigurator {
    static func applyIfNeeded() {
        guard let image = loadIconImage() else { return }
        NSApplication.shared.applicationIconImage = image
    }

    private static func loadIconImage() -> NSImage? {
        let bundles: [Bundle] = [Bundle.main, Bundle.module]
        let candidates: [(String, String?, String?)] = [
            ("AppIcon-512", "png", "Assets"),
            ("AppIcon-512", "png", nil),
            ("AppIcon-1024", "png", "Assets"),
            ("AppIcon", "icns", nil),
        ]

        for bundle in bundles {
            for (name, ext, subdirectory) in candidates {
                if let url = bundle.url(
                    forResource: name,
                    withExtension: ext,
                    subdirectory: subdirectory
                ),
                   let image = NSImage(contentsOf: url) {
                    image.size = NSSize(width: 512, height: 512)
                    image.isTemplate = false
                    return image
                }
            }
        }
        return nil
    }
}
