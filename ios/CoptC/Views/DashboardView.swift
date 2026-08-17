import SwiftUI

struct DashboardView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: 22) {
                    header
                    if let err = appState.errorMessage {
                        Text(err)
                            .font(.footnote)
                            .foregroundStyle(Theme.red)
                    }
                    walletCard
                    positionsSection
                    historySection
                }
                .padding(.horizontal, 20)
                .padding(.top, 8)
                .padding(.bottom, 32)
            }
            .background(Theme.bg.ignoresSafeArea())
            .toolbar(.hidden, for: .navigationBar)
            .refreshable { await appState.refresh() }
        }
    }

    private var header: some View {
        HStack(alignment: .center) {
            VStack(alignment: .leading, spacing: 8) {
                Text("CoptC")
                    .font(.system(size: 28, weight: .bold, design: .rounded))
                    .foregroundStyle(Theme.ink)
                liveButton
            }
            Spacer()
            NavigationLink {
                SettingsView()
            } label: {
                Image(systemName: "gearshape")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundStyle(Theme.ink)
                    .frame(width: 48, height: 48)
                    .background(Theme.card)
                    .clipShape(Circle())
                    .modifier(SoftShadow())
            }
        }
    }

    private var liveButton: some View {
        Button {
            Task { await appState.toggleLive() }
        } label: {
            HStack(spacing: 8) {
                Circle()
                    .fill(appState.home?.live.on == true ? Theme.green : Theme.red)
                    .frame(width: 8, height: 8)
                Text(appState.home?.live.label ?? "Live kapalı")
                    .font(.subheadline.weight(.semibold))
            }
            .foregroundStyle(Theme.ink)
            .padding(.horizontal, 14)
            .padding(.vertical, 8)
            .background(Theme.card)
            .clipShape(Capsule())
            .modifier(SoftShadow())
        }
        .disabled(appState.isLoading || appState.home == nil)
    }

    @ViewBuilder
    private var walletCard: some View {
        if let w = appState.home?.wallet {
            HStack(alignment: .center, spacing: 16) {
                VStack(alignment: .leading, spacing: 8) {
                    Text(w.label)
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(Color.white.opacity(0.55))
                    Text(w.cashText)
                        .font(.system(size: 32, weight: .bold, design: .rounded))
                        .foregroundStyle(.white)
                    Text(w.subtitle)
                        .font(.caption)
                        .foregroundStyle(Color.white.opacity(0.62))
                        .fixedSize(horizontal: false, vertical: true)
                    Text(w.footer)
                        .font(.caption2)
                        .foregroundStyle(Color.white.opacity(0.45))
                        .padding(.top, 4)
                }
                Spacer(minLength: 8)
                ProgressRing(progress: w.ringPct ?? 0, text: w.ringText)
            }
            .padding(22)
            .background(Theme.navy)
            .clipShape(RoundedRectangle(cornerRadius: 30, style: .continuous))
            .modifier(SoftShadow())
        }
    }

    @ViewBuilder
    private var positionsSection: some View {
        let positions = appState.home?.positions ?? []
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Açık pozisyonlar")
                    .font(.title3.bold())
                    .foregroundStyle(Theme.ink)
                if !positions.isEmpty {
                    Text("\(positions.count)")
                        .font(.caption.weight(.bold))
                        .foregroundStyle(Theme.navy)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(Theme.gold.opacity(0.35))
                        .clipShape(Capsule())
                }
                Spacer()
                if appState.isLoading { ProgressView() }
            }

            if positions.isEmpty {
                SoftCard(fill: Theme.cream) {
                    Text(appState.home?.live.on == true ? "Şu an açık pozisyon yok" : "Live kapalı — emir açılmıyor")
                        .font(.subheadline)
                        .foregroundStyle(Theme.mut)
                }
            } else {
                VStack(spacing: 12) {
                    ForEach(positions) { PositionCardView(position: $0) }
                }
            }
        }
    }

    @ViewBuilder
    private var historySection: some View {
        let history = appState.home?.history ?? []
        VStack(alignment: .leading, spacing: 14) {
            Text("Son işlemler")
                .font(.title3.bold())
                .foregroundStyle(Theme.ink)
            if history.isEmpty {
                SoftCard(fill: Theme.cream) {
                    Text("Henüz kapanmış işlem yok")
                        .font(.subheadline)
                        .foregroundStyle(Theme.mut)
                }
            } else {
                VStack(spacing: 0) {
                    ForEach(Array(history.enumerated()), id: \.element.id) { index, trade in
                        HistoryRowView(trade: trade, isLast: index == history.count - 1)
                    }
                }
            }
        }
    }
}
