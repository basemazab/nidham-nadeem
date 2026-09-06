# الأساسيات الثابتة

- Next.js App Router, React 19, TypeScript, Tailwind v4, Turbopack
- Supabase (Postgres + RLS) — multi-tenant بـ `company_id` على كل جدول تشغيلي
- النشر على Vercel، الدومين nidhamhr.com
- عربي أولًا، RTL
- الامتثال: قانون العمل 14/2025، التأمينات 148/2019

## قواعد معمارية غير قابلة للتفاوض

- `service_role` بيتخطى RLS بالتصميم — أي مسار بيستخدمه لازم يكون عليه WITH CHECK على مستوى قاعدة البيانات أو فلتر company_id صريح في الكود
- أي جدول جديد: RLS مفعّل، وسياسة فيها USING و WITH CHECK
- مفيش بيانات PII في اللوجز ولا في رسائل الخطأ
