import Foundation

@MainActor
final class AppState: ObservableObject {
    @Published var isLoggedIn = false
    @Published var baseURL = KeychainHelper.load(key: "baseURL") ?? APIClient.defaultBaseURL
    @Published var home: HomeResponse?
    @Published var settings: SettingsResponse?
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var lastRefresh: Date?

    private var refreshTask: Task<Void, Never>?

    func bootstrap() async {
        guard KeychainHelper.load(key: "password") != nil else {
            isLoggedIn = false
            return
        }
        await refresh(silent: true)
        if errorMessage == nil, home != nil {
            isLoggedIn = true
            startAutoRefresh()
        }
    }

    func login(password: String, serverURL: String) async {
        isLoading = true
        errorMessage = nil
        let url = serverURL.trimmingCharacters(in: .whitespacesAndNewlines)
        do {
            try await APIClient.shared.login(baseURL: url, password: password)
            KeychainHelper.save(password, key: "password")
            KeychainHelper.save(url, key: "baseURL")
            baseURL = url
            isLoggedIn = true
            await refresh(silent: false)
            startAutoRefresh()
        } catch {
            errorMessage = error.localizedDescription
            isLoggedIn = false
        }
        isLoading = false
    }

    func logout() async {
        stopAutoRefresh()
        await APIClient.shared.logout(baseURL: baseURL)
        KeychainHelper.delete(key: "password")
        home = nil
        settings = nil
        isLoggedIn = false
        errorMessage = nil
    }

    func refresh(silent: Bool = false) async {
        if !silent { isLoading = true }
        defer { if !silent { isLoading = false } }
        guard let password = KeychainHelper.load(key: "password") else {
            isLoggedIn = false
            return
        }
        do {
            try await APIClient.shared.login(baseURL: baseURL, password: password)
            home = try await APIClient.shared.home(baseURL: baseURL)
            lastRefresh = Date()
            errorMessage = nil
        } catch APIClientError.unauthorized {
            KeychainHelper.delete(key: "password")
            isLoggedIn = false
            home = nil
            errorMessage = APIClientError.unauthorized.errorDescription
            stopAutoRefresh()
        } catch {
            if !silent { errorMessage = error.localizedDescription }
        }
    }

    func toggleLive() async {
        guard let live = home?.live else { return }
        isLoading = true
        do {
            _ = try await APIClient.shared.setLive(baseURL: baseURL, on: !live.on)
            home = try await APIClient.shared.home(baseURL: baseURL)
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    func loadSettings() async {
        do {
            settings = try await APIClient.shared.settings(baseURL: baseURL)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func saveAmounts(low: Double, mid: Double, high: Double) async -> Bool {
        isLoading = true
        defer { isLoading = false }
        do {
            settings = try await APIClient.shared.saveAmounts(baseURL: baseURL, low: low, mid: mid, high: high)
            errorMessage = nil
            return true
        } catch {
            errorMessage = error.localizedDescription
            return false
        }
    }

    private func startAutoRefresh() {
        stopAutoRefresh()
        refreshTask = Task {
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: 20_000_000_000)
                if Task.isCancelled { break }
                await refresh(silent: true)
            }
        }
    }

    private func stopAutoRefresh() {
        refreshTask?.cancel()
        refreshTask = nil
    }
}
