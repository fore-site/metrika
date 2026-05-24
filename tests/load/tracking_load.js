import http from 'k6/http';
import { check } from 'k6';
import { randomString } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// ---- Configuration (override via environment variables) ----
const TARGET_URL = __ENV.TARGET_URL || 'https://metrika-api.up.railway.app/api/event/';
const TRACKING_TOKEN = __ENV.TRACKING_TOKEN;

// ---- Test parameters ----
export const options = {
  stages: [
    { duration: '30s', target: 20 },   // ramp up to 20 virtual users
    { duration: '1m',  target: 50 },   // stay at 50 virtual users
    { duration: '30s', target: 0  },   // ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% of requests should be < 500 ms
    http_req_failed:   ['rate<0.01'],  // less than 1% failure rate
  },
};

// ---- Main test function ----
export default function () {
  // Build a realistic payload
  const payload = JSON.stringify({
    visitor_id:   randomString(36),                       // random UUID‑ish string
    url:          `https://loadtest.example.com/page-${__ITER}`,
    referrer:     'https://www.google.com/search?q=test',
    screen_width: 1920,
    timezone:     'UTC',
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'X-Tracking-Token': TRACKING_TOKEN,
    },
  };

  const res = http.post(TARGET_URL, payload, params);

  // Verify success
  check(res, {
    'status is 200':                (r) => r.status === 200,
    'envelope status success':      (r) => r.json('status') === 'success',
    'message contains "Event recorded"': (r) => r.json('message') === 'Event recorded.',
  });
}