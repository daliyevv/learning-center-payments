# Reja: o'quv markazi to'lovlar mini-hisobi

## Kontekst
[task.md](task.md) — test topshiriq: API (o'quvchilar, to'lovlar, qarzdorlar), interfeys (variant B — veb-sahifa), README. Maqsad — TZ'ga aynan mos, sodda, har bir punkti tekshiriladigan yechim.

## Qarorlar
| Mavzu | Qaror |
|---|---|
| Stek | Python 3.12, FastAPI, SQLAlchemy 2.0 (sync), **SQLite** (fayl `data.db`, ishga tushganda `create_all`). Alembic va Docker yo'q |
| Interfeys | Mobilga mos veb-sahifa, FastAPI'dan static (vanilla HTML/CSS/JS) |
| Guruh | O'quvchida oddiy matn maydoni `group` |
| Pul | `Decimal`, ustun `Numeric(12,2)`; JSON'da string. Yig'indi va filtr **Python'da** (pastdagi izohga qarang) |
| Qarz | `debt = max(0, monthly_fee − Σ to'lovlar [oy boshi; keyingi oy boshi))`. Hech narsa to'lamagan ham qarzdor (qarz = to'liq summa). Barcha faol o'quvchilar hisobga olinadi, `created_at` bo'yicha filtr yo'q. Carry-over, proporsional, narx tarixi yo'q |
| Narx o'zgarishi | Oylik summa o'zgarsa, o'tgan oylar ham yangi narx bilan hisoblanadi (narx tarixi yo'q) |
| Sana | To'lovda `DATE`; default va "joriy oy" — Asia/Tashkent; kelajak sana taqiqlangan |
| O'chirish | Soft delete (`deleted_at`): ro'yxat, qarzdorlar va yangi to'lovdan chiqariladi, to'lovlar saqlanadi |
| Validatsiya | Pydantic, faqat 404 va 422; pytest |

### Nega yig'indi SQL'da emas, Python'da
SQLite'da haqiqiy decimal tipi yo'q: SQLAlchemy `Numeric` ustunni SQLite'da REAL (float) sifatida saqlaydi. `SUM(amount)` float qo'shadi va `0.1 + 0.2 = 0.30000000000000004` kabi xato beradi, `paid < monthly_fee` taqqoslashi esa noto'g'ri natija berishi mumkin. Shuning uchun SQL faqat qatorlarni tanlaydi: faol o'quvchilar va shu oy to'lovlari. Har bir summa o'qilganda `Decimal` ga o'giriladi (SQLAlchemy `Numeric(asdecimal=True)` buni o'zi qiladi, 2 xonaga yaxlitlab). Yig'indi `sum(..., Decimal("0"))` bilan, qarzdorlar filtri `paid < monthly_fee` ham Python'da hisoblanadi. 12,2 aniqlikdagi summalar float'da yo'qotishsiz saqlanadi, demak o'qib, yaxlitlab olish xavfsiz. Bu sabab README'ga ham yoziladi; PostgreSQL'ga o'tilsa, yig'indini SQL'ga qaytarish mumkin.

## Struktura
```
testTask/
  requirements.txt          # fastapi, uvicorn, sqlalchemy, pydantic, tzdata (Windows'da Asia/Tashkent uchun), pytest, httpx
  app/
    main.py                 # FastAPI, routerlar, startup'da create_all, "/" → static/index.html
    db.py                   # engine (DATABASE_URL env, default sqlite:///data.db), get_db
    models.py               # Student, Payment
    schemas.py              # telefon tozalash, Money, Month
    timeutil.py             # today_tashkent(), month_range("YYYY-MM") → (start, next_start)
    debtors.py              # qarz hisoblash (SQL tanlaydi, Decimal yig'indi/filtr Python'da)
    routers/students.py payments.py
    static/index.html style.css app.js
  tests/
    conftest.py             # in-memory SQLite + TestClient, get_db override
    test_api.py             # CRUD, 404/422, soft delete, to'lovlar
    test_debtors.py         # to'lamagan, qisman, to'liq, ortiqcha, oy chegarasi (31-kun / 1-kun), 0.10+0.20 kasr aniqligi
  README.md
```

## Ma'lumotlar modeli
- `students(id, name, phone, group, monthly_fee Numeric(12,2), created_at, deleted_at NULL)`
- `payments(id, student_id FK, amount Numeric(12,2), paid_on DATE, created_at)`; index `(student_id, paid_on)`

## API
- `POST /students`, `GET /students` (`?group=`), `GET/PATCH/DELETE /students/{id}`
- `POST /payments {student_id, amount, paid_on?}`, `GET /students/{id}/payments`
- `GET /debtors?month=YYYY-MM` (berilmasa — joriy oy, Toshkent). Javob: `student_id, name, phone, group, monthly_fee, paid, debt`, debt bo'yicha kamayish tartibida
- Qarz hisobi: 1) faol o'quvchilar; 2) shu oy to'lovlari (`paid_on >= start AND paid_on < next_start`, faol o'quvchilarniki). Python'da `student_id` bo'yicha `Decimal` yig'indi (to'lovi yo'q bo'lsa 0), `paid < monthly_fee` bo'lganlar qaytariladi, `debt = monthly_fee − paid`

## Validatsiya
- `name`, `group`: bo'sh emas, trim; `monthly_fee > 0`; `amount > 0`; ikkala summa ham ko'pi bilan 2 kasr xonali
- `phone`: bo'shliq, `-`, `(`, `)` olib tashlanadi; natija `^\+?\d{7,15}$` bo'lishi kerak, aks holda 422. Tozalangan ko'rinishda saqlanadi
- `month`: `^\d{4}-(0[1-9]|1[0-2])$`, aks holda 422
- `paid_on <= bugun (Toshkent)`, aks holda 422
- Yo'q yoki o'chirilgan o'quvchi (GET/PATCH/DELETE/to'lov) → 404

## Veb-sahifa
Bitta sahifa, mobile-first: oy tanlagich (default joriy oy) → qarzdorlar kartochkalari (ism, guruh, to'langan / oylik, qarz). Kartochkaga bosilsa, formada shu o'quvchi tanlanadi. Forma: o'quvchi select (`GET /students` dan to'ldiriladi, `/debtors` dan emas — qarzi yo'q o'quvchiga ham to'lov qo'shish mumkin), summa (`inputmode="decimal"`), sana (default bugun) → `POST /payments` → ro'yxat yangilanadi; xato va muvaffaqiyat xabarlari.

## README
- Noldan ishga tushirish: `python -m venv .venv`, `pip install -r requirements.txt`, `uvicorn app.main:app --reload`, `pytest`
- O'quvchi (va uning guruhi) veb-sahifada emas, `/docs` (Swagger) orqali qo'shiladi/tahrirlanadi
- Qarorlar/taxminlar bo'limi (yuqoridagi jadval), shu jumladan: oylik summa o'zgarsa, o'tgan oylar ham yangi narx bilan hisoblanadi
- "Yana bir hafta bo'lsa" (3–5): oylar orasida qarz/ortiqchani ko'chirish va narx tarixi; telefonni qat'iy `+998XXXXXXXXX` ga normallashtirish; auth; guruhlarni alohida jadvalga chiqarish; PostgreSQL + Alembic + Docker (yig'indini SQL'da `NUMERIC` bilan hisoblash)

## Tekshirish
1. `uvicorn app.main:app` → `/docs` da o'quvchilar yaratish, to'lovlar qo'shish.
2. `GET /debtors?month=...`: to'lamagan (qarz = oylik), qisman to'lagan, ortiqcha to'lagan (ro'yxatda yo'q), 31-kuni va keyingi oyning 1-kuni qilingan to'lovlar to'g'ri oyga tushadi; oylik 0.30 bo'lgan o'quvchiga 0.10 + 0.20 to'lansa, u qarzdor bo'lib chiqmaydi.
3. O'quvchini o'chirish → ro'yxatda va qarzdorlarda yo'q, unga to'lov qo'shib bo'lmaydi (404).
4. `pytest` — hammasi yashil.
5. Brauzer DevTools mobil rejimida veb-sahifadan to'lov qo'shish.
