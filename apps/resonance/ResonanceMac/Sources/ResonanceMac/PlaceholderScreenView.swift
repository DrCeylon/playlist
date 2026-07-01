import ResonanceDesign
import SwiftUI

struct PlaceholderScreenView: View {
    let title: String
    let message: String

    var body: some View {
        ThemedScreen {
            VStack(alignment: .leading, spacing: 12) {
                Text(title)
                    .font(.largeTitle.weight(.semibold))
                Text(message)
                    .font(.body)
            }
            .padding(24)
        }
        .navigationTitle(title)
    }
}
