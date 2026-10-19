# CLAUDE.md

O'quv markazi to'lovlar mini-hisobi (test topshiriq). TZ: @docs/task.md
To'liq reja va qarorlar: @docs/plan.md — qaror o'zgarsa, avval shu faylni yangila.
Bajarilganlar: @docs/checklist.md — har bir band tugagach belgilab bor.

## Buyruqlar
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload        # http://127.0.0.1:8000  (Swagger: /docs)
pytest                               # barcha testlar
pytest tests/test_debtors.py -q      # faqat qarz mantig'i
```

## Stek
- Python 3.12, FastAPI, SQLAlchemy 2.0 (sync), Pydantic v2, SQLite (`data.db`).
- Jadvallar ishga tushganda `Base.metadata.create_all` bilan yaratiladi.
- Alembic, Docker, PostgreSQL, ORM'dan tashqari kutubxonalar — **qo'shma**.
- Frontend: `app/static/` dagi vanilla HTML/CSS/JS. Framework, bundler, CDN yo'q.

## Qamrov qoidalari
- Faqat @docs/task.md va @docs/plan.md dagi narsalarni qil. Yangi maydon, endpoint, jadval — avval so'ra.
- Guruh — o'quvchidagi oddiy matn maydoni (`group`), alohida jadval yo'q.
- Interfeys — faqat veb-sahifa (variant B). Telegram-bot yo'q.
- O'quvchi qo'shish/tahrirlash UI'da yo'q — faqat `/docs` orqali.

## Pul
- Barcha summalar `Decimal`, ustun `Numeric(12, 2)`, JSON'da string.
- `float` hech qayerda ishlatilmaydi (kodda, testda, JS hisob-kitobida).
- SQLite `Numeric`ni REAL saqlaydi → `SUM()` va summa taqqoslashni **SQL'da qilma**.
  Qatorlarni tanla, yig'indini Python'da `sum(..., Decimal("0"))` bilan hisobla.
- Summalar > 0, ko'pi bilan 2 kasr xonasi.

## Qarz mantig'i
- `debt = monthly_fee − paid`, `paid` = shu oy `[oy boshi; keyingi oy boshi)` to'lovlari yig'indisi.
- `paid < monthly_fee` bo'lsa qarzdor; to'lovi umuman yo'q o'quvchi ham qarzdor.
- Faqat faol (`deleted_at IS NULL`) o'quvchilar. `created_at` bo'yicha filtr yo'q.
- Carry-over, proporsional hisob, narx tarixi **yo'q** — qo'shma.
- Natija debt bo'yicha kamayish tartibida.

## Sana va vaqt
- To'lov sanasi — `DATE` (`paid_on`), default bugun.
- "Bugun" va "joriy oy" faqat `app/timeutil.py` orqali (Asia/Tashkent, `zoneinfo`).
  `date.today()` / `datetime.now()` ni to'g'ridan-to'g'ri chaqirma.
- Kelajak sana → 422.

## O'chirish
- Soft delete: `deleted_at` qo'yiladi, to'lovlar o'chirilmaydi.
- O'chirilgan o'quvchi: ro'yxatda yo'q, GET/PATCH/DELETE/to'lov → 404.

## Xatolar va validatsiya
- Faqat 404 (topilmadi / o'chirilgan) va 422 (validatsiya). 409 ishlatilmaydi.
- Validatsiya Pydantic sxemalarida (`app/schemas.py`), routerlarda emas.
- Telefon: bo'shliq, `-`, `(`, `)` olib tashlanadi → `^\+?\d{7,15}$`, tozalangan holda saqlanadi.
- `month`: `^\d{4}-(0[1-9]|1[0-2])$`.

## Testlar
- Har bir xatti-harakat o'zgarishiga test (pytest, `fastapi.testclient`).
- Testlar in-memory SQLite bilan (`tests/conftest.py`), `data.db` ga tegmaydi.
- Sanaga bog'liq testlarda "bugun"ni monkeypatch qil, haqiqiy sanaga tayanma.
- Ish "tayyor" deyishdan oldin `pytest` ni ishga tushir va natijani ko'rsat.

## Kod uslubi
- Kichik, aniq modullar: `models.py`, `schemas.py`, `debtors.py`, `timeutil.py`, `routers/`.
- Type hint'lar hamma joyda. Ortiqcha abstraksiya (repository, service layer) yo'q.
- Izohlar faqat "nega" uchun.

## Git
- `data.db`, `.venv`, `__pycache__`, `notes.md` commit qilinmaydi.
- Commit faqat foydalanuvchi so'raganda.
