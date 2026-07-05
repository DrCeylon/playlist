import AppKit
import ResonanceDesign
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
    @State private var loadedImage: NSImage?

    var body: some View {
        ZStack {
            palette.backgroundPrimary

            if let loadedImage {
                Image(nsImage: loadedImage)
                    .resizable()
                    .scaledToFill()
                    .blur(radius: 48)
                    .scaleEffect(1.12)
                    .opacity(0.62)
                    .transition(.opacity)

                if let accentColor {
                    LinearGradient(
                        colors: [
                            accentColor.opacity(0.42),
                            accentColor.opacity(0.18),
                            palette.backgroundPrimary.opacity(0.55),
                        ],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                } else {
                    LinearGradient(
                        colors: [
                            palette.backgroundPrimary.opacity(0.15),
                            palette.backgroundPrimary.opacity(0.62),
                        ],
                        startPoint: .top,
                        endPoint: .bottom
                    )
                }
            }
        }
        .clipped()
        .animation(.easeOut(duration: 0.35), value: artworkURL)
        .animation(.easeOut(duration: 0.35), value: accentColor)
        .animation(.easeOut(duration: 0.35), value: loadedImage != nil)
        .task(id: artworkURL) {
            await loadArtwork(from: artworkURL)
        }
    }

    @MainActor
    private func loadArtwork(from url: URL?) async {
        guard let url else {
            loadedImage = nil
            accentColor = nil
            return
        }

        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            guard let image = NSImage(data: data) else {
                loadedImage = nil
                accentColor = nil
                return
            }
            loadedImage = image
            accentColor = ArtworkPaletteExtractor.dominantColor(from: image)
        } catch {
            loadedImage = nil
            accentColor = nil
        }
    }
}
