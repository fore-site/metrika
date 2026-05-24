import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'https://metria-api.up.railway.app';
const LOGIN_EMAIL = __ENV.LOGIN_EMAIL || 'loadtest0001@example.com';
const LOGIN_PASSWORD = __ENV.LOGIN_PASSWORD || 'LoadTest@Pass';

export function setup() {
  // Perform a single login to get the access token
  const loginUrl = `${BASE_URL}/api/auth/login/`;
  const payload = JSON.stringify({
    email: LOGIN_EMAIL,
    password: LOGIN_PASSWORD,
  });
  const params = { headers: { 'Content-Type': 'application/json' } };
  const res = http.post(loginUrl, payload, params);

  if (res.status !== 200) {
    throw new Error(`Login failed: ${res.status} ${res.body}`);
  }
  const accessToken = res.json('data.access');
  return { token: accessToken };
}

export const options = {
  stages: [
    { duration: '30s', target: 20 },   // ramp up to 20 VUs
    { duration: '1m', target: 50 },    // hold at 50 VUs
    { duration: '30s', target: 0 },    // ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<800'],   // read queries may be a bit heavier
    http_req_failed: ['rate<0.01'],
  },
};

const ENDPOINTS = [
  'top-regions',
  'top-cities',
  'hourly',
  'realtime',
];

export default function (data) {
  const token = data.token;
  const siteId = Math.floor(Math.random() * 1000) + 1;   // 1..1000
  const endpoint = ENDPOINTS[Math.floor(Math.random() * ENDPOINTS.length)];
  const url = `${BASE_URL}/api/stats/${siteId}/${endpoint}/`;

  const params = {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  };

  const res = http.get(url, params);

  check(res, {
    'status is 200': (r) => r.status === 200,
    'has data': (r) => Array.isArray(r.json('data')),
  });

  sleep(1);
}