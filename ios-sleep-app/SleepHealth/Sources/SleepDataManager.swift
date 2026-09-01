import Foundation
import HealthKit

/// Represents a single sleep session with all relevant metadata.
struct SleepRecord: Identifiable {
    let id: UUID
    let startDate: Date
    let endDate: Date
    let duration: TimeInterval
    let stage: HKCategoryValueSleepAnalysis

    var stageLabel: String {
        switch stage {
        case .inBed:            return "In Bed"
        case .asleepUnspecified: return "Asleep"
        case .awake:            return "Awake"
        case .asleepCore:       return "Core Sleep"
        case .asleepDeep:       return "Deep Sleep"
        case .asleepREM:        return "REM Sleep"
        @unknown default:       return "Unknown"
        }
    }

    var durationFormatted: String {
        let hours   = Int(duration) / 3600
        let minutes = (Int(duration) % 3600) / 60
        return hours > 0 ? "\(hours)h \(minutes)m" : "\(minutes)m"
    }
}

/// Manages all HealthKit interactions for sleep data.
@MainActor
final class SleepDataManager: ObservableObject {

    // MARK: - Published State

    @Published var records: [SleepRecord]    = []
    @Published var isLoading: Bool           = false
    @Published var errorMessage: String?     = nil
    @Published var authorizationStatus: HKAuthorizationStatus = .notDetermined

    // MARK: - Private

    private let store = HKHealthStore()
    private let sleepType = HKObjectType.categoryType(forIdentifier: .sleepAnalysis)!

    // MARK: - Authorization

    /// Requests HealthKit read permission for sleep analysis.
    func requestAuthorization() {
        guard HKHealthStore.isHealthDataAvailable() else {
            errorMessage = "HealthKit is not available on this device."
            return
        }

        store.requestAuthorization(toShare: [], read: [sleepType]) { [weak self] success, error in
            Task { @MainActor in
                if let error {
                    self?.errorMessage = error.localizedDescription
                    return
                }
                self?.authorizationStatus = self?.store.authorizationStatus(for: self!.sleepType) ?? .notDetermined
                if success {
                    await self?.fetchSleepData(days: 30)
                }
            }
        }
    }

    // MARK: - Fetch

    /// Fetches sleep records for the past `days` days, sorted newest first.
    func fetchSleepData(days: Int = 30) async {
        isLoading    = true
        errorMessage = nil

        let calendar  = Calendar.current
        let startDate = calendar.date(byAdding: .day, value: -days, to: Date())!
        let predicate = HKQuery.predicateForSamples(withStart: startDate, end: Date(), options: .strictStartDate)
        let sortDesc  = NSSortDescriptor(key: HKSampleSortIdentifierStartDate, ascending: false)

        await withCheckedContinuation { continuation in
            let query = HKSampleQuery(
                sampleType: sleepType,
                predicate:  predicate,
                limit:      HKObjectQueryNoLimit,
                sortDescriptors: [sortDesc]
            ) { [weak self] _, samples, error in
                Task { @MainActor in
                    defer { self?.isLoading = false }

                    if let error {
                        self?.errorMessage = error.localizedDescription
                        continuation.resume()
                        return
                    }

                    self?.records = (samples as? [HKCategorySample] ?? []).map { sample in
                        SleepRecord(
                            id:        sample.uuid,
                            startDate: sample.startDate,
                            endDate:   sample.endDate,
                            duration:  sample.endDate.timeIntervalSince(sample.startDate),
                            stage:     HKCategoryValueSleepAnalysis(rawValue: sample.value) ?? .asleepUnspecified
                        )
                    }
                    continuation.resume()
                }
            }
            store.execute(query)
        }
    }

    // MARK: - Aggregates

    /// Groups records by calendar day and returns per-day totals (asleep only).
    var dailySleepSummary: [(date: Date, totalSleep: TimeInterval, records: [SleepRecord])] {
        let calendar = Calendar.current
        let asleepStages: Set<HKCategoryValueSleepAnalysis> = [
            .asleepUnspecified, .asleepCore, .asleepDeep, .asleepREM
        ]
        let grouped = Dictionary(grouping: records.filter { asleepStages.contains($0.stage) }) {
            calendar.startOfDay(for: $0.startDate)
        }
        return grouped
            .map { (date: $0.key, totalSleep: $0.value.reduce(0) { $0 + $1.duration }, records: $0.value) }
            .sorted { $0.date > $1.date }
    }

    /// Average nightly sleep duration over all tracked days.
    var averageSleepDuration: TimeInterval {
        let summaries = dailySleepSummary
        guard !summaries.isEmpty else { return 0 }
        return summaries.reduce(0) { $0 + $1.totalSleep } / Double(summaries.count)
    }
}
