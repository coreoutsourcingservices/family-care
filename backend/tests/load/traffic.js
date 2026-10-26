// Do not run against production/Supabase without explicit authorization.
// k6 run -e BASE_URL=http://127.0.0.1:5001 -e TOKENS=jwt1,jwt2 traffic.js
import http from 'k6/http';
import {check} from 'k6';
import {Counter} from 'k6/metrics';
const base = __ENV.BASE_URL;
if (!base || !/^http:\/\/(127\.0\.0\.1|localhost):/.test(base)) throw new Error('Only an isolated loopback target is permitted');
const tokens = (__ENV.TOKENS || '').split(',').filter(Boolean);
if (!tokens.length) throw new Error('Provide tokens for isolated patient test accounts');
const unexpected = new Counter('unexpected_errors');
export const options = {
  scenarios: {read_mix: {executor: 'constant-arrival-rate', rate: 200, timeUnit: '1s', duration: '60s', preAllocatedVUs: 100, maxVUs: 100}},
  thresholds: {http_req_duration: ['p(95)<500'], http_req_failed: ['rate<0.01'], unexpected_errors: ['count<2']},
};
export default function () {
  const token = tokens[(__VU - 1) % tokens.length];
  const path = Math.random() < 0.8 ? '/api/v1/patients/me' : '/api/v1/health';
  const response = http.get(base + path, {headers: {Authorization: 'Bearer ' + token}});
  const ok = check(response, {'HTTP 200': r => r.status === 200});
  if (!ok) unexpected.add(1);
}
