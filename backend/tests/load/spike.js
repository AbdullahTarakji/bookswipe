// Spike Test — sudden burst of 5000 VUs to test auto-scaling and recovery
// Simulates a viral moment or feature launch
//
// Usage:
//   k6 run backend/tests/load/spike.js
//   k6 run -e BASE_URL=https://api.bookswipe.app backend/tests/load/spike.js

import { sleep } from "k6";
import { THRESHOLDS } from "./config.js";
import {
  authFlow,
  discoveryFlow,
  swipeFlow,
  recommendationsFlow,
  socialFlow,
  healthCheck,
} from "./helpers.js";

export const options = {
  stages: [
    { duration: "10s", target: 50 },     // Warm up
    { duration: "10s", target: 5000 },    // SPIKE — instant surge
    { duration: "1m", target: 5000 },     // Hold spike
    { duration: "10s", target: 50 },      // Rapid drop
    { duration: "30s", target: 50 },      // Recovery period
    { duration: "10s", target: 0 },       // Cool down
  ],
  thresholds: {
    // Spike thresholds — we expect degradation but need graceful handling
    http_req_failed: ["rate<0.10"],                   // <10% error rate
    http_req_duration: ["p(95)<5000"],                // p95 < 5s overall
    "http_req_duration{type:read}": ["p(95)<3000"],   // p95 < 3s reads
    "http_req_duration{type:write}": ["p(95)<5000"],  // p95 < 5s writes
  },
};

export default function () {
  // During a spike, most users are new visitors discovering the app
  const roll = Math.random();

  if (roll < 0.40) {
    // 40%: Anonymous browsing (no auth overhead)
    discoveryFlow(null);
    sleep(0.2);
    discoveryFlow(null);
  } else if (roll < 0.65) {
    // 25%: New user sign-up + first swipe
    const token = authFlow(__VU);
    sleep(0.3);
    if (token) {
      swipeFlow(token);
      sleep(0.2);
      swipeFlow(token);
    }
  } else if (roll < 0.80) {
    // 15%: Returning user — recommendations + swipe
    const token = authFlow(__VU);
    if (token) {
      recommendationsFlow(token);
      sleep(0.2);
      swipeFlow(token);
    }
  } else if (roll < 0.95) {
    // 15%: Social browsing
    const token = authFlow(__VU);
    if (token) {
      socialFlow(token);
    }
  } else {
    // 5%: Health/monitoring
    healthCheck();
  }

  sleep(0.3);
}
