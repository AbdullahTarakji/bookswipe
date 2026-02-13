// Reusable test flows for k6 load test scenarios

import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";
import {
  BASE_URL,
  CATEGORIES,
  FAKE_BOOK_IDS,
  authHeader,
  jsonHeaders,
} from "./config.js";

// ── Custom Metrics ─────────────────────────────────────────
export const errorRate = new Rate("error_rate");
export const authDuration = new Trend("auth_flow_duration", true);
export const discoverDuration = new Trend("discover_duration", true);
export const swipeDuration = new Trend("swipe_duration", true);
export const recommendDuration = new Trend("recommend_duration", true);
export const socialDuration = new Trend("social_duration", true);

// ── Auth Flow: register → login → token ────────────────────
export function authFlow(vuId) {
  const uniqueId = `${vuId}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  const email = `loadtest+${uniqueId}@bookswipe.test`;
  const password = "LoadTest1!strongP";

  const start = Date.now();

  // Register
  const regRes = http.post(
    `${BASE_URL}/api/auth/register`,
    JSON.stringify({ email, password }),
    { ...jsonHeaders(), tags: { name: "POST /api/auth/register", type: "write" } },
  );

  const regOk = check(regRes, {
    "register: status 201": (r) => r.status === 201,
  });
  errorRate.add(!regOk);

  if (regRes.status !== 201) {
    // If registration fails (e.g., duplicate), try login directly
    const loginRes = http.post(
      `${BASE_URL}/api/auth/login`,
      JSON.stringify({ email, password }),
      { ...jsonHeaders(), tags: { name: "POST /api/auth/login", type: "write" } },
    );
    errorRate.add(loginRes.status !== 200);
    authDuration.add(Date.now() - start);
    if (loginRes.status === 200) {
      return JSON.parse(loginRes.body).access_token;
    }
    return null;
  }

  sleep(0.5);

  // Login
  const loginRes = http.post(
    `${BASE_URL}/api/auth/login`,
    JSON.stringify({ email, password }),
    { ...jsonHeaders(), tags: { name: "POST /api/auth/login", type: "write" } },
  );

  const loginOk = check(loginRes, {
    "login: status 200": (r) => r.status === 200,
    "login: has access_token": (r) => {
      try { return !!JSON.parse(r.body).access_token; } catch { return false; }
    },
  });
  errorRate.add(!loginOk);
  authDuration.add(Date.now() - start);

  if (loginRes.status === 200) {
    return JSON.parse(loginRes.body).access_token;
  }
  return null;
}

// ── Discovery Flow: browse books with pagination ────────────
export function discoveryFlow(token) {
  const category = CATEGORIES[Math.floor(Math.random() * CATEGORIES.length)];
  const page = Math.floor(Math.random() * 3) + 1;

  const opts = token
    ? { ...authHeader(token), tags: { name: "GET /api/books/discover", type: "read" } }
    : { tags: { name: "GET /api/books/discover", type: "read" } };

  const start = Date.now();
  const res = http.get(
    `${BASE_URL}/api/books/discover?category=${category}&page=${page}&page_size=20`,
    opts,
  );

  const ok = check(res, {
    "discover: status 200": (r) => r.status === 200,
    "discover: has books array": (r) => {
      try { return Array.isArray(JSON.parse(r.body).books); } catch { return false; }
    },
  });
  errorRate.add(!ok);
  discoverDuration.add(Date.now() - start);
}

// ── Swipe Flow: like/skip books rapidly ─────────────────────
export function swipeFlow(token) {
  if (!token) return;

  const bookId = FAKE_BOOK_IDS[Math.floor(Math.random() * FAKE_BOOK_IDS.length)];
  const action = Math.random() > 0.3 ? "like" : "skip";
  const endpoint = action === "like" ? "/api/books/like" : "/api/books/skip";

  const payload = JSON.stringify({
    google_book_id: bookId,
    title: `Load Test Book ${bookId}`,
    authors: "Load Test Author",
    thumbnail: "",
  });

  const start = Date.now();
  const res = http.post(`${BASE_URL}${endpoint}`, payload, {
    ...authHeader(token),
    tags: { name: `POST ${endpoint}`, type: "write" },
  });

  const ok = check(res, {
    "swipe: status 2xx": (r) => r.status >= 200 && r.status < 300,
  });
  errorRate.add(!ok);
  swipeDuration.add(Date.now() - start);

  // Also record a swipe event for the recommendation engine
  const eventPayload = JSON.stringify({
    google_book_id: bookId,
    action: action === "like" ? "like" : "skip",
    genre: "fiction",
    author: "Load Test Author",
    category: "fiction",
  });

  http.post(`${BASE_URL}/api/swipe-events`, eventPayload, {
    ...authHeader(token),
    tags: { name: "POST /api/swipe-events", type: "write" },
  });
}

// ── Recommendations Flow ────────────────────────────────────
export function recommendationsFlow(token) {
  if (!token) return;

  const start = Date.now();
  const res = http.get(
    `${BASE_URL}/api/recommendations?page=1&page_size=20`,
    { ...authHeader(token), tags: { name: "GET /api/recommendations", type: "read" } },
  );

  const ok = check(res, {
    "recommendations: status 200": (r) => r.status === 200,
  });
  errorRate.add(!ok);
  recommendDuration.add(Date.now() - start);
}

// ── Social Flow: feed, follow, book lists ───────────────────
export function socialFlow(token) {
  if (!token) return;

  const start = Date.now();

  // Get activity feed
  const feedRes = http.get(
    `${BASE_URL}/api/social/feed?page=1&page_size=20`,
    { ...authHeader(token), tags: { name: "GET /api/social/feed", type: "read" } },
  );
  check(feedRes, {
    "feed: status 200": (r) => r.status === 200,
  });

  // Get own profile
  const profileRes = http.get(
    `${BASE_URL}/api/profile`,
    { ...authHeader(token), tags: { name: "GET /api/profile", type: "read" } },
  );
  check(profileRes, {
    "profile: status 200": (r) => r.status === 200,
  });

  // Get followers
  http.get(
    `${BASE_URL}/api/social/followers?page=1&page_size=10`,
    { ...authHeader(token), tags: { name: "GET /api/social/followers", type: "read" } },
  );

  // Get book lists
  http.get(
    `${BASE_URL}/api/book-lists?page=1&page_size=10`,
    { ...authHeader(token), tags: { name: "GET /api/book-lists", type: "read" } },
  );

  const ok = check(feedRes, {
    "social: feed accessible": (r) => r.status === 200,
  });
  errorRate.add(!ok);
  socialDuration.add(Date.now() - start);
}

// ── Health Check ────────────────────────────────────────────
export function healthCheck() {
  const res = http.get(`${BASE_URL}/health`, {
    tags: { name: "GET /health", type: "read" },
  });
  check(res, {
    "health: status 200": (r) => r.status === 200,
  });
}
