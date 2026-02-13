// Stress Test — push beyond normal capacity to find breaking points
// Ramps from 500 to 2000 VUs over 10 minutes
//
// Usage:
//   k6 run backend/tests/load/stress.js
//   k6 run -e BASE_URL=https://api.bookswipe.app backend/tests/load/stress.js

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
    { duration: "1m", target: 500 },    // Ramp to baseline
    { duration: "2m", target: 500 },     // Hold at 500
    { duration: "2m", target: 1000 },    // Push to 1000
    { duration: "2m", target: 2000 },    // Push to 2000 (stress)
    { duration: "1m", target: 2000 },    // Hold at peak
    { duration: "2m", target: 0 },       // Recovery
  ],
  thresholds: {
    ...THRESHOLDS,
    // Relaxed thresholds for stress — we're looking for breaking points
    http_req_failed: ["rate<0.05"],                   // <5% error rate
    http_req_duration: ["p(95)<2000"],                // p95 < 2s overall
    "http_req_duration{type:read}": ["p(95)<1000"],   // p95 < 1s reads
    "http_req_duration{type:write}": ["p(95)<2000"],  // p95 < 2s writes
  },
};

export default function () {
  // Quick auth (reuse token concept — in stress, focus on API load)
  const token = authFlow(__VU);

  if (!token) {
    // Even if auth fails under load, exercise read endpoints
    discoveryFlow(null);
    sleep(0.5);
    healthCheck();
    return;
  }

  sleep(0.5);

  // Mixed workload under stress
  const roll = Math.random();
  if (roll < 0.30) {
    discoveryFlow(token);
    sleep(0.3);
    discoveryFlow(token);
  } else if (roll < 0.55) {
    // Rapid swiping — high write load
    for (let i = 0; i < 5; i++) {
      swipeFlow(token);
      sleep(0.1);
    }
  } else if (roll < 0.75) {
    recommendationsFlow(token);
    sleep(0.3);
    discoveryFlow(token);
  } else if (roll < 0.90) {
    socialFlow(token);
  } else {
    healthCheck();
  }

  sleep(0.5);
}
