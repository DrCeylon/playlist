import ResonanceCore
import ResonanceDesign
import SwiftUI

struct KeywordTagField: View {
    let title: String
    @Binding var keywords: [KeywordRef]
    @ObservedObject var engineHolder: AutocompleteEngineHolder<KeywordRef>
    let palette: ThemePalette
    let onCommit: () -> Void

    @State private var draftQuery = ""
    @FocusState private var isInputFocused: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.caption)
                .foregroundStyle(palette.textSecondary)

            FlowLayout(spacing: 8) {
                ForEach(keywords) { keyword in
                    keywordChip(keyword)
                }
                tagInput
            }

            if engineHolder.engine.session.isPanelVisible {
                keywordSuggestionPanel
            }
        }
        .onAppear {
            engineHolder.engine.reloadRecents()
        }
    }

    private func keywordChip(_ keyword: KeywordRef) -> some View {
        HStack(spacing: 4) {
            Text(keyword.label)
                .font(.callout.weight(.medium))
            Button {
                keywords.removeAll { $0.id == keyword.id }
                onCommit()
            } label: {
                Image(systemName: "xmark")
                    .font(.caption2.weight(.bold))
            }
            .buttonStyle(.borderless)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(palette.accentPrimary.opacity(0.14))
        .foregroundStyle(palette.textPrimary)
        .clipShape(Capsule())
    }

    private var tagInput: some View {
        TextField("Ajouter un mot-clé", text: $draftQuery)
            .textFieldStyle(.roundedBorder)
            .frame(minWidth: 160)
            .focused($isInputFocused)
            .onSubmit(addDraftKeyword)
            .onChange(of: draftQuery) { _, value in
                engineHolder.engine.updateQuery(value)
                engineHolder.engine.beginEditing()
            }
            .onChange(of: isInputFocused) { _, focused in
                if focused {
                    engineHolder.engine.beginEditing()
                } else {
                    engineHolder.engine.endEditing()
                }
            }
    }

    private var keywordSuggestionPanel: some View {
        let items = engineHolder.engine.session.visibleItems
        return VStack(alignment: .leading, spacing: 0) {
            if engineHolder.engine.session.showsRecents {
                Text("Récents et suggestions")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(palette.textTertiary)
                    .padding(.horizontal, 8)
                    .padding(.top, 6)
            }
            ForEach(items) { item in
                Button {
                    addKeyword(item)
                } label: {
                    Text(item.label)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 6)
                }
                .buttonStyle(.plain)
            }
        }
        .background(palette.backgroundPrimary)
        .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 8, style: .continuous)
                .stroke(palette.borderSubtle, lineWidth: 1)
        )
    }

    private func addDraftKeyword() {
        let trimmed = draftQuery.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        let keyword = KeywordRef(id: trimmed.lowercased().replacingOccurrences(of: " ", with: "-"), label: trimmed)
        addKeyword(keyword)
    }

    private func addKeyword(_ keyword: KeywordRef) {
        guard !keywords.contains(where: { $0.id == keyword.id }) else {
            draftQuery = ""
            engineHolder.engine.dismiss()
            return
        }
        keywords.append(keyword)
        engineHolder.engine.select(keyword)
        draftQuery = ""
        onCommit()
    }
}

private struct FlowLayout: Layout {
    var spacing: CGFloat = 8

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let result = arrange(proposal: proposal, subviews: subviews)
        return result.size
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let result = arrange(proposal: proposal, subviews: subviews)
        for placement in result.placements {
            subviews[placement.index].place(
                at: CGPoint(x: bounds.minX + placement.origin.x, y: bounds.minY + placement.origin.y),
                proposal: .unspecified
            )
        }
    }

    private func arrange(proposal: ProposedViewSize, subviews: Subviews) -> Arrangement {
        let maxWidth = proposal.width ?? .infinity
        var x: CGFloat = 0
        var y: CGFloat = 0
        var rowHeight: CGFloat = 0
        var placements: [Placement] = []

        for index in subviews.indices {
            let size = subviews[index].sizeThatFits(.unspecified)
            if x > 0, x + size.width > maxWidth {
                x = 0
                y += rowHeight + spacing
                rowHeight = 0
            }
            placements.append(Placement(index: index, origin: CGPoint(x: x, y: y)))
            rowHeight = max(rowHeight, size.height)
            x += size.width + spacing
        }

        return Arrangement(
            size: CGSize(width: maxWidth, height: y + rowHeight),
            placements: placements
        )
    }

    private struct Placement {
        let index: Int
        let origin: CGPoint
    }

    private struct Arrangement {
        let size: CGSize
        let placements: [Placement]
    }
}
