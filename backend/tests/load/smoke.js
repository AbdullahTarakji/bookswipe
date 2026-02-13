// Smoke Test — sanity check that all endpoints are alive
// 5 VUs, 30 seconds
//
// Usage:
//   k6 run backend/tests/load/smoke.js
//   k6 run -e BASE_URL=https://api.bookswipe.app backend/tests/load/smoke.js

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
  vus: 5,
  duration: "30s",
  thresholds: THRESHOLDS,
};

export default function () {
  // Health check
  healthCheck();
  sleep(1);

  // Full user journey
  const token = authFlow(__VU);
  sleep(1);

  discoveryFlow(token);
  sleep(1);

  swipeFlow(token);
  sleep(0.5);

  recommendationsFlow(token);
  sleep(1);

  socialFlow(token);
  sleep(1);
}
