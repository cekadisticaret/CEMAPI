import SwiftUI

struct HistoryRowView: View {
    let trade: TradeHistory
    var isLast = false

    var body: some View {
        HStack(alignment: .top, spacing: 14) {
            VStack(spacing: 0) {
                Circle()
                    .fill(trade.win ? Theme.green : Theme.red)
                    .frame(width: 10, height: 10)
                    .padding(.top, 18)
                if !isLast {
                    Rectangle()
                        .fill(Theme.navy.opacity(0.12))
                        .frame(width: 2)
                        .frame(maxHeight: .infinity)
                }
            }
            .frame(width: 10)

            VStack(alignment: .leading, spacing: 2) {
                Text(timeLabel)
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(Theme.mut)
                SoftCard(fill: Theme.pnlFill(trade.pnl)) {
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(trade.symbol)
                                .font(.subheadline.weight(.bold))
                                .foregroundStyle(Theme.ink)
                            Text("\(trade.pred ?? "—") → \(trade.actual ?? "—")")
                                .font(.caption)
                                .foregroundStyle(Theme.mut)
                        }
                        Spacer()
                        VStack(alignment: .trailing, spacing: 4) {
                            Text(trade.win ? "Kazanç" : "Kayıp")
                                .font(.caption.weight(.semibold))
                                .foregroundStyle(trade.win ? Theme.green : Theme.red)
                            Text(String(format: "%+.2f$", trade.pnl))
                                .font(.subheadline.weight(.bold))
                                .foregroundStyle(Theme.pnlColor(trade.pnl))
                        }
                    }
                }
            }
        }
    }

    private var timeLabel: String {
        let parts = trade.time.split(separator: " ")
        return parts.count == 2 ? String(parts[1]) : trade.time
    }
}
