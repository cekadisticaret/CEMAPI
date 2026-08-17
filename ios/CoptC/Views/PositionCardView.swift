import SwiftUI

struct PositionCardView: View {
    let position: Position

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 6) {
                Text(position.symbol)
                    .font(.title3.bold())
                    .foregroundStyle(Theme.ink)
                if !position.badge.isEmpty {
                    TagView(text: position.badge, color: Theme.navy)
                }
                if !position.source.isEmpty {
                    TagView(text: position.source, color: Theme.mut)
                }
                Spacer()
                TagView(
                    text: position.dirLabel,
                    color: position.dir == "UP" ? Theme.green : Theme.red
                )
            }

            HStack(alignment: .firstTextBaseline, spacing: 8) {
                if let spot = position.spotNow {
                    Text(Theme.money(spot))
                        .font(.system(size: 24, weight: .bold, design: .rounded))
                        .foregroundStyle(Theme.ink)
                }
                if let win = position.winning {
                    Image(systemName: win ? "checkmark" : "xmark")
                        .font(.caption.weight(.bold))
                        .foregroundStyle(win ? Theme.green : Theme.red)
                }
                if let diff = position.spotDiff {
                    Text(String(format: "%+.2f", diff))
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(diff >= 0 ? Theme.green : Theme.red)
                }
            }

            Text(entryLine)
                .font(.caption)
                .foregroundStyle(Theme.mut)

            VStack(alignment: .leading, spacing: 6) {
                Text("ANLIK KÂR/ZARAR")
                    .font(.caption2.weight(.semibold))
                    .foregroundStyle(Theme.mut)
                HStack(alignment: .firstTextBaseline, spacing: 8) {
                    Text(pnlText)
                        .font(.system(size: 26, weight: .bold, design: .rounded))
                    if let pct = position.pnlPct, !position.noLiquidity {
                        Text(String(format: "%+.1f%%", pct))
                            .font(.title3.weight(.semibold))
                    }
                }
                .foregroundStyle(Theme.pnlColor(position.closePnl))
                if position.noLiquidity {
                    Text("Piyasada alıcı yok")
                        .font(.caption2)
                        .foregroundStyle(Theme.gold)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(14)
            .background(Theme.pnlFill(position.closePnl))
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))

            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("ANLIK KAPATMA")
                        .font(.caption2.weight(.semibold))
                        .foregroundStyle(Theme.mut)
                    Text(tokenLine)
                        .font(.caption)
                        .foregroundStyle(Theme.mut)
                }
                Spacer()
                Text(position.noLiquidity ? "—" : Theme.money(position.closeVal))
                    .font(.title3.bold())
                    .foregroundStyle(Theme.ink)
            }
            .padding(14)
            .background(Theme.card)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))

            HStack {
                Text("Risk \(Theme.money(position.spent))")
                    .font(.subheadline)
                    .foregroundStyle(Theme.ink)
                Spacer()
                Text("Kazanırsa \(Theme.money(position.toWin))")
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(Theme.green)
            }
        }
        .padding(16)
        .background(Theme.card)
        .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
        .overlay {
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .stroke(Theme.pnlColor(position.closePnl).opacity(0.35), lineWidth: 1.5)
        }
        .modifier(SoftShadow())
    }

    private var entryLine: String {
        let entry = position.entry.map { "Giriş $\(String(format: "%.2f", $0))" } ?? "Giriş —"
        let slot = position.slot.isEmpty ? "—" : position.slot
        return "\(entry) · Slot \(slot)"
    }

    private var tokenLine: String {
        if position.noLiquidity { return "alıcı yok" }
        if let bid = position.tokenBid {
            return "token \(bid)"
        }
        return "token —"
    }

    private var pnlText: String {
        guard !position.noLiquidity, let pnl = position.closePnl else { return "—" }
        return (pnl >= 0 ? "+" : "") + String(format: "%.2f$", pnl)
    }
}
