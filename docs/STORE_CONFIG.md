# BookSwipe — Store Configuration Checklist

> Step-by-step setup instructions for App Store Connect and Google Play Console.

---

## Apple App Store Connect

### Prerequisites

- [ ] Apple Developer account ($99/year) — developer.apple.com
- [ ] Xcode installed with valid signing certificates
- [ ] App-specific Bundle ID registered: `com.bookswipe.app`

### App Record Setup

- [ ] Log in to [App Store Connect](https://appstoreconnect.apple.com)
- [ ] Click **My Apps → (+) New App**
- [ ] Fill in:
  - Platform: iOS
  - Name: `BookSwipe`
  - Primary Language: English (U.S.)
  - Bundle ID: `com.bookswipe.app`
  - SKU: `bookswipe-ios`
- [ ] Select **Primary Category: Books**
- [ ] Select **Secondary Category: Lifestyle**

### App Information

- [ ] Enter Subtitle: `Swipe, Discover & Read More`
- [ ] Set Content Rights: "Does not contain third-party content" (or declare as needed)
- [ ] Set Age Rating: complete questionnaire (expect 4+ / Everyone)
- [ ] Add Privacy Policy URL: `https://bookswipe.app/privacy`
- [ ] Add Support URL: `https://bookswipe.app/support`
- [ ] Add Marketing URL: `https://bookswipe.app`

### Version 1.0.0

- [ ] Enter Description (copy from STORE_LISTING.md — Apple section)
- [ ] Enter Keywords (copy from STORE_LISTING.md)
- [ ] Enter Promotional Text (copy from STORE_LISTING.md)
- [ ] Enter What's New text (copy from STORE_LISTING.md)
- [ ] Upload screenshots for all required device sizes (see SCREENSHOT_GUIDE.md)
- [ ] Upload 1024×1024 App Icon (uploaded automatically via Xcode asset catalog)
- [ ] Upload App Preview video (optional, see video script below)

### Pricing & Availability

- [ ] Set Price: Free
- [ ] Select availability: All territories (or choose specific ones)
- [ ] Pre-order: No (unless marketing strategy dictates otherwise)

### In-App Purchases (Subscriptions)

- [ ] Go to **Features → Subscriptions**
- [ ] Create Subscription Group: `BookSwipe Premium`
- [ ] Add Subscription:
  - Reference Name: `Premium Monthly`
  - Product ID: `com.bookswipe.premium.monthly`
  - Duration: 1 Month
  - Price: $4.99 (Tier 5) — Apple auto-calculates international pricing
- [ ] Add Subscription Localization:
  - Display Name: `BookSwipe Premium`
  - Description: `Unlimited swipes, advanced filters, and ad-free experience.`
- [ ] (Optional) Add free trial: 7-day free trial
- [ ] (Optional) Add annual plan:
  - Product ID: `com.bookswipe.premium.annual`
  - Duration: 1 Year
  - Price: $39.99 (≈$3.33/mo — show savings)

### App Privacy

- [ ] Complete App Privacy questionnaire in App Store Connect
- [ ] Declare data types collected (at minimum):
  - Email address — Account creation
  - Name — Account creation
  - User ID — App functionality
  - Book preferences — App functionality / Personalization
  - Purchase history — App functionality

### Review & Submit

- [ ] Add demo account credentials for App Review (if login required)
- [ ] Add review notes explaining core functionality
- [ ] Submit for review

---

## Google Play Console

### Prerequisites

- [ ] Google Play Developer account ($25 one-time) — play.google.com/console
- [ ] App signing key generated (use Google Play App Signing, recommended)

### App Creation

- [ ] Log in to [Google Play Console](https://play.google.com/console)
- [ ] Click **Create app**
- [ ] Fill in:
  - App name: `BookSwipe`
  - Default language: English (United States)
  - App or game: App
  - Free or paid: Free
- [ ] Accept declarations

### Store Listing

- [ ] Go to **Grow → Store presence → Main store listing**
- [ ] Enter Short Description (copy from STORE_LISTING.md — Google section)
- [ ] Enter Full Description (copy from STORE_LISTING.md — Google section)
- [ ] Upload App Icon: 512×512 PNG
- [ ] Upload Feature Graphic: 1024×500 PNG
- [ ] Upload Phone Screenshots (min 2, max 8 — see SCREENSHOT_GUIDE.md)
- [ ] (Optional) Upload 7" and 10" tablet screenshots

### App Content (Policy Declarations)

- [ ] **Privacy Policy:** Enter `https://bookswipe.app/privacy`
- [ ] **Ads:** Declare "Yes, contains ads" if free tier has ads, otherwise "No"
- [ ] **App access:** Provide test credentials if login required
- [ ] **Content rating:** Complete IARC questionnaire → expect "Everyone"
- [ ] **Target audience:** 13+ (or as appropriate)
- [ ] **Data safety:** Complete the data safety form:
  - Data collected: Email, name, reading preferences, purchase history
  - Data shared: None (or declare ad partners if applicable)
  - Encryption: Yes (HTTPS)
  - Deletion mechanism: Yes (account deletion in-app or via support)

### App Category & Contact

- [ ] Category: **Books & Reference**
- [ ] Contact email: `support@bookswipe.app`
- [ ] (Optional) Website: `https://bookswipe.app`
- [ ] (Optional) Phone number

### Subscription Products (Google Play Billing)

- [ ] Go to **Monetize → Products → Subscriptions**
- [ ] Create subscription:
  - Product ID: `premium_monthly`
  - Name: `BookSwipe Premium`
  - Description: `Unlimited swipes, advanced filters, and ad-free experience.`
- [ ] Add base plan:
  - Billing period: 1 month
  - Price: $4.99
  - Auto-renewing
- [ ] (Optional) Add free trial offer: 7 days
- [ ] (Optional) Add annual base plan:
  - Product ID: `premium_annual`
  - Billing period: 1 year
  - Price: $39.99
- [ ] Set prices for all target countries (use auto-convert or set manually)

### Testing Tracks

- [ ] **Internal testing:**
  - Create internal test track
  - Add testers by email (create email list)
  - Upload first AAB (Android App Bundle)
  - Share opt-in link with team
- [ ] **Closed testing (Alpha):**
  - Create closed test track when ready for wider testing
  - Min 20 testers recommended for meaningful feedback
- [ ] **Open testing (Beta):**
  - Requires passing all policy checks
  - Good for pre-launch buzz
- [ ] **Production:**
  - Staged rollout recommended (start 10% → 25% → 50% → 100%)

### Pre-launch Report

- [ ] Enable pre-launch report (automated testing on Firebase Test Lab)
- [ ] Review accessibility, performance, and crash reports before production release

---

## App Preview Video Script

### Overview

- **Duration:** 20 seconds
- **Resolution:** 1080 × 1920 (portrait)
- **Format:** MP4 / H.264 (Apple); also usable for Google Play promo video
- **Audio:** Upbeat, light instrumental (royalty-free) — no voiceover required

### Scene Breakdown

| Time | Scene | Visual | Caption Overlay |
|---|---|---|---|
| 0–3s | **Open** | App icon animates into the swipe screen. A stack of book cards appears. | **"Discover books you'll love"** |
| 3–7s | **Swipe** | User swipes right on a book (like animation). Swipes left on another (skip). One more right swipe with a heart burst effect. | **"Swipe right to save"** |
| 7–11s | **Detail** | Tap on a book card → book detail screen slides up. Shows cover, rating, description. | **"See ratings & reviews"** |
| 11–15s | **Organize** | Quick cuts: category filter screen → liked books grid → a reading list with books. | **"Build your perfect reading list"** |
| 15–18s | **Premium** | Premium screen slides in showing benefits: unlimited swipes, advanced filters. | **"Go Premium for unlimited discovery"** |
| 18–20s | **Close** | BookSwipe logo centered on gradient background. App Store / Play Store badges below. | **"BookSwipe — Download Free"** |

### Transitions

- Use smooth slide/fade transitions (0.3s each)
- Match the app's actual navigation animations
- No jarring cuts — keep it fluid and polished

### Notes

- Apple requires the video to be captured from the actual app (screen recording)
- No hands or physical devices in Apple App Preview videos
- Google Play allows more creative freedom (can add external graphics)
- Keep text overlays within safe zones (avoid top/bottom 10%)
