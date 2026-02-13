// Shared configuration for all k6 load test scenarios
// Override BASE_URL with: k6 run -e BASE_URL=https://api.bookswipe.app smoke.js

export const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

// ── Thresholds ─────────────────────────────────────────────
export const THRESHOLDS = {
  // Global
  http_req_failed: ["rate<0.01"], // <1% error rate
  http_req_duration: ["p(95)<500"], // p95 < 500ms overall

  // Read endpoints (discover, feed, recommendations)
  "http_req_duration{type:read}": ["p(95)<200"],

  // Write endpoints (swipe, follow, register)
  "http_req_duration{type:write}": ["p(95)<500"],
};

// ── Book categories for discovery ──────────────────────────
export const CATEGORIES = [
  "fiction",
  "mystery",
  "science",
  "history",
  "romance",
  "biography",
  "fantasy",
  "technology",
  "philosophy",
  "art",
];

// ── Fake book IDs for swipe simulation ─────────────────────
export const FAKE_BOOK_IDS = Array.from(
  { length: 100 },
  (_, i) => `load_test_book_${i}`,
);

// ── Helper: build auth header ──────────────────────────────
export function authHeader(token) {
  return { headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" } };
}

// ── Helper: JSON POST headers ──────────────────────────────
export function jsonHeaders() {
  return { headers: { "Content-Type": "application/json" } };
}
