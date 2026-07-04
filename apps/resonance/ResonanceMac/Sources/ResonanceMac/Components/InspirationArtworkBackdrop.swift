import AppKit
import SwiftUI

enum ArtworkPaletteExtractor {
    static func dominantColor(from image: NSImage) -> Color? {
        let targetSize = NSSize(width: 1, height: 1)
        let sample = NSImage(size: targetSize)
        sample.lockFocus()
        image.draw(
            in: NSRect(origin: .zero, size: targetSize),
            from: NSRect(origin: .zero, size: image.size),
            operation: .copy,
            fraction: 1
        )
        sample.unlockFocus()

        guard let bitmap = sample.representations.first as? NSBitmapImageRep,
              let nsColor = bitmap.colorAt(x: 0, y: 0) else {
            return nil
        }
        return Color(nsColor: nsColor)
    }
}

struct InspirationArtworkBackdrop: View {
    let artworkURL: URL?
    let palette: ThemePalette

    @State private var accentColor: Color?

    var body: some View {
        ZStack {
            palette.backgroundPrimary

            if artworkURL != nil {
                AsyncImage(url: artworkURL, transaction: Transaction(animation: .easeOut(duration: 0.35))) { phase in
                    switch phase {
                    case .success(let image):
                        image
                            .resizable()
                            .scaledToFill()
                            .blur(radius: 56)
                            .scaleEffect(1.15)
                            .opacity(0.55)
                    default:
                        EmptyView()
                    }
                }

                if let accentColor {
                    LinearGradient(
                        colors: [
                            accentColor.opacity(0.38),
                            palette.backgroundPrimary.opacity(0.9),
                        ],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                } else {
                    palette.backgroundPrimary.opacity(0.84)
                }
            }
        }
        .clipped()
        .animation(.easeOut(duration: 0.35), value: artworkURL)
        .animation(.easeOut(duration: 0.35), value: accentColor)
        .task(id: artworkURL) {
            await loadPalette(from: artworkURL)
        }
    }

    @MainActor
    private func loadPalette(from url: URL?) async {
        guard let url else {
            accentColor = nil
            return
        }

        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            guard let image = NSImage(data: data) else {
                accentColor = nil
                return
            }
            accentColor = ArtworkPaletteExtractor.dominantColor(from: image)
        } catch {
            accentColor = nil
        }
    }
}
