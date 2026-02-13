// Average Load Test — simulates normal production traffic
// 100 VUs, 5 minutes with ramp-up/down
//
// Usage:
//   k6 run backend/tests/load/average.js
//   k6 run -e BASE_URL=https://api.bookswipe.app backend/tests/load/average.js

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
    { duration: "30s", target: 20 },   // Ramp up
    { duration: "1m", target: 50 },     // Moderate load
    { duration: "2m", target: 100 },    // Full average load
    { duration: "1m", target: 50 },     // Ramp down
    { duration: "30s", target: 0 },     // Cool down
  ],
  thresholds: THRESHOLDS,
};

export default function () {
  const token = authFlow(__VU);
  sleep(1);

  // Weighted user behavior: discovery is most common
  const roll = Math.random();
  if (roll < 0.35) {
    // 35%: Browse and discover books
    discoveryFlow(token);
    sleep(0.5);
    discoveryFlow(token);
    sleep(1);
  } else if (roll < 0.60) {
    // 25%: Swipe session (3–5 rapid swipes)
    const swipeCount = Math.floor(Math.random() * 3) + 3;
    for (let i = 0; i < swipeCount; i++) {
      swipeFlow(token);
      sleep(0.3);
    }
  } else if (roll < 0.80) {
    // 20%: Check recommendations
    recommendationsFlow(token);
    sleep(1);
    discoveryFlow(token);
    sleep(0.5);
  } else if (roll < 0.95) {
    // 15%: Social browsing
    socialFlow(token);
    sleep(1);
  } else {
    // 5%: Health check (monitoring)
    healthCheck();
    sleep(0.5);
  }

  sleep(1);
}
