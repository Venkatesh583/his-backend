<<<<<<< HEAD
from flask import Flask, render_template, request, redirect
import sqlite3
import os
=======
from flask import Flask, render_template, request, redirect, send_file
import sqlite3
import os
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
>>>>>>> 613e80f (Initial Flask HIS backend)

app = Flask(__name__)
app.secret_key = "his_secret_key"

# ================= DATABASE CONFIG =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "his.db")

<<<<<<< HEAD

def get_db():
    return sqlite3.connect(DB_NAME)


=======
def get_db():
    return sqlite3.connect(DB_NAME)

>>>>>>> 613e80f (Initial Flask HIS backend)
# ================= INIT TABLES =================
def init_db():
    conn = get_db()
    cur = conn.cursor()

<<<<<<< HEAD
    # USERS TABLE
=======
>>>>>>> 613e80f (Initial Flask HIS backend)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)

<<<<<<< HEAD
    # APPLICATIONS TABLE
=======
>>>>>>> 613e80f (Initial Flask HIS backend)
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

<<<<<<< HEAD
    # DEFAULT USERS
=======
>>>>>>> 613e80f (Initial Flask HIS backend)
    cur.execute("""
        INSERT OR IGNORE INTO users (username, password, role)
        VALUES ('caseworker', '1234', 'CASEWORKER')
    """)
    cur.execute("""
        INSERT OR IGNORE INTO users (username, password, role)
        VALUES ('admin', 'admin123', 'ADMIN')
    """)

    conn.commit()
    conn.close()

<<<<<<< HEAD



=======
>>>>>>> 613e80f (Initial Flask HIS backend)
# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT role FROM users WHERE username=? AND password=?",
            (username, password)
        )
        user = cur.fetchone()
        conn.close()

        if user:
<<<<<<< HEAD
            if user[0] == "CASEWORKER":
                return redirect("/dashboard")
            else:
                return redirect("/admin-dashboard")
        else:
            return "Invalid Credentials"

    return render_template("login.html")


=======
            return redirect("/dashboard" if user[0] == "CASEWORKER" else "/admin-dashboard")
        return "Invalid Credentials"

    return render_template("login.html")

>>>>>>> 613e80f (Initial Flask HIS backend)
# ================= DASHBOARDS =================
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

<<<<<<< HEAD

=======
>>>>>>> 613e80f (Initial Flask HIS backend)
@app.route("/admin-dashboard")
def admin_dashboard():
    return render_template("admin-dashboard.html")

<<<<<<< HEAD

# ================= APPLICATION REGISTRATION (AR) =================
@app.route("/create-application", methods=["GET", "POST"])
def create_application():
    if request.method == "POST":
        full_name = request.form["full_name"]
        age = int(request.form["age"])
        scheme = request.form["scheme"]
        income = int(request.form["income"])
        children = int(request.form.get("children", 0))
        pregnant = request.form.get("pregnant", "NO")

        status = "AR_COMPLETED"
=======
# ================= APPLICATION CREATE =================
@app.route("/create-application", methods=["GET", "POST"])
def create_application():
    if request.method == "POST":
        data = (
            request.form["full_name"],
            int(request.form["age"]),
            request.form["scheme"],
            int(request.form["income"]),
            int(request.form.get("children", 0)),
            request.form.get("pregnant", "NO"),
            "AR_COMPLETED"
        )
>>>>>>> 613e80f (Initial Flask HIS backend)

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO applications
            (full_name, age, scheme, income, children, pregnant, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
<<<<<<< HEAD
        """, (full_name, age, scheme, income, children, pregnant, status))
=======
        """, data)
>>>>>>> 613e80f (Initial Flask HIS backend)
        conn.commit()
        conn.close()

        return redirect("/application-list")

    return render_template("application-create.html")

<<<<<<< HEAD

=======
>>>>>>> 613e80f (Initial Flask HIS backend)
# ================= APPLICATION LIST =================
@app.route("/application-list")
def application_list():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM applications")
<<<<<<< HEAD
    data = cur.fetchall()
    conn.close()
    return render_template("application-list.html", applications=data)


# ================= DATA COLLECTION (DC) =================
@app.route("/data-collection/<int:app_id>", methods=["GET", "POST"])
def data_collection(app_id):
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        income = int(request.form["income"])
        children = int(request.form["children"])
        pregnant = request.form.get("pregnant", "NO")

        cur.execute("""
            UPDATE applications
            SET income=?, children=?, pregnant=?, status='DC_COMPLETED'
            WHERE id=?
        """, (income, children, pregnant, app_id))

        conn.commit()
        conn.close()
        return redirect(f"/eligibility/{app_id}")

    cur.execute("SELECT * FROM applications WHERE id=?", (app_id,))
    app_data = cur.fetchone()
    conn.close()

    return render_template("data-collection.html", app=app_data)


# ================= ELIGIBILITY DETERMINATION (ED) =================
@app.route("/eligibility/<int:app_id>")
def eligibility(app_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT full_name, age, income, scheme, children
        FROM applications WHERE id=?
    """, (app_id,))

    row = cur.fetchone()

    if row is None:
        conn.close()
        return "Application not found"

    full_name, age, income, scheme, children = row

    # ================= RULE ENGINE =================
    if scheme == "SNAP" and income <= 200000:
        status = "ELIGIBLE"
        notice = (
            f"Dear {full_name}, "
            f"your application for SNAP has been approved. "
            f"You are eligible to receive benefits as per program guidelines."
        )

    elif scheme == "CCAP" and income <= 300000 and children > 0:
        status = "ELIGIBLE"
        notice = (
            f"Dear {full_name}, "
            f"your CCAP application is approved. "
            f"Child care assistance benefits will be provided."
        )

    elif scheme == "Medicaid" and income <= 250000:
        status = "ELIGIBLE"
        notice = (
            f"Dear {full_name}, "
            f"you are approved for Medicaid health coverage."
        )

    elif scheme == "Medicare" and age >= 65:
        status = "ELIGIBLE"
        notice = (
            f"Dear {full_name}, "
            f"you qualify for Medicare benefits due to age eligibility."
        )

    elif scheme == "QHP":
        status = "PURCHASE REQUIRED"
        notice = (
            f"Dear {full_name}, "
            f"you are not eligible for free coverage. "
            f"You may purchase a Qualified Health Plan."
        )

    else:
        status = "DENIED"
        notice = (
            f"Dear {full_name}, "
            f"after review, you are not eligible for {scheme} benefits."
        )

    # ================= SAVE DECISION + NOTICE =================
    cur.execute("""
        UPDATE applications
        SET status=?, notice=?
        WHERE id=?
    """, (status, notice, app_id))

    conn.commit()
    conn.close()

    return redirect(f"/notice/{app_id}")



# ================= VIEW NOTICE =================
@app.route("/notice/<int:app_id>")
def view_notice(app_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT full_name, scheme, status, notice
        FROM applications WHERE id=?
    """, (app_id,))

    data = cur.fetchone()
    conn.close()

    return render_template(
        "notice.html",
        full_name=data[0],
        scheme=data[1],
        status=data[2],
        notice=data[3]
    )

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from flask import send_file
import io

# ================= DOWNLOAD NOTICE PDF =================
=======
    apps = cur.fetchall()
    conn.close()
    return render_template("application-list.html", applications=apps)

# ================= NOTICE PDF =================
>>>>>>> 613e80f (Initial Flask HIS backend)
@app.route("/download-notice/<int:app_id>")
def download_notice(app_id):
    conn = get_db()
    cur = conn.cursor()
<<<<<<< HEAD

    cur.execute("""
        SELECT full_name, scheme, status, notice
        FROM applications WHERE id=?
    """, (app_id,))
    data = cur.fetchone()
    conn.close()

    # SAFETY CHECK
    if data is None:
        return "Application not found"

    full_name, scheme, status, notice = data

    if notice is None:
        notice = "No official notice has been generated for this application yet."

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    # HEADER
=======
    cur.execute("SELECT full_name, scheme, status, notice FROM applications WHERE id=?", (app_id,))
    data = cur.fetchone()
    conn.close()

    if not data:
        return "Application not found"

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

>>>>>>> 613e80f (Initial Flask HIS backend)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(300, 800, "Government of India")
    pdf.drawCentredString(300, 780, "Health Insurance Scheme Notice")

<<<<<<< HEAD
    # BASIC DETAILS
    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, 730, f"Applicant Name : {full_name}")
    pdf.drawString(50, 710, f"Scheme         : {scheme}")
    pdf.drawString(50, 690, f"Status         : {status}")

    pdf.line(50, 670, 550, 670)

    # NOTICE BODY
    text = pdf.beginText(50, 640)
    text.textLine("Official Notice:")
    text.textLine("")

    for line in notice.split("."):
        if line.strip():
            text.textLine(line.strip())

    pdf.drawText(text)

    # FOOTER
    pdf.drawString(50, 120, "Authorized Officer")
    pdf.drawString(50, 100, "Health & Welfare Department")

    pdf.showPage()
    pdf.save()

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Notice_{app_id}.pdf",
        mimetype="application/pdf"
    )



# ================= DEBUG =================
@app.route("/debug-db")
def debug_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM applications")
    data = cur.fetchall()
    conn.close()
    return str(data)

=======
    pdf.setFont("Helvetica", 11)
    y = 730
    for label, value in zip(["Name", "Scheme", "Status"], data[:3]):
        pdf.drawString(50, y, f"{label}: {value}")
        y -= 20

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="notice.pdf")
>>>>>>> 613e80f (Initial Flask HIS backend)

# ================= RUN =================
if __name__ == "__main__":
    init_db()
<<<<<<< HEAD
    app.run(debug=True)
=======
    app.run(host="0.0.0.0", port=5000)
>>>>>>> 613e80f (Initial Flask HIS backend)
