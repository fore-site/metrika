import http from 'k6/http';
import { check, sleep } from 'k6';

const REGISTER_URL = __ENV.REGISTER_URL || 'https://metrika-api.up.railway.app/api/auth/register/';

export const options = {
  vus: 1,
  duration: '30s',
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const randomEmail = `loadtest-${Date.now()}-${__VU}-${__ITER}@example.com`;
  const payload = JSON.stringify({
    email: randomEmail,
    password: 'StrongP@ss1',
    name: 'K6 Test',
  });

  const params = { headers: { 'Content-Type': 'application/json' } };
  const res = http.post(REGISTER_URL, payload, params);

  check(res, {
    'status is 201': (r) => r.status === 201,
  });

  sleep(10);  // spread out requests
}