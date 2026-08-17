import SwiftUI

struct PositionCardView: View {
    let position: Position

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text(position.symbol)
                    .font(.headline.weight(.bold))
                    .foregroundStyle(Theme.ink)
                Spacer()
                Image(systemName: position.dir == "UP" ? "arrow.up.right" : "arrow.down.right")
                    .font(.caption.weight(.bold))
                    .foregroundStyle(position.dir == "UP" ? Theme.green : Theme.red)
            }
            TagView(
                text: position.dirLabel,
                color: position.dir == "UP" ? Theme.green : Theme.red
            )
            Text(pnlText)
                .font(.system(size: 20, weight: .bold, design: .rounded))
                .foregroundStyle(Theme.pnlColor(position.closePnl))
            if let pct = position.pnlPct {
                Text(String(format: "%+.1f%%", pct))
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(Theme.pnlColor(position.closePnl))
            }
            Text(position.slot.isEmpty ? "—" : position.slot)
                .font(.caption2)
                .foregroundStyle(Theme.mut)
        }
        .padding(16)
        .frame(maxWidth: .infinity, minHeight: 168, alignment: .topLeading)
        .background(cardFill)
        .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
        .overlay {
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .stroke(Theme.pnlColor(position.closePnl).opacity(0.28), lineWidth: 1)
        }
        .modifier(SoftShadow())
    }

    private var cardFill: Color {
        position.noLiquidity ? Theme.cream : Theme.pnlFill(position.closePnl)
    }

    private var pnlText: String {
        guard !position.noLiquidity, let pnl = position.closePnl else { return "—" }
        return (pnl >= 0 ? "+" : "") + String(format: "%.2f$", pnl)
    }
}
