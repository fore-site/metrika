import http from 'k6/http';
import { check } from 'k6';

// ---- Configuration (override via env vars) ----
const BASE_URL = __ENV.BASE_URL || 'https://metrika-api.up.railway.app';
const LOGIN_EMAIL = __ENV.LOGIN_EMAIL || 'loadtest0001@example.com';
const LOGIN_PASSWORD = __ENV.LOGIN_PASSWORD || 'LoadTest@Pass';

// ---- Endpoints to test ----
const ENDPOINTS = [
  'top-regions',
  'top-cities',
  'timeseries',
];

// setup: authenticate
export function setup() {
  // 1. Login
  const loginUrl = `${BASE_URL}/api/auth/login/`;
  const loginPayload = JSON.stringify({
    email: LOGIN_EMAIL,
    password: LOGIN_PASSWORD,
  });
  const loginParams = { headers: { 'Content-Type': 'application/json' } };
  const loginRes = http.post(loginUrl, loginPayload, loginParams);

  if (loginRes.status !== 200) {
    throw new Error(`Login failed: ${loginRes.status} ${loginRes.body}`);
  }
  const token = loginRes.json('data.access');

  // 2. Fetch the user's sites
  const sitesUrl = `${BASE_URL}/api/sites/`;
  const sitesParams = {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  };
  const sitesRes = http.get(sitesUrl, sitesParams);

  if (sitesRes.status !== 200) {
    throw new Error(`Failed to fetch sites: ${sitesRes.status} ${sitesRes.body}`);
  }
  const sites = sitesRes.json('data');   // array of site objects
  if (!Array.isArray(sites) || sites.length === 0) {
    throw new Error('User has no sites – cannot run analytics test.');
  }

  return { token};
}

// Test options 
export const options = {
  stages: [
    { duration: '30s', target: 100 },   // ramp up to 20 VUs
    { duration: '1m',  target: 200 },   // stay at 50 VUs
    { duration: '30s', target: 0  },   // ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<800'],   // 95% of reads under 800ms
    http_req_failed:   ['rate<0.01'],   // less than 1% failure
  },
};

// Main test function 
export default function (data) {
  const token = data.token;

  // Pick a random site that belongs to the user
  const siteId = 7199 // Belongs to loadtest0001@example.com
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
    'has data array': (r) => Array.isArray(r.json('data')),
  });
}