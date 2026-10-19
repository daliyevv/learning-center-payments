# Checklist — [task.md](task.md) bandlari

Belgilar: `[x]` bajarildi, `[ ]` bajarilmadi. Har bir band yonida — qayerda tekshirish mumkin.

## Umumiy
- [x] Stek tanlangan: Python (FastAPI) — `requirements.txt`
- [x] Ma'lumotlar bazasi: SQLite — `app/db.py`

## 1-qism. API
### 1. O'quvchilar: ism, telefon, guruh, oylik summa
- [x] Yaratish — `POST /students`
- [x] Ro'yxat — `GET /students`
- [x] O'zgartirish — `PATCH /students/{id}`
- [x] O'chirish — `DELETE /students/{id}` (soft delete)

### 2. To'lovlar: o'quvchi, summa, sana
- [x] Qo'shish — `POST /payments`
- [x] O'quvchi bo'yicha ro'yxat — `GET /students/{id}/payments`

### 3. Qarzdorlar
- [x] `GET /debtors?month=YYYY-MM` — `monthly_fee` dan kam to'laganlar
- [x] Har biri uchun qancha qarzi borligi (`debt`) qaytariladi
- [x] Umuman to'lamagan o'quvchi ham ro'yxatda

## 2-qism. Interfeys (variant B — veb-sahifa)
- [x] Qarzdorlar ro'yxati
- [x] To'lov qo'shish formasi — headless Chrome'da sinaldi: kartochka → forma, xato xabarlari, saqlash, ro'yxat yangilanishi
- [x] Telefonda qulay (mobile-first) — 390px mobil emulyatsiya: gorizontal scroll yo'q, tegish o'lchami ≥ 48px. Haqiqiy telefonda sinalmagan

## 3-qism. README
- [x] Noldan ishga tushirish (buyruqlar)
- [x] "Yana bir hafta bo'lsa" — 3–5 band

## 4-qism. AI haqida (chatga matn, 5–8 gap — repoda emas)
- [ ] Qaysi vositalar va promptlar eng yaxshi natija berdi
- [ ] AI qayerda xato qildi, qanday topildi va tuzatildi
- [ ] Kodning qaysi qismini o'zim yozdim, qaysini AI yaratdi

## Yuborish (Telegram @code_debugger007)
- [x] GitHub repozitoriy havolasi — https://github.com/daliyevv/learning-center-payments
- [ ] 4-qism matni
- [ ] Sarflangan soatlar

## Qo'shimcha (TZ'da yo'q, rejada bor)
- [x] Validatsiya: 404 / 422 — `app/schemas.py`
- [x] Asia/Tashkent bo'yicha "bugun" / "joriy oy" — `app/timeutil.py`
- [x] pytest testlari yashil (73 ta) — `tests/`
- [x] README'da qarorlar/taxminlar bo'limi
