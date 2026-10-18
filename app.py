import os, sqlite3, json
from functools import wraps
from datetime import datetime
from urllib.parse import quote
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-before-publishing")
DB_NAME = os.path.join(os.path.dirname(__file__), "rang_e_husn.db")
WHATSAPP_NUMBER = "923186957897"  # 03186957897 in international format
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ChangeMe123!")  # Change before public hosting

DEFAULT_SERVICES = [
    ("Party Makeup", 3500, "Elegant makeup for parties and special events.", "💄"),
    ("Bridal Makeup", 18000, "A beautiful bridal look planned with you.", "👰"),
    ("Facial & Skin Care", 1800, "A relaxing facial for a fresh, cared-for look.", "🌸"),
    ("Hair Styling", 1500, "Styling for everyday events and celebrations.", "💇‍♀️"),
    ("Manicure & Pedicure", 2000, "A little self-care from hands to feet.", "💅"),
    ("Mehndi", 1200, "Traditional mehndi designs for your occasion.", "🌿"),
]
DEFAULT_PRODUCTS = [
    ("Hydrating Face Cream", 950, "Daily moisture for soft-feeling skin.", "🧴", 20, 1),
    ("Gentle Face Cleanser", 650, "A gentle cleanser for your daily routine.", "🫧", 20, 1),
    ("Lip Care Balm", 350, "A simple lip-care essential.", "💋", 30, 1),
    ("Beauty Brush Set", 1200, "A handy set for makeup application.", "🖌️", 10, 1),
    ("Hair Serum", 800, "For a smooth, polished hair finish.", "✨", 15, 1),
    ("Sheet Face Mask", 250, "A quick self-care treat.", "🌷", 40, 1),
]

def db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS services (
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, price INTEGER NOT NULL,
          description TEXT NOT NULL DEFAULT '', emoji TEXT NOT NULL DEFAULT '🌸', active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS products (
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, price INTEGER NOT NULL,
          description TEXT NOT NULL DEFAULT '', emoji TEXT NOT NULL DEFAULT '🧴',
          stock INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS appointments (
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, phone TEXT NOT NULL,
          service TEXT NOT NULL, appointment_date TEXT NOT NULL, appointment_time TEXT NOT NULL,
          notes TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'Pending',
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS orders (
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, phone TEXT NOT NULL,
          address TEXT NOT NULL, items_json TEXT NOT NULL, total INTEGER NOT NULL,
          payment_method TEXT NOT NULL DEFAULT 'Cash on delivery / confirm on WhatsApp',
          status TEXT NOT NULL DEFAULT 'Pending', created_at TEXT NOT NULL
        );
        """)
        if conn.execute("SELECT COUNT(*) FROM services").fetchone()[0] == 0:
            conn.executemany("INSERT INTO services (name,price,description,emoji) VALUES (?,?,?,?)", DEFAULT_SERVICES)
        if conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
            conn.executemany("INSERT INTO products (name,price,description,emoji,stock,active) VALUES (?,?,?,?,?,?)", DEFAULT_PRODUCTS)

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper

@app.context_processor
def inject_globals():
    return {"shop_name": "Rang-e-Husn Beauty Parlour"}

@app.route("/")
def home():
    with db() as conn:
        services = conn.execute("SELECT * FROM services WHERE active=1 ORDER BY id").fetchall()
        products = conn.execute("SELECT * FROM products WHERE active=1 ORDER BY id").fetchall()
    return render_template("index.html", services=services, products=products, whatsapp=WHATSAPP_NUMBER)

@app.post("/book")
def book():
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    service_id = request.form.get("service_id", "").strip()
    date = request.form.get("date", "").strip()
    time = request.form.get("time", "").strip()
    notes = request.form.get("notes", "").strip()
    if not all([name, phone, service_id, date, time]):
        flash("Please fill in all required appointment fields.", "error")
        return redirect(url_for("home") + "#appointment")
    with db() as conn:
        service = conn.execute("SELECT name FROM services WHERE id=? AND active=1", (service_id,)).fetchone()
        if not service:
            flash("Please choose a valid service.", "error")
            return redirect(url_for("home") + "#appointment")
        conn.execute("""INSERT INTO appointments(name,phone,service,appointment_date,appointment_time,notes,created_at)
                        VALUES(?,?,?,?,?,?,?)""",
                     (name, phone, service["name"], date, time, notes, datetime.now().isoformat(timespec="seconds")))
    msg = f"Assalam-o-Alaikum! Appointment request for Rang-e-Husn.%0AName: {quote(name)}%0APhone: {quote(phone)}%0AService: {quote(service['name'])}%0ADate: {quote(date)}%0ATime: {quote(time)}%0ANotes: {quote(notes or 'None')}"
    flash("Appointment request saved. Continue to WhatsApp to request confirmation.", "success")
    return redirect(f"https://wa.me/{WHATSAPP_NUMBER}?text={msg}")

@app.post("/checkout")
def checkout():
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    raw = request.form.get("cart", "[]")
    if not all([name, phone, address]):
        flash("Please complete your name, phone and delivery address.", "error")
        return redirect(url_for("home") + "#shop")
    try:
        items = json.loads(raw)
    except (ValueError, TypeError):
        items = []
    clean, total = [], 0
    with db() as conn:
        for item in items if isinstance(items, list) else []:
            try:
                pid, qty = int(item.get("id")), max(1, min(50, int(item.get("qty", 1))))
            except (ValueError, TypeError, AttributeError):
                continue
            product = conn.execute("SELECT * FROM products WHERE id=? AND active=1", (pid,)).fetchone()
            if not product:
                continue
            if product["stock"] < qty:
                flash(f"Not enough stock for {product['name']}. Please adjust your cart.", "error")
                return redirect(url_for("home") + "#shop")
            line_total = product["price"] * qty
            clean.append({"id": pid, "name": product["name"], "qty": qty, "price": product["price"], "line_total": line_total})
            total += line_total
        if not clean:
            flash("Your cart is empty. Add a product before checkout.", "error")
            return redirect(url_for("home") + "#shop")
        cur = conn.execute("""INSERT INTO orders(name,phone,address,items_json,total,created_at)
                              VALUES(?,?,?,?,?,?)""",
                           (name, phone, address, json.dumps(clean), total, datetime.now().isoformat(timespec="seconds")))
        order_id = cur.lastrowid
        for item in clean:
            conn.execute("UPDATE products SET stock=stock-? WHERE id=?", (item["qty"], item["id"]))
    item_lines = "\n".join(f"- {i['name']} x {i['qty']} = Rs. {i['line_total']:,}" for i in clean)
    msg = f"Assalam-o-Alaikum! New Rang-e-Husn order request #{order_id}\nName: {name}\nPhone: {phone}\nAddress: {address}\n{item_lines}\nTotal: Rs. {total:,}\nPlease confirm delivery and payment."
    return render_template("success.html", title="Order Request Received", message="Your order has been saved. Continue to WhatsApp so the shop can confirm availability, delivery and payment.", order_id=order_id, whatsapp_url=f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(msg)}")

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(request.args.get("next") or url_for("admin_dashboard"))
        flash("Incorrect username or password.", "error")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    with db() as conn:
        orders = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
        appointments = conn.execute("SELECT * FROM appointments ORDER BY id DESC").fetchall()
        products = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
        services = conn.execute("SELECT * FROM services ORDER BY id").fetchall()
        stats = {
            "orders": conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
            "appointments": conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0],
            "products": conn.execute("SELECT COUNT(*) FROM products").fetchone()[0],
            "pending": conn.execute("SELECT COUNT(*) FROM orders WHERE status='Pending'").fetchone()[0]
        }
    return render_template("admin.html", orders=orders, appointments=appointments, products=products, services=services, stats=stats)

@app.post("/admin/product/save")
@admin_required
def save_product():
    try:
        pid = request.form.get("id", "").strip()
        name = request.form.get("name", "").strip()
        price = int(request.form.get("price", "0"))
        stock = int(request.form.get("stock", "0"))
        description = request.form.get("description", "").strip()
        emoji = request.form.get("emoji", "🧴").strip() or "🧴"
        active = 1 if request.form.get("active") == "on" else 0
        if not name or price < 0 or stock < 0:
            raise ValueError
        with db() as conn:
            if pid:
                conn.execute("UPDATE products SET name=?,price=?,description=?,emoji=?,stock=?,active=? WHERE id=?",
                             (name, price, description, emoji, stock, active, int(pid)))
            else:
                conn.execute("INSERT INTO products(name,price,description,emoji,stock,active) VALUES(?,?,?,?,?,?)",
                             (name, price, description, emoji, stock, active))
        flash("Product saved.", "success")
    except (ValueError, TypeError):
        flash("Please enter a valid product name, price and stock.", "error")
    return redirect(url_for("admin_dashboard") + "#products")

@app.post("/admin/product/delete")
@admin_required
def delete_product():
    try:
        pid = int(request.form.get("id", "0"))
        with db() as conn:
            conn.execute("UPDATE products SET active=0 WHERE id=?", (pid,))
        flash("Product hidden from the store. Past orders are preserved.", "success")
    except ValueError:
        flash("Invalid product.", "error")
    return redirect(url_for("admin_dashboard") + "#products")

@app.post("/admin/service/save")
@admin_required
def save_service():
    try:
        sid = request.form.get("id", "").strip()
        name = request.form.get("name", "").strip()
        price = int(request.form.get("price", "0"))
        description = request.form.get("description", "").strip()
        emoji = request.form.get("emoji", "🌸").strip() or "🌸"
        active = 1 if request.form.get("active") == "on" else 0
        if not name or price < 0:
            raise ValueError
        with db() as conn:
            if sid:
                conn.execute("UPDATE services SET name=?,price=?,description=?,emoji=?,active=? WHERE id=?",
                             (name, price, description, emoji, active, int(sid)))
            else:
                conn.execute("INSERT INTO services(name,price,description,emoji,active) VALUES(?,?,?,?,?)",
                             (name, price, description, emoji, active))
        flash("Service saved.", "success")
    except (ValueError, TypeError):
        flash("Please enter a valid service name and price.", "error")
    return redirect(url_for("admin_dashboard") + "#services-admin")

@app.post("/admin/order/status")
@admin_required
def order_status():
    status = request.form.get("status", "")
    if status not in ["Pending", "Confirmed", "Preparing", "Dispatched", "Completed", "Cancelled"]:
        abort(400)
    with db() as conn:
        conn.execute("UPDATE orders SET status=? WHERE id=?", (status, request.form.get("id")))
    flash("Order status updated.", "success")
    return redirect(url_for("admin_dashboard") + "#orders")

@app.post("/admin/appointment/status")
@admin_required
def appointment_status():
    status = request.form.get("status", "")
    if status not in ["Pending", "Confirmed", "Completed", "Cancelled"]:
        abort(400)
    with db() as conn:
        conn.execute("UPDATE appointments SET status=? WHERE id=?", (status, request.form.get("id")))
    flash("Appointment status updated.", "success")
    return redirect(url_for("admin_dashboard") + "#appointments")

@app.route("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
