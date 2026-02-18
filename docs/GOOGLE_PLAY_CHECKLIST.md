# BookSwipe — Google Play Store Publication Checklist

> Comprehensive, actionable checklist for getting BookSwipe (Flutter book discovery app with subscriptions) approved and published on Google Play.
>
> Generated: 2026-02-18

---

## 1. Google Play Developer Account

| # | Task | Why | Status |
|---|------|-----|--------|
| 1.1 | Register a Google Play Developer account at [play.google.com/console](https://play.google.com/console) | Required to publish | ⬜ Not started |
| 1.2 | Pay $25 one-time registration fee | Required | ⬜ Not started |
| 1.3 | Complete **identity verification** (government-issued ID + address verification for personal accounts; DUNS number or business documents for organization accounts) | Required since 2023 for all new accounts; must be completed before publishing | ⬜ Not started |
| 1.4 | Provide valid contact email, phone number, and website | Displayed on store listing; required | ⬜ Not started |
| 1.5 | Decide: **Personal** vs **Organization** account (organization recommended for a commercial app — requires DUNS number) | Organization accounts get higher trust; personal accounts have stricter limits (new apps limited to 20 testers for 14 days before wider release) | ⬜ Not started |
| 1.6 | Complete the **Developer Program Policy** agreement | Must accept all policies | ⬜ Not started |
| 1.7 | Set up a **payments profile** (merchant account) in Google Play Console for receiving subscription revenue | Required if selling anything | ⬜ Not started |

---

## 2. Google Play Policies Compliance

| # | Task | Policy | Status |
|---|------|--------|--------|
| 2.1 | Review all [Developer Program Policies](https://play.google.com/about/developer-content-policy/) | General compliance | ⬜ Not started |
| 2.2 | Ensure app content is appropriate (no prohibited content: hate speech, violence, sexual content, etc.) | Restricted Content policy | ⬜ Not started |
| 2.3 | Declare whether app contains **ads** in Play Console | Ads policy — must be accurate | ⬜ Not started |
| 2.4 | Ensure no **deceptive behavior** (app does what it claims, no misleading descriptions) | Deceptive Behavior policy | ⬜ Not started |
| 2.5 | Comply with **User Data** policy — only collect data necessary for app function, disclose all collection | User Data policy | ⬜ Not started |
| 2.6 | Comply with **Permissions** policy — only request permissions that are necessary; justify any sensitive permissions | Permissions policy | ⬜ Not started |
| 2.7 | No **spam or minimum functionality** violations — app must provide value, not be a thin wrapper | Spam & Minimum Functionality policy | ⬜ Not started |
| 2.8 | Comply with **Intellectual Property** — ensure book covers/data usage is licensed or fair use | IP policy | ⬜ Not started |
| 2.9 | If using third-party SDKs, ensure they also comply with policies | SDK policy | ⬜ Not started |
| 2.10 | Ensure store listing (screenshots, description) accurately represents app functionality | Store Listing & Promotion policy | ⬜ Not started |

---

## 3. Technical Requirements

| # | Task | Requirement | Status |
|---|------|-------------|--------|
| 3.1 | Set `minSdkVersion` ≥ 21 (Android 5.0) — recommended ≥ 23 (Android 6.0) for modern APIs | Best practice; Flutter default is 21 | ⬜ Not started |
| 3.2 | Set `targetSdkVersion` to **35** (Android 15) — Google Play requires new apps to target within 1 year of latest Android release. As of Aug 2025, target SDK 35 is required for new apps. | [Target API level requirement](https://developer.android.com/google/play/requirements/target-sdk) | ⬜ Not started |
| 3.3 | Set `compileSdkVersion` ≥ 35 (must be ≥ targetSdkVersion) | Build requirement | ⬜ Not started |
| 3.4 | Build as **Android App Bundle (.aab)** — APK uploads are no longer accepted for new apps | Play Console requirement since 2021 | ⬜ Not started |
| 3.5 | App size: AAB must not exceed **150 MB** (use Play Asset Delivery for larger assets) | Play Store limit | ⬜ Not started |
| 3.6 | Declare all required permissions in `AndroidManifest.xml` with justification for sensitive ones | Permissions policy | ⬜ Not started |
| 3.7 | If using `INTERNET` permission (you will), no special justification needed — but `ACCESS_FINE_LOCATION`, `CAMERA`, `READ_CONTACTS`, etc. require justification | Sensitive permissions policy | ⬜ Not started |
| 3.8 | Handle runtime permissions properly (request at time of use, graceful degradation if denied) | Android requirement + UX | ⬜ Not started |
| 3.9 | Support **64-bit** architecture (arm64-v8a) — Flutter does this by default | Required since 2019 | ⬜ Not started |
| 3.10 | Ensure app doesn't crash on launch / basic functionality works | Broken Functionality policy | ⬜ Not started |

---

## 4. ⚠️ Billing / Subscriptions — CRITICAL CHANGE NEEDED

| # | Task | Why | Status |
|---|------|-----|--------|
| 4.1 | **⚠️ REPLACE Stripe with Google Play Billing for in-app subscriptions** — Google Play policy REQUIRES Google Play's billing system for digital goods/subscriptions sold within the app. Stripe CANNOT be used for this. | [Payments policy](https://support.google.com/googleplay/android-developer/answer/9858738) — violation = app rejection/removal | ⬜ Not started |
| 4.2 | Integrate the [`in_app_purchase`](https://pub.dev/packages/in_app_purchase) Flutter plugin (or `purchases_flutter` from RevenueCat) | Google Play Billing Library integration | ⬜ Not started |
| 4.3 | Create subscription products in **Google Play Console** (Monetization > Products > Subscriptions) | Required for Play Billing | ⬜ Not started |
| 4.4 | Define subscription **base plans** (e.g., monthly, yearly) and **offers** (free trials, introductory pricing) | Play Console subscription config | ⬜ Not started |
| 4.5 | Implement **server-side receipt validation** using [Google Play Developer API](https://developers.google.com/android-publisher) (Real-time Developer Notifications via Cloud Pub/Sub recommended) | Prevent fraud, manage subscription lifecycle | ⬜ Not started |
| 4.6 | Handle **purchase acknowledgment** within 3 days or purchase is auto-refunded | Play Billing requirement | ⬜ Not started |
| 4.7 | **Stripe can still be used for web subscriptions** — consider a hybrid approach: Play Billing on Android, Stripe on web/other platforms | Maximize flexibility | ⬜ Not started |
| 4.8 | Google takes a **15% commission** (first $1M/year) or **30%** after that | Budget planning | ⬜ Not started |
| 4.9 | Note: Some regions allow alternative billing (EEA under Digital Markets Act) — Google offers user-choice billing with reduced commission. Evaluate if applicable. | DMA compliance option | ⬜ Not started |

---

## 5. Privacy & Data Safety

| # | Task | Policy | Status |
|---|------|--------|--------|
| 5.1 | Create a **Privacy Policy** page hosted at a publicly accessible URL | Required for all apps; must be linked in store listing AND in-app | ⬜ Not started |
| 5.2 | Complete the **Data Safety** section in Play Console — declare ALL data types collected, shared, and their purposes | Required since July 2022; incomplete = rejection | ⬜ Not started |
| 5.3 | Declare data types: **Email address** (account), **Name** (profile), **Purchase history** (subscriptions), **App interactions** (swipe data, preferences), **Device ID** (analytics) | Must be accurate and complete | ⬜ Not started |
| 5.4 | Declare if data is **encrypted in transit** (yes, if using HTTPS — which you should) | Data Safety form | ⬜ Not started |
| 5.5 | Declare data **sharing** with third parties (analytics providers, crash reporting, etc.) | Must disclose all third-party data sharing | ⬜ Not started |
| 5.6 | Declare if users can request **data deletion** (required if you collect personal data) | User Data policy + GDPR | ⬜ Not started |
| 5.7 | If using Firebase Analytics, Crashlytics, etc. — declare their data collection | SDK data collection | ⬜ Not started |
| 5.8 | Provide a **data deletion request** mechanism (URL or in-app) — required by Google Play as of Dec 2023 | [Account deletion requirement](https://support.google.com/googleplay/android-developer/answer/13327111) | ⬜ Not started |
| 5.9 | If app collects location data, camera, microphone, etc. — provide **prominent disclosure** before collection | User Data policy | ⬜ Not started |

---

## 6. Legal

| # | Task | Requirement | Status |
|---|------|-------------|--------|
| 6.1 | Write **Terms of Service** and host at a public URL | Best practice, strongly recommended | ⬜ Not started |
| 6.2 | Complete **IARC content rating** questionnaire in Play Console | Required — app won't publish without it | ⬜ Not started |
| 6.3 | BookSwipe will likely receive **Everyone** or **Everyone 10+** rating — answer questionnaire accurately | IARC | ⬜ Not started |
| 6.4 | Comply with **GDPR** (EU users): consent for data processing, right to access/delete, DPO if needed | EU law | ⬜ Not started |
| 6.5 | Comply with **CCPA** (California users): "Do Not Sell My Personal Information" option if applicable | California law | ⬜ Not started |
| 6.6 | Declare **target audience** (is app for children under 13?) — if NOT targeting children, declare accordingly | Families policy; COPPA | ⬜ Not started |
| 6.7 | If app targets children AND adults, must comply with **Families Program** requirements (no behavioral advertising, COPPA-compliant) | Families policy | ⬜ Not started |
| 6.8 | Ensure subscription terms are clearly disclosed **before** purchase (price, billing period, renewal terms, cancellation method) | Consumer protection laws + Play policy | ⬜ Not started |
| 6.9 | Include **auto-renewal disclosure** language per Google's requirements | Subscription policy | ⬜ Not started |

---

## 7. Store Listing Assets

| # | Asset | Specification | Status |
|---|-------|--------------|--------|
| 7.1 | **App icon** | 512 × 512 px, PNG, 32-bit, 1024 KB max | ⬜ Not started |
| 7.2 | **Feature graphic** | 1024 × 500 px, PNG or JPEG | ⬜ Not started |
| 7.3 | **Phone screenshots** | Min 2, max 8; 16:9 or 9:16 aspect ratio; min 320px, max 3840px per side; PNG or JPEG | ⬜ Not started |
| 7.4 | **7-inch tablet screenshots** | Recommended; same specs as phone | ⬜ Not started |
| 7.5 | **10-inch tablet screenshots** | Recommended; same specs as phone | ⬜ Not started |
| 7.6 | **Short description** | Max 80 characters | ⬜ Not started |
| 7.7 | **Full description** | Max 4000 characters | ⬜ Not started |
| 7.8 | **App name** | Max 30 characters ("BookSwipe" ✓) | ⬜ Not started |
| 7.9 | **App category** | "Books & Reference" or "Entertainment" | ⬜ Not started |
| 7.10 | **Content rating** | From IARC questionnaire (see 6.2) | ⬜ Not started |
| 7.11 | **Contact email** | Required; displayed on listing | ⬜ Not started |
| 7.12 | **Privacy policy URL** | Required; displayed on listing | ⬜ Not started |
| 7.13 | Optional: **Promo video** (YouTube URL) | Recommended for discovery | ⬜ Not started |
| 7.14 | **Localization** — translate listing for target markets | Recommended for international reach | ⬜ Not started |

---

## 8. Google Play Console Configuration

| # | Task | Details | Status |
|---|------|---------|--------|
| 8.1 | Create app in Play Console (Dashboard > Create app) | Set name, language, app/game, free/paid | ⬜ Not started |
| 8.2 | Complete **App content** section (privacy policy, ads declaration, target audience, content rating, data safety, government apps declaration) | All mandatory before review | ⬜ Not started |
| 8.3 | Set up **Internal testing** track (up to 100 testers, no review needed) | For initial QA | ⬜ Not started |
| 8.4 | Set up **Closed testing** track (alpha/beta, invite-only, reviewed by Google) | For broader beta | ⬜ Not started |
| 8.5 | **New personal accounts**: Must run a closed test with ≥ 20 testers for ≥ 14 consecutive days before production release | [Testing requirement](https://support.google.com/googleplay/android-developer/answer/14151465) — enforced since Nov 2023 | ⬜ Not started |
| 8.6 | Set up **Open testing** track (public beta, listed on Play Store with "Early Access" badge) | Optional but recommended | ⬜ Not started |
| 8.7 | Set up **Production** release after testing | Final publication | ⬜ Not started |
| 8.8 | Configure **country/region availability** | Select which countries to publish in | ⬜ Not started |
| 8.9 | Set **pricing** (free with in-app subscriptions) | Monetization setup | ⬜ Not started |
| 8.10 | Configure **managed publishing** (optional — control when approved updates go live) | Release management | ⬜ Not started |
| 8.11 | Set up **Play Console API** access for CI/CD (service account with appropriate permissions) | Automation | ⬜ Not started |

---

## 9. App Signing

| # | Task | Details | Status |
|---|------|---------|--------|
| 9.1 | Enroll in **Play App Signing** (mandatory for new apps since Aug 2021) | Google manages your app signing key; you use an upload key | ⬜ Not started |
| 9.2 | Generate an **upload keystore** (`keytool -genkey -v -keystore upload-keystore.jks -keyalg RSA -keysize 2048 -validity 10000`) | Used to sign AABs before uploading | ⬜ Not started |
| 9.3 | Configure signing in `android/app/build.gradle` — reference the upload keystore | Build configuration | ⬜ Not started |
| 9.4 | Create `android/key.properties` file (NOT committed to git!) with keystore credentials | Security | ⬜ Not started |
| 9.5 | **Back up** the upload keystore securely — if lost, you must contact Google support to reset | Critical — loss means you can't update | ⬜ Not started |
| 9.6 | Add `key.properties` and `*.jks` to `.gitignore` | Security best practice | ⬜ Not started |

---

## 10. Common Rejection Reasons (Avoid These!)

| # | Rejection Reason | How to Avoid |
|---|-----------------|--------------|
| 10.1 | **Broken functionality** — app crashes on launch or core features don't work | Thorough QA on multiple devices/API levels |
| 10.2 | **Privacy policy missing or inadequate** | Host comprehensive privacy policy, link in store listing AND app |
| 10.3 | **Data Safety form incomplete or inaccurate** | Audit all data collection, declare everything honestly |
| 10.4 | **Using Stripe/third-party payment for digital subscriptions** | Use Google Play Billing (see section 4) |
| 10.5 | **Misleading store listing** — screenshots/description don't match app | Use real screenshots, accurate descriptions |
| 10.6 | **Requesting unnecessary permissions** | Only request what you need; justify sensitive permissions |
| 10.7 | **Impersonation** — app name/icon too similar to another app | Ensure unique branding |
| 10.8 | **Minimum functionality** — app is too basic or a webview wrapper | Ensure genuine native functionality and value |
| 10.9 | **Missing content rating** | Complete IARC questionnaire |
| 10.10 | **Target SDK too low** | Target SDK 35+ |
| 10.11 | **No account deletion mechanism** | Implement data/account deletion |
| 10.12 | **Background services/permissions abuse** | Don't use foreground services unnecessarily |

---

## 11. Subscription-Specific Requirements

| # | Task | Policy/Requirement | Status |
|---|------|-------------------|--------|
| 11.1 | Clearly display **subscription price, billing period, and description** before purchase | Subscriptions policy | ⬜ Not started |
| 11.2 | Disclose that subscription **auto-renews** and explain how to cancel | Subscriptions policy | ⬜ Not started |
| 11.3 | Provide **free trial terms** clearly if offering one (duration, what happens after) | Subscriptions policy | ⬜ Not started |
| 11.4 | Configure **grace period** (3, 7, 14, or 30 days) in Play Console — allows users to fix payment issues without losing access | Recommended; configurable per subscription | ⬜ Not started |
| 11.5 | Configure **account hold** — pauses subscription when payment fails beyond grace period; user loses access but sub isn't cancelled | Recommended to reduce churn | ⬜ Not started |
| 11.6 | Implement **restore purchases** — users must be able to restore subscriptions on new devices / reinstall | Required for good UX + policy | ⬜ Not started |
| 11.7 | Handle **subscription lifecycle events**: new purchase, renewal, cancellation, pause, hold, expiry | Backend integration with Play Developer API | ⬜ Not started |
| 11.8 | Implement **Real-time Developer Notifications** (RTDN) via Google Cloud Pub/Sub for server-side subscription status updates | Best practice for reliable subscription management | ⬜ Not started |
| 11.9 | Link to **Google Play subscription management** page (`https://play.google.com/store/account/subscriptions`) for easy cancellation | Recommended + reduces support burden | ⬜ Not started |
| 11.10 | Support subscription **upgrades/downgrades** if offering multiple tiers | Play Billing feature | ⬜ Not started |
| 11.11 | Handle **refunds** gracefully — revoke access when Google processes refund | Voided Purchases API | ⬜ Not started |

---

## 12. Push Notifications (FCM)

| # | Task | Details | Status |
|---|------|---------|--------|
| 12.1 | Create a **Firebase project** at [console.firebase.google.com](https://console.firebase.google.com) | Required for FCM | ⬜ Not started |
| 12.2 | Register Android app in Firebase (package name must match) | Firebase setup | ⬜ Not started |
| 12.3 | Download `google-services.json` and place in `android/app/` | Firebase Android config | ⬜ Not started |
| 12.4 | Add Firebase dependencies to `android/build.gradle` and `android/app/build.gradle` | Google services plugin + Firebase BOM | ⬜ Not started |
| 12.5 | Add [`firebase_messaging`](https://pub.dev/packages/firebase_messaging) Flutter plugin | FCM integration | ⬜ Not started |
| 12.6 | Handle FCM token registration and send to your backend | For targeted notifications | ⬜ Not started |
| 12.7 | Handle **foreground, background, and terminated** notification states | Flutter FCM requirements | ⬜ Not started |
| 12.8 | Request **POST_NOTIFICATIONS** permission (required on Android 13+ / API 33+) | Runtime permission | ⬜ Not started |
| 12.9 | Don't send spam/misleading notifications | Google Play policy | ⬜ Not started |
| 12.10 | Provide user ability to **opt out** of notifications | Best practice + policy | ⬜ Not started |

---

## 13. Flutter-Specific Configuration

| # | Task | Details | Status |
|---|------|---------|--------|
| 13.1 | Update `android/app/build.gradle`: set `compileSdkVersion 35`, `targetSdkVersion 35`, `minSdkVersion 23` | Play Store SDK requirements | ⬜ Not started |
| 13.2 | Use latest stable Flutter SDK (`flutter upgrade`) | Bug fixes + compatibility | ⬜ Not started |
| 13.3 | Update `android/build.gradle`: use latest Android Gradle Plugin (AGP 8.x+) and Gradle 8.x+ | Build compatibility | ⬜ Not started |
| 13.4 | Ensure `android/gradle/wrapper/gradle-wrapper.properties` has Gradle ≥ 8.2 | AGP 8.x requirement | ⬜ Not started |
| 13.5 | Update Kotlin version to ≥ 1.9.x in `android/build.gradle` | Compatibility with latest AGP | ⬜ Not started |
| 13.6 | Build release AAB: `flutter build appbundle --release` | Produces `.aab` file | ⬜ Not started |
| 13.7 | **R8/ProGuard**: Flutter enables R8 by default in release builds. If using Firebase or Play Billing, add keep rules if needed | Prevent code stripping issues | ⬜ Not started |
| 13.8 | Add ProGuard rules in `android/app/proguard-rules.pro` if needed: ```-keep class com.android.vending.billing.** { *; }``` | Play Billing compatibility | ⬜ Not started |
| 13.9 | Set unique `applicationId` in `build.gradle` (e.g., `com.bookswipe.app`) — CANNOT be changed after publishing | Permanent identifier | ⬜ Not started |
| 13.10 | Set `versionCode` (integer, must increment each upload) and `versionName` (display string) | Release management | ⬜ Not started |
| 13.11 | Test release build on physical device before uploading | Catch release-only issues (missing ProGuard rules, signing problems) | ⬜ Not started |
| 13.12 | Enable **multidex** if method count exceeds 64K (likely with Firebase + Billing + other packages) — add `multiDexEnabled true` in `build.gradle` | Build requirement | ⬜ Not started |
| 13.13 | Set `android:label` in `AndroidManifest.xml` to "BookSwipe" | App name on device | ⬜ Not started |
| 13.14 | Configure adaptive icon in `android/app/src/main/res/` (foreground + background layers) | Android 8.0+ icon standard | ⬜ Not started |
| 13.15 | Add internet permission in `AndroidManifest.xml`: `<uses-permission android:name="android.permission.INTERNET"/>` | Network access | ⬜ Not started |
| 13.16 | Run `flutter build appbundle` and verify AAB size < 150 MB | Size limit | ⬜ Not started |

---

## Summary — Critical Path

1. **🔴 BLOCKER: Switch from Stripe to Google Play Billing** for in-app subscriptions (section 4)
2. Set up Google Play Developer Account with identity verification
3. Complete all "App content" declarations in Play Console
4. Prepare store listing assets
5. Configure app signing
6. Run closed testing (20+ testers, 14+ days for new personal accounts)
7. Submit for production review

## Estimated Timeline
- **Account setup + verification**: 1–2 weeks (verification can take days)
- **Play Billing integration**: 1–3 weeks (significant code change)
- **Store listing + assets**: 1 week
- **Closed testing**: 2+ weeks (mandatory)
- **Review process**: 1–7 days (can be longer for new accounts)
- **Total**: ~6–8 weeks minimum

---

*Note: Google Play policies change frequently. Always check the latest [Developer Program Policies](https://play.google.com/about/developer-content-policy/) and [Play Console Help](https://support.google.com/googleplay/android-developer/) before submission.*
