# Sleep Health – iOS App

A simple iPhone app that reads your Apple Health sleep data and displays nightly sleep stages, durations, and trends.

---

## Prerequisites

You need a Mac to build and run iOS apps. This cannot be done from a Linux or Windows machine.

| Requirement | Version | How to get it |
|---|---|---|
| Mac | macOS 13 Ventura or later | — |
| Xcode | 15 or later | Mac App Store (free) |
| Apple Developer account | Free tier is enough for personal use | https://developer.apple.com |
| iPhone | iOS 17 or later | — |
| USB cable | Lightning or USB-C | — |

> **HealthKit does not work in the iOS Simulator.** You must run on a real iPhone.

---

## Step 1 – Install Xcode

```bash
# Check if Xcode is already installed
xcode-select -p

# If not installed, open the Mac App Store
open "macapp://itunes.apple.com/app/id497799835"
```

After installing Xcode, accept the license and install command-line tools:

```bash
sudo xcodebuild -license accept
xcode-select --install
```

---

## Step 2 – Clone or copy the project to your Mac

If the project is on a remote machine, copy it over:

```bash
# From your Mac terminal – replace user@host with your actual server address
scp -r user@host:/home/user/mcp_server/ios-sleep-app ~/Desktop/ios-sleep-app
```

Or if you cloned the whole repo:

```bash
cd ~/Desktop/ios-sleep-app
```

---

## Step 3 – Connect your iPhone

1. Plug your iPhone into your Mac with a USB cable.
2. On your iPhone, tap **Trust** when prompted.
3. On your Mac, open **Xcode**, go to **Window → Devices and Simulators**.
4. Your phone should appear in the left panel. If it shows "Unavailable", tap it and click **Enable Developer Mode** on the iPhone (Settings → Privacy & Security → Developer Mode).

Verify Xcode sees your device from the terminal:

```bash
xcrun xctrace list devices
```

You should see your iPhone listed with a UDID like `iPhone (17.x) [ABC123...]`.

---

## Step 4 – Configure signing (one-time setup)

iOS apps must be code-signed even for personal use.

```bash
cd ~/Desktop/ios-sleep-app

# Open the project in Xcode
open SleepHealth.xcodeproj
```

Inside Xcode:

1. Click **SleepHealth** in the left sidebar (the blue project icon).
2. Select the **SleepHealth** target.
3. Go to the **Signing & Capabilities** tab.
4. Check **Automatically manage signing**.
5. Under **Team**, select your Apple ID. If none appears, go to **Xcode → Settings → Accounts** and add your Apple ID.
6. Change `com.yourname.SleepHealth` under **Bundle Identifier** to something unique, e.g. `com.johndoe.SleepHealth`.
7. Make sure **HealthKit** appears in the capabilities list. If not, click **+ Capability** and add it.

---

## Step 5 – Build and run from the CLI

```bash
cd ~/Desktop/ios-sleep-app

# List available schemes and destinations
xcodebuild -list -project SleepHealth.xcodeproj

# Find your iPhone's UDID (copy the part inside the brackets)
xcrun xctrace list devices

# Build and install on your iPhone (replace UDID with yours)
xcodebuild \
  -project SleepHealth.xcodeproj \
  -scheme SleepHealth \
  -destination 'id=YOUR_IPHONE_UDID' \
  -configuration Debug \
  clean build

# Then install and launch it
xcrun devicectl device install app \
  --device YOUR_IPHONE_UDID \
  $(find ~/Library/Developer/Xcode/DerivedData -name "SleepHealth.app" -type d | head -1)
```

**Full one-liner example** (replace the UDID):

```bash
UDID="00008120-001234ABCDEF" && \
xcodebuild \
  -project SleepHealth.xcodeproj \
  -scheme SleepHealth \
  -destination "id=$UDID" \
  -configuration Debug \
  clean build && \
xcrun devicectl device install app \
  --device "$UDID" \
  "$(find ~/Library/Developer/Xcode/DerivedData -name 'SleepHealth.app' -type d | head -1)"
```

---

## Step 6 – First launch on iPhone

1. Find the **Sleep Health** app on your iPhone home screen and tap it.
2. Tap **Allow Health Access** — this opens the iOS Health permission sheet.
3. Enable **Sleep Analysis** (turn on the toggle) and tap **Allow**.
4. The app will immediately load your sleep data from the past 30 days.

> If you see "No Sleep Data", make sure your Apple Watch or the Health app has sleep tracking enabled:
> iPhone → **Health app → Browse → Sleep → Set Up Sleep**.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `No team found` | Add your Apple ID in Xcode → Settings → Accounts |
| `Untrusted Developer` on iPhone | iPhone → Settings → General → VPN & Device Management → tap your Apple ID → Trust |
| `HealthKit not available` | You are running in the Simulator — must use a real device |
| `Permission denied` after denying access | iPhone → Settings → Privacy & Security → Health → Sleep Health → enable Sleep Analysis |
| Build fails with provisioning error | In Xcode, click **Fix Issue** button under Signing & Capabilities |

---

## Project structure

```
ios-sleep-app/
├── SleepHealth.xcodeproj/       Xcode project (open this)
└── SleepHealth/
    ├── Sources/
    │   ├── SleepHealthApp.swift  App entry point
    │   ├── ContentView.swift     All SwiftUI screens
    │   └── SleepDataManager.swift HealthKit queries & data model
    └── Resources/
        └── Info.plist            HealthKit usage permission strings
```
