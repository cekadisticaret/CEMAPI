import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var appState: AppState
    @State private var low = ""
    @State private var mid = ""
    @State private var high = ""
    @State private var saved = false

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 18) {
                Text("Giriş tutarlarını buradan elle değiştirirsin. Sembol win rate'e göre kademe seçilir.")
                    .font(.subheadline)
                    .foregroundStyle(Theme.mut)

                SoftCard(fill: Theme.cream) {
                    VStack(alignment: .leading, spacing: 14) {
                        amountField(appState.settings?.labels.low ?? "Low", text: $low)
                        amountField(appState.settings?.labels.mid ?? "Mid", text: $mid)
                        amountField(appState.settings?.labels.high ?? "High", text: $high)
                    }
                }

                if let err = appState.errorMessage {
                    Text(err).font(.footnote).foregroundStyle(Theme.red)
                }
                if saved {
                    Text("Kaydedildi").font(.footnote).foregroundStyle(Theme.green)
                }

                Button {
                    Task { await save() }
                } label: {
                    Text("Kaydet")
                        .fontWeight(.semibold)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 16)
                        .foregroundStyle(Theme.ink)
                        .background(Theme.gold)
                        .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
                }
                .disabled(appState.isLoading)

                Button {
                    Task { await appState.logout() }
                } label: {
                    Text("Çıkış yap")
                        .fontWeight(.semibold)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 14)
                        .foregroundStyle(Theme.red)
                }
            }
            .padding(20)
        }
        .background(Theme.bg.ignoresSafeArea())
        .navigationTitle("Ayarlar")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await appState.loadSettings()
            if let a = appState.settings?.amounts {
                low = String(a.low)
                mid = String(a.mid)
                high = String(a.high)
            }
        }
    }

    private func amountField(_ title: String, text: Binding<String>) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.caption.weight(.semibold))
                .foregroundStyle(Theme.mut)
            TextField("0.00", text: text)
                .keyboardType(.decimalPad)
                .padding(14)
                .background(Theme.card)
                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
        }
    }

    private func save() async {
        saved = false
        let lo = Double(low.replacingOccurrences(of: ",", with: ".")) ?? 0
        let mi = Double(mid.replacingOccurrences(of: ",", with: ".")) ?? 0
        let hi = Double(high.replacingOccurrences(of: ",", with: ".")) ?? 0
        saved = await appState.saveAmounts(low: lo, mid: mi, high: hi)
    }
}
