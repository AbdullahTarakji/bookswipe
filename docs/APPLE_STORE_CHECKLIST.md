# BookSwipe — Apple App Store Requirements Checklist

> **Last updated:** 2026-02-18
> **App:** BookSwipe (Flutter, book discovery/swiping with subscriptions)
> **Status legend:** ⬜ Not Started | 🔲 In Progress | ✅ Done

---

## 1. Apple Developer Program

| # | Item | Why | Status |
|---|------|-----|--------|
| 1.1 | **Enroll in Apple Developer Program** ($99/year) | Required to publish to App Store | ⬜ |
| 1.2 | **Apple ID with 2FA enabled** | Required for enrollment | ⬜ |
| 1.3 | **D-U-N-S Number** (if enrolling as organization) | Required for org accounts; free from Dun & Bradstreet | ⬜ |
| 1.4 | **Legal entity info** — name, address, legal status | Displayed on App Store as seller name | ⬜ |
| 1.5 | **Agreements & tax forms** in App Store Connect — accept Paid Apps agreement, configure banking & tax | Required before selling subscriptions | ⬜ |

---

## 2. App Store Review Guidelines (Key Sections)

| # | Item | Guideline | Status |
|---|------|-----------|--------|
| 2.1 | **No objectionable content** — book covers/descriptions must not contain prohibited content | §1.1 Safety | ⬜ |
| 2.2 | **User-generated content** — if users can post reviews/lists: implement content filtering, reporting, blocking, and published contact info | §1.2 UGC | ⬜ |
| 2.3 | **App completeness** — no placeholder content, broken links, or "coming soon" sections | §2.1 Performance | ⬜ |
| 2.4 | **No crashes or bugs** — thorough testing on real devices | §2.1 Performance | ⬜ |
| 2.5 | **Accurate metadata** — description, screenshots must reflect actual app functionality | §2.3 Accurate Metadata | ⬜ |
| 2.6 | **Use Apple IAP for subscriptions** (NOT Stripe for in-app digital content) | §3.1.1 In-App Purchase | ⬜ |
| 2.7 | **Human Interface Guidelines compliance** — standard iOS patterns, navigation, typography | §4.0 Design | ⬜ |
| 2.8 | **Privacy policy URL** — must be provided and accessible | §5.1 Privacy | ⬜ |
| 2.9 | **Login/account deletion** — must offer "Sign in with Apple" if any third-party sign-in is offered; must support account deletion | §4.8, §5.1.1 | ✅ |
| 2.10 | **No hidden features or remote toggling** that changes app behavior post-review | §2.3.1 | ⬜ |

---

## 3. Technical Requirements

| # | Item | Details | Status |
|---|------|---------|--------|
| 3.1 | **Minimum iOS deployment target: iOS 16** | Flutter currently supports iOS 13+, but Apple requires Xcode 16+ for submissions which targets iOS 16+. Set `MinimumOSVersion` accordingly | ⬜ |
| 3.2 | **Built with latest stable Xcode** (Xcode 16.x as of 2026) | Apple requires apps be built with recent Xcode/SDK | ⬜ |
| 3.3 | **Support all current iPhone screen sizes** — including iPhone 16 Pro Max (6.9"), iPhone 16 Pro (6.3"), etc. | Required for approval | ⬜ |
| 3.4 | **iPad support** — either Universal or iPhone-only (if iPhone-only, justify in review notes) | Recommended: support iPad | ⬜ |
| 3.5 | **App icon: 1024×1024px** single icon in Assets.xcassets (Xcode auto-generates all sizes) | Required; no alpha/transparency; PNG format | ⬜ |
| 3.6 | **Launch screen** — use LaunchScreen.storyboard (not static images); no logos per HIG | Required | ⬜ |
| 3.7 | **Dark mode support** (recommended, not required) | Best practice per HIG | ✅ |
| 3.8 | **64-bit support** | Required since iOS 11; Flutter handles this | ⬜ |
| 3.9 | **IPv6 networking support** | Apple requires apps work on IPv6-only networks | ⬜ |
| 3.10 | **Info.plist usage descriptions** — for any permissions (camera, photo library, notifications, tracking) | Rejection if missing | ⬜ |

---

## 4. ⚠️ In-App Purchases & Subscriptions (CRITICAL)

> **🚨 STRIPE CANNOT BE USED FOR iOS IN-APP DIGITAL SUBSCRIPTIONS.**
> Apple's Guideline 3.1.1 requires all digital content/subscriptions sold within iOS apps use Apple's In-App Purchase (StoreKit). Stripe can only be used for physical goods/services. **BookSwipe must replace Stripe with Apple IAP on iOS.**

| # | Item | Details | Status |
|---|------|---------|--------|
| 4.1 | **Implement StoreKit 2 / `in_app_purchase` Flutter plugin** | Replace Stripe for iOS subscription handling | ✅ |
| 4.2 | **Configure subscriptions in App Store Connect** — create subscription group, set pricing tiers, durations | Required before IAP works | ⬜ |
| 4.3 | **Display subscription terms BEFORE purchase** — price, duration, renewal terms, cancellation policy | §3.1.2(a) — rejection if missing | ✅ |
| 4.4 | **"Restore Purchases" button** — prominently accessible in subscription/settings screen | §3.1.5(b) — common rejection reason | ✅ |
| 4.5 | **Subscription management** — link to Apple subscription management or use `showManageSubscriptions()` | Best practice per Apple | ✅ |
| 4.6 | **Free trial disclosure** — if offering trials, clearly state duration and post-trial price | §3.1.2(a) | ⬜ |
| 4.7 | **Server-side receipt validation** — use App Store Server API / Server Notifications V2 | Prevent fraud, sync subscription state | ⬜ |
| 4.8 | **Dual payment system** — keep Stripe for Android/web, Apple IAP for iOS | Platform-specific implementation | ✅ |
| 4.9 | **Handle subscription states** — expired, grace period, billing retry, revoked | Required for good UX | ⬜ |
| 4.10 | **Sandbox testing** — test all IAP flows in sandbox environment before submission | Required | ⬜ |
| 4.11 | **Apple's commission** — 15% (Small Business Program) or 30% standard; factor into pricing | Financial planning | ⬜ |
| 4.12 | **Apply for App Store Small Business Program** if eligible (<$1M revenue) | Reduces commission to 15% | ⬜ |

---

## 5. Privacy

| # | Item | Details | Status |
|---|------|---------|--------|
| 5.1 | **Privacy Policy URL** — publicly accessible, linked in App Store Connect AND in-app | Required; rejection without it | ✅ |
| 5.2 | **App Privacy "Nutrition Labels"** — complete questionnaire in App Store Connect declaring all data collected | Required since Dec 2020 | ⬜ |
| 5.3 | **Categories to declare:** Contact Info (email), Identifiers (user ID), Usage Data (app interactions), Purchases | Based on BookSwipe features | ⬜ |
| 5.4 | **App Tracking Transparency (ATT)** — if using IDFA or cross-app tracking, must show ATT prompt via `requestTrackingAuthorization()` | §5.1.2 — if not tracking, declare "does not track" | ⬜ |
| 5.5 | **NSUserTrackingUsageDescription** in Info.plist if using ATT | Required if requesting tracking permission | ⬜ |
| 5.6 | **Third-party SDK privacy manifests** — all SDKs must include privacy manifests (required since Spring 2024) | Apple rejects without them | ⬜ |
| 5.7 | **Required Reason APIs** — if using UserDefaults, file timestamp, disk space, etc., must declare reasons in PrivacyInfo.xcprivacy | Required since Spring 2024 | ✅ |
| 5.8 | **Data minimization** — only collect data necessary for app functionality | Best practice | ⬜ |

---

## 6. Legal

| # | Item | Details | Status |
|---|------|---------|--------|
| 6.1 | **Terms of Service / Terms of Use** — hosted URL, linked in-app | Required for subscription apps | ✅ |
| 6.2 | **EULA** — use Apple's standard EULA or provide custom one in App Store Connect | Required | ⬜ |
| 6.3 | **GDPR compliance** — consent mechanisms, data export, right to deletion (for EU users) | Legal requirement | ⬜ |
| 6.4 | **CCPA compliance** — "Do Not Sell My Data" option for California users | Legal requirement | ⬜ |
| 6.5 | **Age Rating** — complete questionnaire in App Store Connect; BookSwipe likely 4+ or 12+ depending on content | Required | ⬜ |
| 6.6 | **Account deletion** — must allow users to delete their account and data from within the app | §5.1.1(v) — required since June 2022 | ✅ |
| 6.7 | **Copyright** — ensure book cover images, descriptions are used with proper licensing | Avoid IP infringement | ⬜ |
| 6.8 | **Export compliance (ECCN)** — declare whether app uses encryption (HTTPS counts but is usually exempt) | Required in App Store Connect | ⬜ |

---

## 7. App Store Connect Assets

### Screenshots (Required)

| # | Size | Device | Status |
|---|------|--------|--------|
| 7.1 | **1290×2796 or 1320×2868 px** | 6.9" iPhone (Pro Max) — **REQUIRED** | ⬜ |
| 7.2 | **1242×2688 or 1284×2778 px** | 6.5" iPhone — required if no 6.9" provided | ⬜ |
| 7.3 | **2048×2732 or 2064×2752 px** | 13" iPad — **REQUIRED if app runs on iPad** | ⬜ |
| 7.4 | Minimum **3 screenshots**, maximum 10, per device class | Best practice: 5-8 showing key features | ⬜ |

### Other Assets

| # | Item | Details | Status |
|---|------|---------|--------|
| 7.5 | **App Icon** — 1024×1024px PNG, no alpha, no rounded corners (Apple adds them) | Uploaded in App Store Connect | ⬜ |
| 7.6 | **App Preview Videos** (optional) — 15-30 sec, captured on device, shows app in action | Highly recommended for discovery | ⬜ |
| 7.7 | **App Name** — max 30 characters | Choose carefully, hard to change | ⬜ |
| 7.8 | **Subtitle** — max 30 characters | Shown below app name on store | ⬜ |
| 7.9 | **Description** — up to 4000 characters | First 3 lines most visible | ⬜ |
| 7.10 | **Keywords** — max 100 characters, comma-separated | For search optimization | ⬜ |
| 7.11 | **Primary Category** — "Books" or "Lifestyle" | Choose most relevant | ⬜ |
| 7.12 | **Secondary Category** (optional) — "Entertainment" | Additional discovery | ⬜ |
| 7.13 | **Promotional Text** — up to 170 chars, can be updated without new build | For timely messages | ⬜ |
| 7.14 | **What's New** text for each version | Required for updates | ⬜ |
| 7.15 | **Support URL** — publicly accessible | Required | ⬜ |
| 7.16 | **Marketing URL** (optional but recommended) | App/landing page | ⬜ |

---

## 8. App Store Connect Configuration

| # | Item | Details | Status |
|---|------|---------|--------|
| 8.1 | **Create App record** — New App → iOS platform, Bundle ID, SKU, name | First step | ⬜ |
| 8.2 | **Bundle ID registration** — register at developer.apple.com/account | e.g., `com.bookswipe.app` | ⬜ |
| 8.3 | **App Information** — category, content rights, age rating | Required fields | ⬜ |
| 8.4 | **Pricing & Availability** — set countries, price (free with IAP) | Required | ⬜ |
| 8.5 | **In-App Purchases** — configure subscription groups, products, pricing | Required for subscriptions | ⬜ |
| 8.6 | **Review Information** — demo account credentials, review notes, contact info | **CRITICAL** — provide login creds for reviewer | ⬜ |
| 8.7 | **TestFlight** — upload build, add internal testers, then external beta | Recommended before submission | ⬜ |
| 8.8 | **TestFlight external beta** — requires Beta App Review (usually quick) | Test with real users first | ⬜ |
| 8.9 | **App Store Server Notifications URL** — configure in App Store Connect for subscription events | Required for subscription management | ⬜ |
| 8.10 | **Export Compliance** — answer encryption questions or add `ITSAppUsesNonExemptEncryption = NO` to Info.plist | Avoids manual step each upload | ⬜ |

---

## 9. Code Signing

| # | Item | Details | Status |
|---|------|---------|--------|
| 9.1 | **Apple Distribution Certificate** — generate in Xcode or developer portal | Required for App Store builds | ⬜ |
| 9.2 | **Provisioning Profile (App Store)** — links certificate, Bundle ID, and entitlements | Required; auto-managed by Xcode recommended | ⬜ |
| 9.3 | **Enable "Automatically manage signing"** in Xcode | Simplest approach for most apps | ⬜ |
| 9.4 | **Entitlements** — In-App Purchase capability must be enabled | In Xcode → Signing & Capabilities → + In-App Purchase | ⬜ |
| 9.5 | **Push Notifications entitlement** (if using push) | Add capability in Xcode | ⬜ |
| 9.6 | **Keychain sharing** (if needed) | For shared credentials | ⬜ |
| 9.7 | **Build with `flutter build ipa`** — generates .xcarchive and .ipa | Use `--release` flag | ⬜ |

---

## 10. Common Rejection Reasons (Pre-flight Checklist)

| # | Check | Why | Status |
|---|-------|-----|--------|
| 10.1 | **No crashes** — test on multiple real devices and iOS versions | #1 rejection reason | ⬜ |
| 10.2 | **No broken links** — all URLs in-app and metadata must work | Common rejection | ⬜ |
| 10.3 | **No placeholder content** — no "Lorem ipsum", "TODO", or empty screens | §2.1 Completeness | ⬜ |
| 10.4 | **All features functional** — no "coming soon" or grayed-out features | §2.1 | ⬜ |
| 10.5 | **Demo account for review** — provide working login credentials in review notes | Apple WILL test login flows | ⬜ |
| 10.6 | **Backend servers running** during review | Apple tests real connectivity | ⬜ |
| 10.7 | **Accurate screenshots** — must match actual app UI | §2.3 Metadata | ⬜ |
| 10.8 | **"Restore Purchases" button present** | Missing = rejection | ✅ |
| 10.9 | **Sign in with Apple** if offering Google/Facebook sign-in | §4.8 — required | ✅ |
| 10.10 | **Account deletion** functionality works | §5.1.1(v) | ✅ |
| 10.11 | **Privacy policy accessible** (not 404) | Common oversight | ⬜ |
| 10.12 | **No references to other platforms** — don't say "also on Android" in screenshots/description | §2.3 | ⬜ |
| 10.13 | **No external payment links** — cannot direct users to pay outside the app for digital content | §3.1.1 (exception: EU "link entitlement") | ⬜ |
| 10.14 | **Permission prompts have clear usage descriptions** | Missing NSUsageDescription = crash = rejection | ⬜ |
| 10.15 | **App Review notes** — explain any non-obvious features, subscription tiers | Helps reviewers | ⬜ |

---

## 11. Subscription-Specific Requirements

| # | Item | Guideline | Status |
|---|------|-----------|--------|
| 11.1 | **Display before paywall:** subscription name, price, duration, renewal terms | §3.1.2(a) | ✅ |
| 11.2 | **Link to Terms of Use and Privacy Policy** on subscription screen | §3.1.2(a) | ✅ |
| 11.3 | **"Restore Purchases"** button on subscription/paywall screen | §3.1.5(b) | ✅ |
| 11.4 | **Subscription management link** — link to `https://apps.apple.com/account/subscriptions` or use StoreKit API | Recommended | ⬜ |
| 11.5 | **Free trial terms** — clearly state: "X days free, then $Y/period" | §3.1.2(a) | ⬜ |
| 11.6 | **No misleading "free" claims** — if app requires subscription, don't market as "free" | Common rejection | ⬜ |
| 11.7 | **Cancellation info** — explain how to cancel before being charged | Best practice | ⬜ |
| 11.8 | **Grace period handling** — Apple offers 6/16-day grace period for billing issues; handle gracefully | Retain subscribers | ⬜ |
| 11.9 | **Introductory offers** — configure in App Store Connect if offering (free trial, pay-as-you-go, pay-up-front) | Optional but recommended | ⬜ |
| 11.10 | **Subscription status in app** — show current plan, expiry, renewal status | Best practice | ✅ |

---

## 12. Push Notifications

| # | Item | Details | Status |
|---|------|---------|--------|
| 12.1 | **APNs Key (p8)** — generate in Apple Developer portal → Keys → Apple Push Notifications service | Recommended over certificates (doesn't expire) | ⬜ |
| 12.2 | **Enable Push Notifications capability** in Xcode | Required entitlement | ⬜ |
| 12.3 | **Request notification permission** — use `UNUserNotificationCenter` / Flutter plugin (`firebase_messaging` or `flutter_local_notifications`) | Must ask user permission | ⬜ |
| 12.4 | **NSUserNotificationsUsageDescription** not needed — but notification permission prompt should explain value | UX best practice | ⬜ |
| 12.5 | **Don't require push for core functionality** — app must work without notifications | §4.5.4 | ⬜ |
| 12.6 | **Configure APNs in your push service** (Firebase/OneSignal/custom) with Team ID + Key ID + p8 file | Backend setup | ⬜ |

---

## 13. Flutter-Specific iOS Gotchas

| # | Item | Details | Status |
|---|------|---------|--------|
| 13.1 | **Minimum deployment target** — set to iOS 16.0 in `ios/Podfile` (`platform :ios, '16.0'`) and Xcode project | Required for latest Xcode/SDK submissions | ⬜ |
| 13.2 | **Xcode version** — use Xcode 16.x (latest stable) | Apple requires recent SDK | ⬜ |
| 13.3 | **Flutter stable channel** — use latest stable Flutter SDK | Avoid beta/dev channel for production | ⬜ |
| 13.4 | **Run `flutter build ipa --release`** — NOT `flutter build ios` | Generates proper archive for upload | ⬜ |
| 13.5 | **CocoaPods** — run `cd ios && pod install --repo-update` before building | Stale pods = build failures | ⬜ |
| 13.6 | **Privacy manifests for Flutter plugins** — ensure all plugins have PrivacyInfo.xcprivacy | Required since 2024; check plugin updates | ⬜ |
| 13.7 | **Required Reason APIs** — Flutter itself uses some (UserDefaults, file timestamps); add PrivacyInfo.xcprivacy to Runner target | Apple rejects without this | ⬜ |
| 13.8 | **Bitcode** — disabled by default in Flutter (Apple no longer requires it) | No action needed | ✅ |
| 13.9 | **`flutter_inappurchase` or `purchases_flutter` (RevenueCat)** — use for StoreKit integration | Recommended: RevenueCat simplifies cross-platform | ⬜ |
| 13.10 | **Open Runner.xcworkspace** (not .xcodeproj) | Common mistake; workspace includes pods | ⬜ |
| 13.11 | **Upload via `xcrun altool` or Transporter app** — or directly from Xcode Archive Organizer | `flutter build ipa` then upload .ipa | ⬜ |
| 13.12 | **Test on real devices** — Simulator is insufficient for IAP testing, push notifications, and performance | Real device testing required | ⬜ |
| 13.13 | **Asset catalog for app icons** — Flutter's `flutter_launcher_icons` package can generate all sizes from single 1024px source | Simplifies icon generation | ⬜ |
| 13.14 | **Localization** — if supporting multiple languages, use Flutter's l10n system and provide localized App Store metadata | Recommended for global reach | ⬜ |

---

## Summary: Critical Path (Do These First)

1. **⚠️ Replace Stripe with Apple IAP on iOS** (§4 above) — this is the biggest architectural change
2. **Enroll in Apple Developer Program** ($99/year)
3. **Set up App Store Connect** — app record, bundle ID, subscription products
4. **Implement StoreKit** via `in_app_purchase` or RevenueCat Flutter plugin
5. **Privacy manifests & Required Reason APIs** — check all plugins
6. **Prepare assets** — icon, screenshots, metadata
7. **Sign in with Apple** + account deletion
8. **Privacy policy & Terms of Service** — host publicly
9. **TestFlight beta** — test thoroughly
10. **Submit for review** with demo account credentials

---

## Estimated Timeline

| Phase | Duration |
|-------|----------|
| IAP migration (Stripe → StoreKit) | 1-2 weeks |
| Privacy/legal compliance | 2-3 days |
| Assets & metadata preparation | 2-3 days |
| TestFlight beta testing | 1 week |
| App Review | 1-3 days (typically 24-48h) |
| **Total** | **~3-4 weeks** |

---

*Sources: Apple App Store Review Guidelines (2025), Apple Developer Documentation, Flutter Deployment Guide, App Store Connect Help*
