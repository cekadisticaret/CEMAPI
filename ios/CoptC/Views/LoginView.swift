import SwiftUI

struct LoginView: View {
    @EnvironmentObject private var appState: AppState
    @State private var password = ""
    @State private var serverURL = APIClient.defaultBaseURL

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 28) {
                VStack(alignment: .leading, spacing: 8) {
                    Text("CoptC")
                        .font(.system(size: 36, weight: .bold, design: .rounded))
                        .foregroundStyle(Theme.ink)
                    Text("Live Control")
                        .font(.subheadline)
                        .foregroundStyle(Theme.mut)
                }

                SoftCard {
                    VStack(alignment: .leading, spacing: 14) {
                        fieldLabel("Sunucu")
                        TextField("https://deadella.com.tr/admin", text: $serverURL)
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                            .keyboardType(.URL)
                            .padding(14)
                            .background(Theme.bg)
                            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))

                        fieldLabel("Parola")
                        SecureField("Panel parolası", text: $password)
                            .padding(14)
                            .background(Theme.bg)
                            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                    }
                }

                if let err = appState.errorMessage {
                    Text(err).font(.footnote).foregroundStyle(Theme.red)
                }

                Button {
                    Task { await appState.login(password: password, serverURL: serverURL) }
                } label: {
                    HStack {
                        if appState.isLoading { ProgressView().tint(.white) }
                        Text("Giriş yap")
                            .fontWeight(.semibold)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 16)
                    .foregroundStyle(.white)
                    .background(Theme.navy)
                    .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
                }
                .disabled(password.isEmpty || appState.isLoading)
            }
            .padding(24)
        }
        .background(Theme.bg.ignoresSafeArea())
    }

    private func fieldLabel(_ text: String) -> some View {
        Text(text)
            .font(.caption.weight(.semibold))
            .foregroundStyle(Theme.mut)
    }
}
