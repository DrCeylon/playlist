import ResonanceCore
import ResonanceDesign
import SwiftUI

struct BoundedScrollScreen<Content: View>: View {
    @ViewBuilder let content: () -> Content

    var body: some View {
        ScrollView {
            content()
        }
        .scrollIndicators(.visible)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
    }
}
