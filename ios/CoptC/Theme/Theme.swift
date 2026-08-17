import SwiftUI

enum Theme {
    static let bg = Color(red: 0.961, green: 0.969, blue: 0.976)       // #F5F7F9
    static let navy = Color(red: 0.129, green: 0.200, blue: 0.243)     // #21333E
    static let cream = Color(red: 1.0, green: 0.945, blue: 0.878)      // #FFF1E0
    static let gold = Color(red: 0.910, green: 0.675, blue: 0.369)     // #E8AC5E
    static let card = Color.white
    static let ink = Color(red: 0.129, green: 0.200, blue: 0.243)
    static let mut = Color(red: 0.45, green: 0.50, blue: 0.55)
    static let green = Color(red: 0.22, green: 0.62, blue: 0.45)
    static let red = Color(red: 0.78, green: 0.32, blue: 0.32)
    static let radius: CGFloat = 26

    static func money(_ value: Double?) -> String {
        guard let value else { return "—" }
        let sign = value < 0 ? "-" : ""
        return sign + "$" + String(format: "%.2f", abs(value)).replacingOccurrences(of: ".", with: ",")
    }

    static func pnlColor(_ value: Double?) -> Color {
        guard let value else { return mut }
        if value > 0 { return green }
        if value < 0 { return red }
        return mut
    }
}

struct SoftShadow: ViewModifier {
    func body(content: Content) -> some View {
        content.shadow(color: Color.black.opacity(0.06), radius: 14, x: 0, y: 8)
    }
}

struct SoftCard<Content: View>: View {
    var fill: Color = Theme.card
    @ViewBuilder var content: Content

    var body: some View {
        content
            .padding(18)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(fill)
            .clipShape(RoundedRectangle(cornerRadius: Theme.radius, style: .continuous))
            .modifier(SoftShadow())
    }
}

struct ProgressRing: View {
    let progress: Double
    let text: String

    var body: some View {
        ZStack {
            Circle()
                .stroke(Color.white.opacity(0.12), lineWidth: 8)
            Circle()
                .trim(from: 0, to: min(max(progress, 0), 1))
                .stroke(Theme.gold, style: StrokeStyle(lineWidth: 8, lineCap: .round))
                .rotationEffect(.degrees(-90))
            Text(text)
                .font(.system(size: 16, weight: .bold, design: .rounded))
                .foregroundStyle(.white)
        }
        .frame(width: 78, height: 78)
    }
}

struct TagView: View {
    let text: String
    let color: Color

    var body: some View {
        Text(text)
            .font(.caption2.weight(.semibold))
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(color.opacity(0.14))
            .foregroundStyle(color)
            .clipShape(Capsule())
    }
}
