from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import sqlite3, os, hashlib, secrets
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.permanent_session_lifetime = timedelta(days=7)

DB = "dashboard.db"

"""
# ── SET TIME ──────────────────────────────────────────────────────────────────

def now_wib():
    return datetime.now(ZoneInfo("Asia/Jakarta"))

"""
# i added this line inside pythonanywhere because they didn't use my current time region
# for now the time is always set to WIB no matter where you are, this is a big oversight but i only intend to use this web-app around my campus

# ── DATABASE ──────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with get_db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT UNIQUE NOT NULL,
            password   TEXT NOT NULL,
            full_name  TEXT NOT NULL,
            role       TEXT NOT NULL DEFAULT 'student',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS task_types (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name    TEXT NOT NULL,
            color   TEXT NOT NULL DEFAULT '#2d5a27',
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER NOT NULL,
            date      TEXT NOT NULL,
            task      TEXT NOT NULL,
            type_name TEXT DEFAULT '',
            done      INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS expenses (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER NOT NULL,
            date      TEXT NOT NULL,
            amount    INTEGER NOT NULL,
            desc      TEXT DEFAULT '',
            type_name TEXT DEFAULT 'Lainnya',
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS budgets (
            user_id     INTEGER PRIMARY KEY,
            amount      INTEGER DEFAULT 0,
            budget_mode TEXT    DEFAULT 'monthly',
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        -- Migrasi: tambah kolom budget_mode jika belum ada (untuk DB lama)
        CREATE TABLE IF NOT EXISTS recurring_tasks (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER NOT NULL,
            name      TEXT NOT NULL,
            type_name TEXT DEFAULT '',
            days      TEXT NOT NULL DEFAULT '',
            active    INTEGER DEFAULT 1,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS recurring_skips (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            recurring_id INTEGER NOT NULL,
            week_key     TEXT NOT NULL,
            done         INTEGER DEFAULT 0,
            FOREIGN KEY(user_id)      REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(recurring_id) REFERENCES recurring_tasks(id) ON DELETE CASCADE,
            UNIQUE(recurring_id, week_key)
        );
        """)
        # Buat admin default jika belum ada
        if not c.execute("SELECT id FROM users WHERE role='admin' LIMIT 1").fetchone():
            c.execute(
                "INSERT INTO users (username,password,full_name,role) VALUES (?,?,?,?)",
                ("admin", hash_pw("admin123"), "Administrator", "admin")
            )
        # Migrasi kolom budget_mode untuk database yang sudah ada
        try:
            c.execute("ALTER TABLE budgets ADD COLUMN budget_mode TEXT DEFAULT 'monthly'")
            c.commit()
        except Exception:
            pass  # kolom sudah ada
        c.commit()

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ── AUTH HELPERS ──────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def wrapped(*a, **kw):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*a, **kw)
    return wrapped

def api_login_required(f):
    @wraps(f)
    def wrapped(*a, **kw):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*a, **kw)
    return wrapped

def uid():
    return session["user_id"]

# ── AUTH ROUTES ───────────────────────────────────────────────────────────────

@app.route("/")
def root():
    return redirect(url_for("dashboard") if "user_id" in session else url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with get_db() as c:
            user = c.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if user and user["password"] == hash_pw(password):
            session.permanent = True
            session.update(user_id=user["id"], username=user["username"],
                           full_name=user["full_name"], role=user["role"])
            return redirect(url_for("dashboard"))
        error = "Username atau password salah."
    return render_template("login.html", error=error)

@app.route("/register", methods=["GET", "POST"])
def register():
    error = success = None
    if request.method == "POST":
        username  = request.form.get("username", "").strip()
        password  = request.form.get("password", "")
        password2 = request.form.get("password2", "")
        full_name = request.form.get("full_name", "").strip()
        if not all([username, password, full_name]):
            error = "Semua field wajib diisi."
        elif len(username) < 3:
            error = "Username minimal 3 karakter."
        elif len(password) < 6:
            error = "Password minimal 6 karakter."
        elif password != password2:
            error = "Konfirmasi password tidak cocok."
        else:
            try:
                with get_db() as c:
                    c.execute(
                        "INSERT INTO users (username,password,full_name) VALUES (?,?,?)",
                        (username, hash_pw(password), full_name)
                    )
                    c.commit()
                success = "Akun berhasil dibuat! Silakan login."
            except sqlite3.IntegrityError:
                error = "Username sudah digunakan, coba yang lain."
    return render_template("register.html", error=error, success=success)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ── DASHBOARD ─────────────────────────────────────────────────────────────────

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("index.html",
        username=session["username"],
        full_name=session["full_name"],
        role=session["role"])

# ── API: DATA ─────────────────────────────────────────────────────────────────

@app.route("/api/today")
@api_login_required
def api_today():
    return jsonify({"date": datetime.now().strftime("%Y-%m-%d")})
    # Each any every datetime.now() has been changed to now_wib() inside pythonanywhere

@app.route("/api/data")
@api_login_required
def api_data():
    u = uid()
    with get_db() as c:
        types = [dict(r) for r in c.execute(
            "SELECT name,color FROM task_types WHERE user_id=? ORDER BY id", (u,))]
        tasks = {}
        for r in c.execute("SELECT id,date,task,type_name,done FROM tasks WHERE user_id=? ORDER BY id", (u,)):
            tasks.setdefault(r["date"], []).append(
                {"id": r["id"], "task": r["task"], "type": r["type_name"], "done": bool(r["done"])})
        expenses = {}
        for r in c.execute("SELECT id,date,amount,desc,type_name FROM expenses WHERE user_id=? ORDER BY id", (u,)):
            expenses.setdefault(r["date"], []).append(
                {"id": r["id"], "amount": r["amount"], "desc": r["desc"], "type": r["type_name"]})
        brow = c.execute("SELECT amount,budget_mode FROM budgets WHERE user_id=?", (u,)).fetchone()
        period_data = fetch_all_expenses(c, u)
    return jsonify({"task_types": types, "tasks": tasks,
                    "expenses": expenses,
                    "budget":      brow["amount"]      if brow else 0,
                    "budget_mode": brow["budget_mode"] if brow else "monthly",
                    "period_used":  period_data["period_used"],
                    "period_start": period_data["period_start"],
                    "period_end":   period_data["period_end"]})

# ── API: TASK TYPES ───────────────────────────────────────────────────────────

def fetch_types(c, u):
    return [dict(r) for r in c.execute(
        "SELECT name,color FROM task_types WHERE user_id=? ORDER BY id", (u,))]

@app.route("/api/task_types", methods=["POST"])
@api_login_required
def add_task_type():
    u = uid(); b = request.json
    name = b.get("name","").strip(); color = b.get("color","#2d5a27")
    if not name: return jsonify({"error":"Name required"}), 400
    with get_db() as c:
        if not c.execute("SELECT id FROM task_types WHERE user_id=? AND name=?", (u,name)).fetchone():
            c.execute("INSERT INTO task_types (user_id,name,color) VALUES (?,?,?)", (u,name,color))
            c.commit()
        return jsonify(fetch_types(c, u))

@app.route("/api/task_types/<name>", methods=["DELETE"])
@api_login_required
def del_task_type(name):
    u = uid()
    with get_db() as c:
        c.execute("DELETE FROM task_types WHERE user_id=? AND name=?", (u,name)); c.commit()
        return jsonify(fetch_types(c, u))

# ── API: TASKS ────────────────────────────────────────────────────────────────

def fetch_tasks(c, u, date):
    return [{"id":r["id"],"task":r["task"],"type":r["type_name"],"done":bool(r["done"])}
            for r in c.execute(
                "SELECT id,task,type_name,done FROM tasks WHERE user_id=? AND date=? ORDER BY id",
                (u,date))]

@app.route("/api/tasks", methods=["POST"])
@api_login_required
def add_task():
    u = uid(); b = request.json
    date = b.get("date"); task = b.get("task","").strip(); ttype = b.get("type","")
    if not date or not task: return jsonify({"error":"Missing"}), 400
    with get_db() as c:
        c.execute("INSERT INTO tasks (user_id,date,task,type_name) VALUES (?,?,?,?)",
                  (u,date,task,ttype)); c.commit()
        return jsonify(fetch_tasks(c, u, date))

@app.route("/api/tasks/<int:tid>/toggle", methods=["POST"])
@api_login_required
def toggle_task(tid):
    u = uid()
    with get_db() as c:
        row = c.execute("SELECT date,done FROM tasks WHERE id=? AND user_id=?", (tid,u)).fetchone()
        if not row: return jsonify({"error":"Not found"}), 404
        c.execute("UPDATE tasks SET done=? WHERE id=?", (0 if row["done"] else 1, tid)); c.commit()
        return jsonify(fetch_tasks(c, u, row["date"]))

@app.route("/api/tasks/<int:tid>", methods=["DELETE"])
@api_login_required
def del_task(tid):
    u = uid()
    with get_db() as c:
        row = c.execute("SELECT date FROM tasks WHERE id=? AND user_id=?", (tid,u)).fetchone()
        if not row: return jsonify({"error":"Not found"}), 404
        c.execute("DELETE FROM tasks WHERE id=?", (tid,)); c.commit()
        return jsonify(fetch_tasks(c, u, row["date"]))

# ── API: EXPENSES ─────────────────────────────────────────────────────────────

def current_period_range(mode):
    """Return (date_start, date_end) string tuple for current week or month."""
    today = datetime.now()
    if mode == "weekly":
        # Senin s.d. Minggu minggu ini
        start = today - timedelta(days=today.weekday())
        end   = start + timedelta(days=6)
    else:
        # 1 s.d. akhir bulan ini
        start = today.replace(day=1)
        # akhir bulan: hari pertama bulan depan - 1 hari
        if today.month == 12:
            end = today.replace(year=today.year+1, month=1, day=1) - timedelta(days=1)
        else:
            end = today.replace(month=today.month+1, day=1) - timedelta(days=1)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

def fetch_all_expenses(c, u):
    # Ambil semua pengeluaran (untuk tampilan kalender & panel)
    exp = {}
    for r in c.execute("SELECT id,date,amount,desc,type_name FROM expenses WHERE user_id=? ORDER BY id", (u,)):
        exp.setdefault(r["date"],[]).append(
            {"id":r["id"],"amount":r["amount"],"desc":r["desc"],"type":r["type_name"]})

    brow = c.execute("SELECT amount,budget_mode FROM budgets WHERE user_id=?", (u,)).fetchone()
    budget = brow["amount"] if brow else 0
    mode   = brow["budget_mode"] if brow else "monthly"

    # Hitung pengeluaran HANYA dalam periode berjalan
    date_start, date_end = current_period_range(mode)
    period_exp = []
    for date, items in exp.items():
        if date_start <= date <= date_end:
            period_exp.extend(items)
    period_used = sum(int(e["amount"]) for e in period_exp)

    return {
        "expenses":    exp,
        "budget":      budget,
        "budget_mode": mode,
        "period_used": period_used,
        "period_start": date_start,
        "period_end":   date_end,
    }

@app.route("/api/expenses", methods=["POST"])
@api_login_required
def add_expense():
    u = uid(); b = request.json
    date=b.get("date"); amount=b.get("amount",0)
    if not date or not amount: return jsonify({"error":"Missing"}), 400
    with get_db() as c:
        c.execute("INSERT INTO expenses (user_id,date,amount,desc,type_name) VALUES (?,?,?,?,?)",
                  (u,date,int(amount),b.get("desc",""),b.get("type","Lainnya"))); c.commit()
        return jsonify(fetch_all_expenses(c, u))

@app.route("/api/expenses/<int:eid>", methods=["DELETE"])
@api_login_required
def del_expense(eid):
    u = uid()
    with get_db() as c:
        if not c.execute("SELECT id FROM expenses WHERE id=? AND user_id=?", (eid,u)).fetchone():
            return jsonify({"error":"Not found"}), 404
        c.execute("DELETE FROM expenses WHERE id=?", (eid,)); c.commit()
        return jsonify(fetch_all_expenses(c, u))

@app.route("/api/budget", methods=["POST"])
@api_login_required
def set_budget():
    u      = uid()
    amount = int(request.json.get("budget", 0))
    mode   = request.json.get("mode", "monthly")
    if mode not in ("monthly", "weekly"):
        mode = "monthly"
    with get_db() as c:
        c.execute(
            "INSERT INTO budgets (user_id,amount,budget_mode) VALUES (?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET amount=excluded.amount, budget_mode=excluded.budget_mode",
            (u, amount, mode)
        )
        c.commit()
        data = fetch_all_expenses(c, u)
    return jsonify({"budget": amount, "budget_mode": mode,
                    "period_used": data["period_used"],
                    "period_start": data["period_start"],
                    "period_end": data["period_end"]})


# ── API: RECURRING TASKS ─────────────────────────────────────────────────────

def week_key(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d")
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"

def js_dow(date_str):
    """0=Sun, 1=Mon, ..., 6=Sat  (JS convention stored in DB)"""
    py_dow = datetime.strptime(date_str, "%Y-%m-%d").weekday()  # 0=Mon
    return (py_dow + 1) % 7   # Mon(0)->1, Sun(6)->0

def fetch_recurring_list(c, u):
    rows = c.execute(
        "SELECT id,name,type_name,days,active FROM recurring_tasks WHERE user_id=? ORDER BY id", (u,)
    ).fetchall()
    return [{"id":r["id"],"name":r["name"],"type":r["type_name"],
             "days":[int(x) for x in r["days"].split(",") if x],
             "active":bool(r["active"])} for r in rows]

def fetch_recurring_status(c, u, date_str):
    wk  = week_key(date_str)
    dow = js_dow(date_str)
    rows = c.execute(
        "SELECT id,name,type_name,days FROM recurring_tasks WHERE user_id=? AND active=1", (u,)
    ).fetchall()
    result = []
    for r in rows:
        day_list = [int(x) for x in r["days"].split(",") if x]
        if dow not in day_list:
            continue
        skip = c.execute(
            "SELECT done FROM recurring_skips WHERE recurring_id=? AND week_key=?",
            (r["id"], wk)
        ).fetchone()
        status = "done" if (skip and skip["done"]==1) else \
                 "skipped" if (skip and skip["done"]==0) else "pending"
        result.append({"id":r["id"],"name":r["name"],"type":r["type_name"],
                        "week_key":wk,"status":status})
    return result

@app.route("/api/recurring")
@api_login_required
def get_recurring():
    u = uid()
    with get_db() as c:
        return jsonify(fetch_recurring_list(c, u))

@app.route("/api/recurring", methods=["POST"])
@api_login_required
def add_recurring():
    u = uid(); b = request.json
    name = b.get("name","").strip(); ttype = b.get("type","")
    days = b.get("days",[])
    if not name or not days:
        return jsonify({"error":"Name and days required"}), 400
    days_str = ",".join(str(d) for d in sorted(set(days)))
    with get_db() as c:
        c.execute("INSERT INTO recurring_tasks (user_id,name,type_name,days) VALUES (?,?,?,?)",
                  (u,name,ttype,days_str)); c.commit()
        return jsonify(fetch_recurring_list(c, u))

@app.route("/api/recurring/<int:rid>", methods=["DELETE"])
@api_login_required
def del_recurring(rid):
    u = uid()
    with get_db() as c:
        c.execute("DELETE FROM recurring_tasks WHERE id=? AND user_id=?", (rid,u)); c.commit()
        return jsonify(fetch_recurring_list(c, u))

@app.route("/api/recurring/<int:rid>/toggle_active", methods=["POST"])
@api_login_required
def toggle_active_recurring(rid):
    u = uid()
    with get_db() as c:
        row = c.execute("SELECT active FROM recurring_tasks WHERE id=? AND user_id=?",(rid,u)).fetchone()
        if not row: return jsonify({"error":"Not found"}), 404
        c.execute("UPDATE recurring_tasks SET active=? WHERE id=?", (0 if row["active"] else 1, rid))
        c.commit()
        return jsonify(fetch_recurring_list(c, u))

@app.route("/api/recurring/status")
@api_login_required
def recurring_status():
    u = uid(); date = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    with get_db() as c:
        return jsonify(fetch_recurring_status(c, u, date))

@app.route("/api/recurring/<int:rid>/done", methods=["POST"])
@api_login_required
def mark_recurring_done(rid):
    u = uid(); b = request.json; wk = b.get("week_key",""); date = b.get("date","")
    if not wk: return jsonify({"error":"week_key required"}), 400
    with get_db() as c:
        c.execute("""INSERT INTO recurring_skips (user_id,recurring_id,week_key,done) VALUES (?,?,?,1)
                     ON CONFLICT(recurring_id,week_key) DO UPDATE SET done=1""", (u,rid,wk))
        c.commit()
        return jsonify(fetch_recurring_status(c, u, date or datetime.now().strftime("%Y-%m-%d")))

@app.route("/api/recurring/<int:rid>/skip", methods=["POST"])
@api_login_required
def skip_recurring(rid):
    u = uid(); b = request.json; wk = b.get("week_key",""); date = b.get("date","")
    if not wk: return jsonify({"error":"week_key required"}), 400
    with get_db() as c:
        c.execute("""INSERT INTO recurring_skips (user_id,recurring_id,week_key,done) VALUES (?,?,?,0)
                     ON CONFLICT(recurring_id,week_key) DO UPDATE SET done=0""", (u,rid,wk))
        c.commit()
        return jsonify(fetch_recurring_status(c, u, date or datetime.now().strftime("%Y-%m-%d")))

@app.route("/api/recurring/<int:rid>/undone", methods=["POST"])
@api_login_required
def undone_recurring(rid):
    u = uid(); b = request.json; wk = b.get("week_key",""); date = b.get("date","")
    with get_db() as c:
        c.execute("DELETE FROM recurring_skips WHERE recurring_id=? AND week_key=? AND user_id=?",
                  (rid,wk,u)); c.commit()
        return jsonify(fetch_recurring_status(c, u, date or datetime.now().strftime("%Y-%m-%d")))

# ── API: GANTI PASSWORD ───────────────────────────────────────────────────────

@app.route("/api/change_password", methods=["POST"])
@api_login_required
def change_password():
    u = uid(); b = request.json
    old_pw = b.get("old_password",""); new_pw = b.get("new_password","")
    if len(new_pw) < 6: return jsonify({"error":"Password baru minimal 6 karakter"}), 400
    with get_db() as c:
        user = c.execute("SELECT password FROM users WHERE id=?", (u,)).fetchone()
        if not user or user["password"] != hash_pw(old_pw):
            return jsonify({"error":"Password lama salah"}), 401
        c.execute("UPDATE users SET password=? WHERE id=?", (hash_pw(new_pw), u)); c.commit()
    return jsonify({"ok": True})

# ── ADMIN ROUTES ──────────────────────────────────────────────────────────────

def admin_required(f):
    @wraps(f)
    def wrapped(*a, **kw):
        if "user_id" not in session: return redirect(url_for("login"))
        if session.get("role") != "admin": return jsonify({"error":"Forbidden"}), 403
        return f(*a, **kw)
    return wrapped

@app.route("/admin")
@admin_required
def admin_panel():
    return render_template("admin.html",
        username=session["username"], full_name=session["full_name"], role=session["role"])

@app.route("/api/admin/stats")
@admin_required
def admin_stats():
    with get_db() as c:
        return jsonify({
            "total_users":    c.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0],
            "total_tasks":    c.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],
            "tasks_done":     c.execute("SELECT COUNT(*) FROM tasks WHERE done=1").fetchone()[0],
            "total_expenses": c.execute("SELECT COALESCE(SUM(amount),0) FROM expenses").fetchone()[0],
        })

@app.route("/api/admin/users")
@admin_required
def admin_users():
    with get_db() as c:
        rows = c.execute(
            "SELECT id,username,full_name,role,created_at FROM users ORDER BY role DESC,full_name"
        ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/admin/users", methods=["POST"])
@admin_required
def admin_create():
    b = request.json
    username=b.get("username","").strip(); pw=b.get("password","")
    full_name=b.get("full_name","").strip(); role=b.get("role","student")
    if not all([username,pw,full_name]): return jsonify({"error":"Semua field wajib diisi"}), 400
    try:
        with get_db() as c:
            c.execute("INSERT INTO users (username,password,full_name,role) VALUES (?,?,?,?)",
                      (username,hash_pw(pw),full_name,role)); c.commit()
        return jsonify({"ok":True})
    except sqlite3.IntegrityError:
        return jsonify({"error":"Username sudah digunakan"}), 409

@app.route("/api/admin/users/<int:target>", methods=["DELETE"])
@admin_required
def admin_delete(target):
    if target == uid(): return jsonify({"error":"Tidak bisa hapus akun sendiri"}), 400
    with get_db() as c:
        c.execute("DELETE FROM users WHERE id=?", (target,)); c.commit()
    return jsonify({"ok":True})

@app.route("/api/admin/users/<int:target>/reset", methods=["POST"])
@admin_required
def admin_reset(target):
    new_pw = request.json.get("password","")
    if len(new_pw) < 6: return jsonify({"error":"Password minimal 6 karakter"}), 400
    with get_db() as c:
        c.execute("UPDATE users SET password=? WHERE id=?", (hash_pw(new_pw),target)); c.commit()
    return jsonify({"ok":True})

# ── MAIN ──────────────────────────────────────────────────────────────────────

init_db()  # selalu jalan — baik via PythonAnywhere maupun lokal

if __name__ == "__main__":
    print("\n╔══════════════════════════════════════╗")
    print("║   Dashboard Kelompok                 ║")
    print("║   http://localhost:5050              ║")
    print("║   Admin: admin / admin123            ║")
    print("╚══════════════════════════════════════╝\n")
    app.run(debug=True, port=5050, host="0.0.0.0")
