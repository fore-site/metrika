import http from 'k6/http';
import { check } from 'k6';
import { SharedArray } from 'k6/data';

// ---- Load the list of 1,000 user emails ----
const users = new SharedArray('users', function () {
  const emails = [];
  for (let i = 0; i < 1000; i++) {
    emails.push(`loadtest${String(i).padStart(4, '0')}@example.com`);
  }
  return emails;
});

const LOGIN_URL = __ENV.LOGIN_URL || 'https://metrika-api.up.railway.app/api/auth/login/';
const PASSWORD = __ENV.LOGIN_PASSWORD || 'LoadTest@Pass';

export const options = {
  stages: [
    { duration: '3m', target: 100 },   // ramp up to 1000 concurrent users
    { duration: '2m',  target: 100 },   // stay at 1000
    { duration: '1m', target: 0  },   // ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],  // Relax p95 expectations for high load
    http_req_failed:   ['rate<0.05'],  // Allow small failure rate at peak
  },
};

export default function () {
  // Pick a random user from the pre‑generated list
  const email = users[Math.floor(Math.random() * users.length)];
  const payload = JSON.stringify({
    email: email,
    password: PASSWORD,
  });

  const params = {
    headers: { 'Content-Type': 'application/json' },
  };

  const res = http.post(LOGIN_URL, payload, params);

  check(res, {
    'status is 200': (r) => r.status === 200,
    'got access token': (r) => r.json('data.access') !== undefined,
  });
}