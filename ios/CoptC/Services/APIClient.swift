import Foundation

enum APIClientError: LocalizedError {
    case invalidURL
    case unauthorized
    case server(String)
    case decode

    var errorDescription: String? {
        switch self {
        case .invalidURL: return "Geçersiz sunucu adresi"
        case .unauthorized: return "Oturum süresi doldu — tekrar giriş yap"
        case .server(let msg): return msg
        case .decode: return "Veri okunamadı"
        }
    }
}

final class APIClient {
    static let shared = APIClient()
    static let defaultBaseURL = "https://deadella.com.tr/admin"

    private let session: URLSession

    init(session: URLSession = .shared) {
        self.session = session
    }

    func login(baseURL: String, password: String) async throws {
        _ = try await request(baseURL, path: "/api/mobile/login", method: "POST", body: ["password": password])
    }

    func logout(baseURL: String) async {
        _ = try? await request(baseURL, path: "/api/mobile/logout", method: "POST", body: [:])
    }

    func home(baseURL: String) async throws -> HomeResponse {
        try decode(try await request(baseURL, path: "/api/mobile/home", method: "GET"))
    }

    func setLive(baseURL: String, on: Bool) async throws -> LiveResponse {
        try decode(try await request(baseURL, path: "/api/mobile/live", method: "POST", body: ["on": on]))
    }

    func settings(baseURL: String) async throws -> SettingsResponse {
        try decode(try await request(baseURL, path: "/api/mobile/settings", method: "GET"))
    }

    func saveAmounts(baseURL: String, low: Double, mid: Double, high: Double) async throws -> SettingsResponse {
        try decode(try await request(
            baseURL,
            path: "/api/mobile/settings/amounts",
            method: "POST",
            body: ["low": low, "mid": mid, "high": high]
        ))
    }

    private func decode<T: Decodable>(_ data: Data) throws -> T {
        do { return try JSONDecoder().decode(T.self, from: data) }
        catch { throw APIClientError.decode }
    }

    private func request(
        _ baseURL: String,
        path: String,
        method: String,
        body: [String: Any]? = nil
    ) async throws -> Data {
        var req = URLRequest(url: try endpoint(baseURL, path: path))
        req.httpMethod = method
        if let body {
            req.setValue("application/json", forHTTPHeaderField: "Content-Type")
            req.httpBody = try JSONSerialization.data(withJSONObject: body)
        }
        let (data, resp) = try await session.data(for: req)
        try check(data: data, response: resp)
        return data
    }

    private func endpoint(_ baseURL: String, path: String) throws -> URL {
        let trimmed = baseURL.trimmingCharacters(in: .whitespacesAndNewlines)
            .trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        guard let url = URL(string: "\(trimmed)\(path)") else {
            throw APIClientError.invalidURL
        }
        return url
    }

    private func check(data: Data, response: URLResponse) throws {
        guard let http = response as? HTTPURLResponse else { return }
        if http.statusCode == 401 {
            throw APIClientError.unauthorized
        }
        guard (200...299).contains(http.statusCode) else {
            if let err = try? JSONDecoder().decode(APIErrorResponse.self, from: data),
               let msg = err.error {
                throw APIClientError.server(msg)
            }
            throw APIClientError.server("HTTP \(http.statusCode)")
        }
    }
}
