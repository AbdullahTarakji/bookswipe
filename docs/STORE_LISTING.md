# BookSwipe — App Store Listings

> Production-ready metadata for Apple App Store and Google Play Store.
> Last updated: 2026-02-19

---

## Apple App Store

### Basic Information

| Field | Value |
|---|---|
| **App Name** | BookSwipe |
| **Subtitle** | Swipe, Discover & Read More |
| **Primary Category** | Books |
| **Secondary Category** | Lifestyle |
| **Bundle ID** | `com.bookswipe.app` |
| **Support URL** | `https://bookswipe.app/support` |
| **Marketing URL** | `https://bookswipe.app` |
| **Privacy Policy URL** | `https://bookswipe.app/privacy` |

### Promotional Text (max 170 chars)

> 📚 Discover your next favorite book in seconds! Swipe through personalized recommendations, build reading lists, and join a community of book lovers.

*Character count: 155*

### Description (max 4000 chars)

```
Tired of scrolling through endless book lists? BookSwipe makes finding your next great read as easy as a swipe.

SWIPE TO DISCOVER
BookSwipe brings the simplicity of swiping to book discovery. See a book that catches your eye? Swipe right to save it. Not interested? Swipe left and move on. It's the fastest, most fun way to find books you'll actually love.

PERSONALIZED FOR YOU
The more you swipe, the smarter BookSwipe gets. Our recommendation engine learns your taste and serves up books tailored to your preferences — from bestselling thrillers to hidden indie gems.

EXPLORE BY CATEGORY
Browse books across dozens of categories including Fiction, Science Fiction, Romance, Mystery, Self-Help, Biography, Fantasy, History, and many more. Filter by genre to discover exactly what you're in the mood for.

BUILD YOUR READING LISTS
Organize your liked books into custom reading lists. Create lists for different moods, seasons, or goals — "Beach Reads," "Career Growth," "Sci-Fi Marathon" — it's entirely up to you.

READ & WRITE REVIEWS
See what other readers think before you commit, or share your own thoughts after finishing a book. Our review system helps the community discover quality reads together.

TRACK YOUR READING JOURNEY
Keep a record of every book you've liked, reviewed, and added to your lists. Watch your literary taste evolve over time.

BOOKSWIPE PREMIUM — $4.99/month
Free users get a generous daily swipe limit. Upgrade to Premium for:
• Unlimited swipes — never stop discovering
• Advanced filters — narrow by rating, page count, publication year & more
• Early access to new features
• Ad-free experience

Whether you're a casual reader looking for your next page-turner or a voracious bookworm hunting for hidden gems, BookSwipe is the discovery tool you've been waiting for.

Download BookSwipe today and start swiping your way to a better bookshelf.
```

*Character count: ~1,580*

### Keywords (max 100 chars, comma-separated)

```
books,reading,book discovery,reading list,book recommendations,swipe,book reviews,bookworm,read
```

*Character count: 95*

### What's New — v1.0.0

```
🎉 Welcome to BookSwipe!

• Swipe through thousands of books to find your next read
• Browse and filter by category
• Create custom reading lists
• Write and read book reviews
• Sign in with Apple or Google
• Premium subscription for unlimited swipes and advanced filters

Happy reading! 📖
```

---

## Google Play Store

### Basic Information

| Field | Value |
|---|---|
| **App Name** | BookSwipe |
| **Short Description** | Swipe to discover books you'll love. Build lists, write reviews & read more. |
| **Category** | Books & Reference |
| **Content Rating** | Everyone |
| **Contact Email** | `support@bookswipe.app` |
| **Privacy Policy URL** | `https://bookswipe.app/privacy` |

*Short description character count: 76*

### Full Description (max 4000 chars)

```
BookSwipe is the easiest and most fun way to discover books. Swipe right on books you love, left on ones you don't — and let BookSwipe learn what you like.

★ SWIPE TO DISCOVER NEW BOOKS
Finding your next great read shouldn't be complicated. BookSwipe shows you one book at a time with its cover, description, and rating. Swipe right to like it, left to skip. It's fast, fun, and addictive — in the best way.

★ SMART RECOMMENDATIONS
BookSwipe gets smarter the more you use it. Our recommendation engine analyzes your swipes to surface books that match your taste. Discover bestsellers, hidden gems, and everything in between.

★ BROWSE BY CATEGORY
Explore books across dozens of genres: Fiction, Non-Fiction, Science Fiction, Fantasy, Romance, Mystery & Thriller, Biography, Self-Help, History, Business, Science, Poetry, and more. Use category filters to focus your discovery on what you're in the mood for.

★ CUSTOM READING LISTS
Save and organize your liked books into reading lists. Create as many lists as you want — group by genre, mood, season, or reading goals. Your bookshelf, your rules.

★ REVIEWS & RATINGS
Read reviews from fellow book lovers before diving in, or share your own opinion after you finish. Help the community find great books and avoid duds.

★ TRACK YOUR READING
Every book you like, skip, or review is tracked. Look back at your discovery history and see how your reading taste evolves.

★ BOOKSWIPE PREMIUM ($4.99/month)
Love discovering books? Go unlimited:
• Unlimited daily swipes
• Advanced search filters (rating, page count, year, and more)
• Early access to new features
• No ads

BookSwipe is free to download and use. Premium is an optional subscription that unlocks the full experience for power readers.

Whether you read one book a month or one a week, BookSwipe helps you find the right book at the right time. Stop wasting hours browsing — start swiping.

Download BookSwipe now and discover your next favorite book today.
```

*Character count: ~1,690*

---

## App Icon

### Design Concept

The BookSwipe icon features an open book viewed from a slight angle with a curved swipe arrow flowing across it, suggesting the swipe gesture. The design uses a gradient background from deep indigo (#4A00E0) to vibrant purple (#8E2DE2), with the book and arrow rendered in white. The style is minimal, modern, and instantly recognizable at small sizes.

### Requirements

| Platform | Size | Format | Notes |
|---|---|---|---|
| iOS App Store | 1024×1024 | PNG | No transparency, no rounded corners (Apple applies mask) |
| iOS Spotlight | 120×120 | PNG | Auto-generated from 1024 |
| Android Play Store | 512×512 | PNG | 32-bit PNG with alpha |
| Android Adaptive | 108×108 dp | XML/PNG | Foreground (72dp safe zone) + background layers |
| Web Favicon | 192×192, 512×512 | PNG | For PWA manifest |

The icon source file is configured via `flutter_launcher_icons` — see `flutter_launcher_icons.yaml` in the frontend directory.

---

## Feature Graphic (Google Play)

### Requirements

- **Size:** 1024 × 500 px
- **Format:** PNG or JPEG, max 1 MB

### Design Concept

A wide banner with the same indigo-to-purple gradient as the app icon. On the left, the BookSwipe logo (icon + wordmark). On the right, a stylized illustration of book covers fanning out like cards being swiped. A tagline in white reads: **"Swipe Your Way to Your Next Great Read."** Clean, minimal, high contrast for readability at small sizes.
