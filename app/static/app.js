"use strict";

// Summalar API'dan string ("500000.50") keladi va shunday yuboriladi —
// JS Number (float) bilan hisob-kitob qilinmaydi.

const $ = (id) => document.getElementById(id);

const els = {
  month: $("month"),
  debtors: $("debtors"),
  debtorsStatus: $("debtors-status"),
  debtorsCount: $("debtors-count"),
  form: $("pay-form"),
  student: $("student"),
  amount: $("amount"),
  paidOn: $("paid-on"),
  submit: $("submit"),
  message: $("form-message"),
  paySection: $("pay-section"),
};

const AMOUNT_RE = /^\d{1,10}(\.\d{1,2})?$/;

// "Bugun" — Asia/Tashkent bo'yicha (serverdagi qoida bilan bir xil).
function todayTashkent() {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Tashkent" }).format(new Date());
}

// "1500000.5" → "1 500 000.50" (faqat string bilan ishlaydi)
function formatMoney(value) {
  const [int, frac = ""] = String(value).split(".");
  const grouped = int.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  return `${grouped}.${frac.padEnd(2, "0")}`;
}

// "500 000,5" → "500000.5"
function normalizeAmount(raw) {
  return raw.replace(/[\s ]/g, "").replace(",", ".");
}

async function api(path, options = {}) {
  const resp = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const body = resp.status === 204 ? null : await resp.json().catch(() => null);
  if (!resp.ok) throw new Error(errorText(resp.status, body));
  return body;
}

function errorText(status, body) {
  const detail = body && body.detail;
  if (Array.isArray(detail)) {
    // FastAPI 422: [{loc: [..., "amount"], msg: "..."}]
    return detail
      .map((e) => `${e.loc[e.loc.length - 1]}: ${e.msg.replace(/^Value error, /, "")}`)
      .join("; ");
  }
  if (typeof detail === "string") return detail;
  return `Xatolik (${status})`;
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

// --- Qarzdorlar ---

async function loadDebtors() {
  const month = els.month.value;
  if (!month) return;
  els.debtorsStatus.hidden = false;
  els.debtorsStatus.textContent = "Yuklanmoqda…";
  els.debtors.replaceChildren();
  els.debtorsCount.hidden = true;

  try {
    const debtors = await api(`/debtors?month=${encodeURIComponent(month)}`);
    renderDebtors(debtors);
  } catch (err) {
    els.debtorsStatus.textContent = `Yuklab bo'lmadi: ${err.message}`;
  }
}

function renderDebtors(debtors) {
  if (debtors.length === 0) {
    els.debtorsStatus.textContent = "Bu oyda qarzdorlar yo'q.";
    return;
  }
  els.debtorsStatus.hidden = true;
  els.debtorsCount.hidden = false;
  els.debtorsCount.textContent = debtors.length;

  const items = debtors.map((d) => {
    const li = el("li");
    const btn = el("button", "debtor");
    btn.type = "button";
    btn.append(
      el("span", "debtor-name", d.name),
      el("span", "debtor-debt", formatMoney(d.debt)),
      el("span", "debtor-meta", `${d.group} · ${formatMoney(d.paid)} / ${formatMoney(d.monthly_fee)}`),
    );
    btn.setAttribute("aria-label", `${d.name}, qarz ${formatMoney(d.debt)} so'm — to'lov qo'shish`);
    btn.addEventListener("click", () => pickStudent(d.student_id, d.debt));
    li.append(btn);
    return li;
  });
  els.debtors.replaceChildren(...items);
}

function pickStudent(studentId, debt) {
  els.student.value = String(studentId);
  els.amount.value = debt;
  hideMessage();
  els.paySection.scrollIntoView({ behavior: "smooth", block: "start" });
  els.amount.focus({ preventScroll: true });
}

// --- O'quvchilar (select) ---

async function loadStudents() {
  try {
    const students = await api("/students");
    const placeholder = el("option", "", students.length ? "Tanlang…" : "O'quvchilar yo'q — /docs orqali qo'shing");
    placeholder.value = "";
    const options = students.map((s) => {
      const opt = el("option", "", `${s.name} — ${s.group} (#${s.id})`);
      opt.value = String(s.id);
      return opt;
    });
    els.student.replaceChildren(placeholder, ...options);
  } catch (err) {
    const opt = el("option", "", `Yuklab bo'lmadi: ${err.message}`);
    opt.value = "";
    els.student.replaceChildren(opt);
  }
}

// --- Forma ---

function showMessage(text, kind) {
  els.message.textContent = text;
  els.message.className = `message ${kind}`;
  els.message.hidden = false;
}

function hideMessage() {
  els.message.hidden = true;
  els.amount.removeAttribute("aria-invalid");
}

async function submitPayment(event) {
  event.preventDefault();
  hideMessage();

  const studentId = els.student.value;
  const amount = normalizeAmount(els.amount.value);
  const paidOn = els.paidOn.value;

  if (!studentId) return showMessage("O'quvchini tanlang.", "error");
  if (!AMOUNT_RE.test(amount) || /^0+(\.0+)?$/.test(amount)) {
    els.amount.setAttribute("aria-invalid", "true");
    els.amount.focus();
    return showMessage("Summa musbat son bo'lishi kerak, ko'pi bilan 2 kasr xona.", "error");
  }
  if (!paidOn) return showMessage("Sanani tanlang.", "error");

  els.submit.disabled = true;
  try {
    const payment = await api("/payments", {
      method: "POST",
      body: JSON.stringify({ student_id: Number(studentId), amount, paid_on: paidOn }),
    });
    const name = els.student.selectedOptions[0].textContent;
    showMessage(`Saqlandi: ${formatMoney(payment.amount)} so'm — ${name}, ${payment.paid_on}`, "ok");
    els.amount.value = "";
    await loadDebtors();
  } catch (err) {
    showMessage(err.message, "error");
  } finally {
    els.submit.disabled = false;
  }
}

// --- Ishga tushirish ---

function init() {
  const today = todayTashkent();
  els.month.value = today.slice(0, 7);
  els.paidOn.value = today;
  els.paidOn.max = today;

  els.month.addEventListener("change", loadDebtors);
  els.form.addEventListener("submit", submitPayment);
  els.amount.addEventListener("input", hideMessage);

  loadDebtors();
  loadStudents();
}

init();
