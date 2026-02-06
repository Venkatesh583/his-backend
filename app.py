from flask import Flask, render_template, request, redirect, send_file, jsonify
import sqlite3
import os
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

app = Flask(__name__)
app.secret_key = "his_secret_key"

# ================= DATABASE =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "his.db")

def get_db():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            age INTEGER,
            scheme TEXT,
            income INTEGER,
            children INTEGER,
            pregnant TEXT,
            status TEXT,
            notice TEXT
        )
    """)
    
    cur.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin','admin123','ADMIN')")
    cur.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('caseworker','1234','CASEWORKER')")
    
    conn.commit()
    conn.close()

# ================= PANEL 1: PUBLIC SITE =================
@app.route("/")
def public_home():
    return render_template("public-home.html")

@app.route("/public/register")
def public_register():
    return render_template("application-create.html")

@app.route("/public/check-status")
def check_status():
    return "Status check page (to be implemented)"

# ================= PANEL 2: ADMIN PANEL =================
@app.route("/admin")
def admin_home():
    return redirect("/admin/dashboard")

@app.route("/admin/dashboard")
def admin_dashboard():
    return render_template("admin-dashboard.html")

@app.route("/admin/users")
def admin_users():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()
    conn.close()
    return str(users)

# ================= PANEL 3: CASEWORKER PANEL =================
@app.route("/caseworker")
def caseworker_home():
    return redirect("/caseworker/dashboard")

@app.route("/caseworker/dashboard")
def caseworker_dashboard():
    return render_template("dashboard.html")

@app.route("/caseworker/applications")
def caseworker_applications():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM applications")
    data = cur.fetchall()
    conn.close()
    return render_template("application-list.html", applications=data)

# ================= PANEL 4: APPLICATION SYSTEM =================
@app.route("/applications")
def all_applications():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM applications")
    data = cur.fetchall()
    conn.close()
    return render_template("application-list.html", applications=data)

@app.route("/create-application", methods=["GET","POST"])
def create_application():
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO applications (full_name, age, scheme, income, children, pregnant, status)
            VALUES (?, ?, ?, ?, ?, ?, 'PENDING')
        """, (
            request.form["full_name"],
            int(request.form["age"]),
            request.form["scheme"],
            int(request.form["income"]),
            int(request.form.get("children",0)),
            request.form.get("pregnant","NO")
        ))
        conn.commit()
        conn.close()
        return redirect("/applications")
    return render_template("application-create.html")

@app.route("/eligibility/<int:app_id>")
def eligibility(app_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT full_name, age, income, scheme, children FROM applications WHERE id=?", (app_id,))
    row = cur.fetchone()
    
    if not row:
        return "Application not found"
    
    full_name, age, income, scheme, children = row
    
    if scheme == "SNAP" and income <= 200000:
        status, notice = "ELIGIBLE", f"Dear {full_name}, SNAP approved."
    elif scheme == "CCAP" and income <= 300000 and children > 0:
        status, notice = "ELIGIBLE", f"Dear {full_name}, CCAP approved."
    elif scheme == "Medicaid" and income <= 250000:
        status, notice = "ELIGIBLE", f"Dear {full_name}, Medicaid approved."
    elif scheme == "Medicare" and age >= 65:
        status, notice = "ELIGIBLE", f"Dear {full_name}, Medicare approved."
    elif scheme == "QHP":
        status, notice = "PURCHASE REQUIRED", f"Dear {full_name}, purchase QHP."
    else:
        status, notice = "DENIED", f"Dear {full_name}, application denied."
    
    cur.execute("UPDATE applications SET status=?, notice=? WHERE id=?", (status, notice, app_id))
    conn.commit()
    conn.close()
    return redirect(f"/notice/{app_id}")

@app.route("/notice/<int:app_id>")
def view_notice(app_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT full_name, scheme, status, notice FROM applications WHERE id=?", (app_id,))
    data = cur.fetchone()
    conn.close()
    
    if not data:
        return "Notice not found"
    
    return render_template("notice.html",
        full_name=data[0],
        scheme=data[1],
        status=data[2],
        notice=data[3]
    )

@app.route("/download-notice/<int:app_id>")
def download_notice(app_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT full_name, scheme, status, notice FROM applications WHERE id=?", (app_id,))
    data = cur.fetchone()
    conn.close()
    
    if not data:
        return "Application not found"
    
    full_name, scheme, status, notice = data
    if not notice:
        notice = "No official notice generated yet."
    
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(300, 800, "Government of India")
    pdf.drawCentredString(300, 780, "Health Insurance Scheme Notice")
    
    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, 730, f"Applicant: {full_name}")
    pdf.drawString(50, 710, f"Scheme: {scheme}")
    pdf.drawString(50, 690, f"Status: {status}")
    
    text = pdf.beginText(50, 650)
    for line in notice.split("."):
        if line.strip():
            text.textLine(line.strip())
    pdf.drawText(text)
    
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True,
                     download_name=f"Notice_{app_id}.pdf",
                     mimetype="application/pdf")

# ================= SYSTEM ROUTES =================
@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "HIS Backend"}), 200

@app.route("/api/health")
def api_health():
    return jsonify({"status": "healthy", "api": "operational"}), 200

@app.route("/test")
def test():
    return "Test route is working!"

@app.route("/debug-db")
def debug_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM applications")
    data = cur.fetchall()
    conn.close()
    return str(data)

# ================= LOGIN/LOGOUT =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        # Hardcoded for testing
        if username == "caseworker" and password == "1234":
            return redirect("/caseworker/dashboard")
        if username == "admin" and password == "admin123":
            return redirect("/admin/dashboard")
        
        # Database check
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT role FROM users WHERE username=? AND password=?", (username,password))
        user = cur.fetchone()
        conn.close()
        
        if user:
            return redirect("/caseworker/dashboard" if user[0] == "CASEWORKER" else "/admin/dashboard")
        return "Invalid Credentials"
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    return redirect("/")

# ================= INIT + RUN =================
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)

    # Add to your existing app.py (around line 60)

@app.route("/admin/dashboard")
def admin_dashboard():
    return render_template("admin-dashboard.html")

@app.route("/caseworker/dashboard")
def caseworker_dashboard():
    return render_template("dashboard.html")

@app.route("/public/register")
def public_register():
    return render_template("application-create.html")