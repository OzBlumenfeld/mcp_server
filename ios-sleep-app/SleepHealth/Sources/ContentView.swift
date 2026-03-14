import SwiftUI

struct ContentView: View {
    @StateObject private var manager = SleepDataManager()

    var body: some View {
        NavigationStack {
            Group {
                switch manager.authorizationStatus {
                case .notDetermined:
                    AuthorizationView(manager: manager)
                case .sharingDenied:
                    PermissionDeniedView()
                default:
                    SleepDashboardView(manager: manager)
                }
            }
            .navigationTitle("Sleep Health")
            .navigationBarTitleDisplayMode(.large)
        }
        .onAppear {
            // Kick off auth check on launch; if already authorized, fetch data.
            manager.requestAuthorization()
        }
    }
}

// MARK: - Authorization prompt

private struct AuthorizationView: View {
    let manager: SleepDataManager

    var body: some View {
        VStack(spacing: 24) {
            Image(systemName: "moon.zzz.fill")
                .font(.system(size: 72))
                .foregroundStyle(.indigo)

            Text("Sleep Health needs access to your Apple Health sleep data.")
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
                .padding(.horizontal)

            Button("Allow Health Access") {
                manager.requestAuthorization()
            }
            .buttonStyle(.borderedProminent)
            .tint(.indigo)
        }
        .padding()
    }
}

// MARK: - Permission denied

private struct PermissionDeniedView: View {
    var body: some View {
        ContentUnavailableView(
            "Health Access Denied",
            systemImage: "lock.shield",
            description: Text("Open **Settings → Privacy & Security → Health → Sleep Health** and enable Sleep Analysis.")
        )
    }
}

// MARK: - Main dashboard

struct SleepDashboardView: View {
    @ObservedObject var manager: SleepDataManager
    @State private var selectedDays: Int = 30

    var body: some View {
        List {
            // Summary card
            Section {
                SummaryCardView(manager: manager)
            }

            // Daily breakdown
            Section("Daily Breakdown") {
                if manager.isLoading {
                    ProgressView("Loading sleep data…")
                        .frame(maxWidth: .infinity, alignment: .center)
                        .padding()
                } else if manager.dailySleepSummary.isEmpty {
                    ContentUnavailableView(
                        "No Sleep Data",
                        systemImage: "moon.zzz",
                        description: Text("No sleep records found for the past \(selectedDays) days.")
                    )
                } else {
                    ForEach(manager.dailySleepSummary, id: \.date) { summary in
                        NavigationLink {
                            DayDetailView(date: summary.date, records: summary.records)
                        } label: {
                            DaySummaryRow(date: summary.date, totalSleep: summary.totalSleep)
                        }
                    }
                }
            }
        }
        .refreshable {
            await manager.fetchSleepData(days: selectedDays)
        }
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Menu {
                    ForEach([7, 14, 30, 90], id: \.self) { days in
                        Button("Last \(days) days") {
                            selectedDays = days
                            Task { await manager.fetchSleepData(days: days) }
                        }
                    }
                } label: {
                    Label("Range", systemImage: "calendar")
                }
            }
        }
        .alert("Error", isPresented: .constant(manager.errorMessage != nil), presenting: manager.errorMessage) { _ in
            Button("OK") { manager.errorMessage = nil }
        } message: { msg in
            Text(msg)
        }
    }
}

// MARK: - Summary card

private struct SummaryCardView: View {
    @ObservedObject var manager: SleepDataManager

    private var avgFormatted: String {
        let h = Int(manager.averageSleepDuration) / 3600
        let m = (Int(manager.averageSleepDuration) % 3600) / 60
        return h > 0 ? "\(h)h \(m)m" : "\(m)m"
    }

    var body: some View {
        HStack(spacing: 16) {
            VStack(alignment: .leading, spacing: 4) {
                Label("Avg. Nightly Sleep", systemImage: "moon.fill")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Text(avgFormatted)
                    .font(.title.bold())
                    .foregroundStyle(.indigo)
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 4) {
                Label("Nights tracked", systemImage: "list.bullet")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Text("\(manager.dailySleepSummary.count)")
                    .font(.title.bold())
                    .foregroundStyle(.indigo)
            }
        }
        .padding(.vertical, 8)
    }
}

// MARK: - Day row

private struct DaySummaryRow: View {
    let date: Date
    let totalSleep: TimeInterval

    private static let dateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateStyle = .medium
        f.timeStyle = .none
        return f
    }()

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(Self.dateFormatter.string(from: date))
                    .font(.subheadline.weight(.medium))
                SleepBarView(duration: totalSleep)
                    .frame(height: 8)
            }
            Spacer()
            Text(formatDuration(totalSleep))
                .font(.subheadline.monospacedDigit())
                .foregroundStyle(sleepColor(totalSleep))
        }
        .padding(.vertical, 4)
    }

    private func formatDuration(_ t: TimeInterval) -> String {
        let h = Int(t) / 3600
        let m = (Int(t) % 3600) / 60
        return h > 0 ? "\(h)h \(m)m" : "\(m)m"
    }

    private func sleepColor(_ t: TimeInterval) -> Color {
        switch t {
        case ..<(6 * 3600):  return .red
        case ..<(7 * 3600):  return .orange
        default:             return .green
        }
    }
}

// MARK: - Sleep quality bar

private struct SleepBarView: View {
    let duration: TimeInterval
    private let recommended: TimeInterval = 8 * 3600

    var body: some View {
        GeometryReader { geo in
            ZStack(alignment: .leading) {
                Capsule().fill(Color(.systemGray5))
                Capsule()
                    .fill(barColor)
                    .frame(width: geo.size.width * min(duration / recommended, 1.0))
            }
        }
    }

    private var barColor: Color {
        switch duration {
        case ..<(6 * 3600):  return .red
        case ..<(7 * 3600):  return .orange
        default:             return .indigo
        }
    }
}

// MARK: - Day detail

struct DayDetailView: View {
    let date: Date
    let records: [SleepRecord]

    var body: some View {
        List(records) { record in
            SleepRecordRow(record: record)
        }
        .navigationTitle(date.formatted(date: .abbreviated, time: .omitted))
        .navigationBarTitleDisplayMode(.inline)
    }
}

private struct SleepRecordRow: View {
    let record: SleepRecord

    var body: some View {
        HStack(spacing: 12) {
            Circle()
                .fill(stageColor(record.stage))
                .frame(width: 10, height: 10)

            VStack(alignment: .leading, spacing: 2) {
                Text(record.stageLabel)
                    .font(.subheadline.weight(.medium))
                Text("\(record.startDate.formatted(date: .omitted, time: .shortened)) – \(record.endDate.formatted(date: .omitted, time: .shortened))")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            Text(record.durationFormatted)
                .font(.subheadline.monospacedDigit())
                .foregroundStyle(.secondary)
        }
        .padding(.vertical, 2)
    }

    private func stageColor(_ stage: HKCategoryValueSleepAnalysis) -> Color {
        switch stage {
        case .asleepDeep:  return .indigo
        case .asleepREM:   return .purple
        case .asleepCore:  return .blue
        case .awake:       return .orange
        default:           return .gray
        }
    }
}

// Needed for HKCategoryValueSleepAnalysis in the view file
import HealthKit
