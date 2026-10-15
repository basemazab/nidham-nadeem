// اختبار ضغط لنِظام Assistant بأداة k6 (https://k6.io).
//
// ⚠️ شغّله على نسخة تجربة (staging) مش على الموقع الحقيقي، ومش وقت ميتنج:
//    كل رد صوتي بيكلّف نداء حقيقي لـ Groq والصوت.
//    أرخص staging: من صفحة الـ Space دوس "Duplicate this Space" واعمله Private بمفاتيح منفصلة.
//
// التشغيل (3 مراحل بالترتيب):
//   k6 run -e BASE_URL=https://<staging>.hf.space loadtest/smoke.js                      # smoke: 2 زوار لمدة دقيقة
//   k6 run -e BASE_URL=... -e STAGE=load  -e USERS=5 loadtest/smoke.js                   # الضغط العادي المتوقع
//   k6 run -e BASE_URL=... -e STAGE=spike -e USERS=5 loadtest/smoke.js                   # 5 أضعاف فجأة
// إضافات اختيارية: -e K=<كود ديمو>   -e AUDIO=<مسار تسجيل صوتي غير loadtest/sample.webm>
//
// مهم: الحماية من الإغراق بتسمح بـ TALK_PER_IP_5MIN ردود لكل IP. كل زوار k6 طالعين من جهازك (IP واحد)،
// فقبل load و spike ارفع TALK_PER_IP_5MIN و TALK_PER_IP_HOUR و TALK_GLOBAL_HOUR في الـ staging بس.
// لو شفت "not rate limited" فاشلة يبقى الحماية هي اللي وقفت الاختبار، مش السيرفر اللي وقع.
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE = (__ENV.BASE_URL || 'http://localhost:7860').replace(/\/$/, '');
const K = __ENV.K || '';
const STAGE = __ENV.STAGE || 'smoke';
const USERS = parseInt(__ENV.USERS || '5', 10);
const AUDIO = open(__ENV.AUDIO || './sample.webm', 'b');

const STAGES = {
  smoke: [{ duration: '1m', target: 2 }],
  load: [
    { duration: '1m', target: USERS },
    { duration: '5m', target: USERS },
    { duration: '30s', target: 0 },
  ],
  spike: [
    { duration: '30s', target: USERS * 5 },
    { duration: '1m', target: USERS * 5 },
    { duration: '30s', target: 0 },
  ],
};

export const options = {
  stages: STAGES[STAGE],
  thresholds: {
    // أقل من 1% أخطاء
    http_req_failed: ['rate<0.01'],
    // الصفحة وفحص اللينك: 95% أسرع من 800 ملي ثانية
    'http_req_duration{kind:page}': ['p(95)<800'],
    // الرد الصوتي الكامل (سمع + تفكير + صوت): 95% أسرع من 15 ثانية — عدّلها لو شايف رقم تاني مناسب
    'http_req_duration{kind:talk}': ['p(95)<15000'],
  },
};

let sid = null;

export default function () {
  // أول مرة لكل زائر: يفتح الصفحة ويتأكد إن اللينك شغال — زي العميل بالظبط
  if (!sid) {
    sid = `k6-${__VU}-${Date.now()}`;
    const page = http.get(`${BASE}/`, { tags: { kind: 'page' } });
    check(page, { 'page loads (200)': (r) => r.status === 200 });
    const demo = http.get(`${BASE}/api/demo?k=${encodeURIComponent(K)}`, { tags: { kind: 'page' } });
    check(demo, { 'link accepted': (r) => r.status === 200 && r.json('ok') === true });
  }

  // كل لفة = جملة واحدة من الزائر ورد صوتي كامل من المساعد
  const res = http.post(
    `${BASE}/api/talk`,
    {
      file: http.file(AUDIO, 'speech.webm', 'audio/webm'),
      session_id: sid,
      k: K,
    },
    { tags: { kind: 'talk' }, timeout: '60s' },
  );
  check(res, {
    'not rate limited': (r) => r.status !== 429,
    'voice reply finished': (r) => r.status === 200 && r.body.includes('event: done'),
  });

  // الإنسان بيسمع الرد ويفكر قبل ما يتكلم تاني
  sleep(8 + Math.random() * 4);
}
