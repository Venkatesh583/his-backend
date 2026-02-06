from flask import Flask, render_template, request, redirect, send_file, jsonify, session, flash
import sqlite3
import os
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

app = Flask(__name__)
app.secret_key = "health_insurance_system_2025"
app.config['SESSION_TYPE'] = 'filesystem'

# ================= DATABASE CONFIG =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "health_insurance.db")

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Return dictionaries
    return conn

def init_tables():
    """Create all tables from your design"""
    conn = get_db()
    cur = conn.cursor()
    
    # Table-1: PLAN_CATEGORY
    cur.execute('''
        CREATE TABLE IF NOT EXISTS plan_category (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name VARCHAR(100) NOT NULL,
            active_sw CHAR(1) DEFAULT 'Y',
            create_date DATE DEFAULT CURRENT_DATE,
            update_date DATE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50)
        )
    ''')
    
    # Table-2: PLAN_MASTER
    cur.execute('''
        CREATE TABLE IF NOT EXISTS plan_master (
            plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_name VARCHAR(100) NOT NULL,
            plan_start_date DATE,
            plan_end_date DATE,
            plan_category_id INTEGER,
            active_sw CHAR(1) DEFAULT 'Y',
            create_date DATE DEFAULT CURRENT_DATE,
            update_date DATE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            FOREIGN KEY (plan_category_id) REFERENCES plan_category(category_id)
        )
    ''')
    
    # Table-3: CASE_WORKER_ACCTS
    cur.execute('''
        CREATE TABLE IF NOT EXISTS case_worker_accts (
            acc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE,
            pwd VARCHAR(100),
            phno VARCHAR(15),
            gender CHAR(1),
            ssn VARCHAR(20) UNIQUE,
            dob DATE,
            active_sw CHAR(1) DEFAULT 'Y',
            create_date DATE DEFAULT CURRENT_DATE,
            update_date DATE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50)
        )
    ''')
    
    # Table-4: CITIZEN_APPS
    cur.execute('''
        CREATE TABLE IF NOT EXISTS citizen_apps (
            app_id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname VARCHAR(100) NOT NULL,
            email VARCHAR(100),
            phno VARCHAR(15),
            ssn VARCHAR(20) UNIQUE,
            gender CHAR(1),
            state_name VARCHAR(50),
            create_date DATE DEFAULT CURRENT_DATE,
            update_date DATE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50)
        )
    ''')
    
    # Table-5: DC_CASES
    cur.execute('''
        CREATE TABLE IF NOT EXISTS dc_cases (
            case_id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_num INTEGER UNIQUE,
            app_id INTEGER,
            plan_id INTEGER,
            FOREIGN KEY (app_id) REFERENCES citizen_apps(app_id),
            FOREIGN KEY (plan_id) REFERENCES plan_master(plan_id)
        )
    ''')
    
    # Table-6: DC_INCOME
    cur.execute('''
        CREATE TABLE IF NOT EXISTS dc_income (
            income_id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_num INTEGER,
            emp_income DECIMAL(10,2),
            property_income DECIMAL(10,2),
            FOREIGN KEY (case_num) REFERENCES dc_cases(case_num)
        )
    ''')
    
    # Table-7: DC_CHILDRENS
    cur.execute('''
        CREATE TABLE IF NOT EXISTS dc_childrens (
            children_id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_num INTEGER,
            children_dob DATE,
            children_ssn VARCHAR(20),
            FOREIGN KEY (case_num) REFERENCES dc_cases(case_num)
        )
    ''')
    
    # Table-8: DC_EDUCATION
    cur.execute('''
        CREATE TABLE IF NOT EXISTS dc_education (
            edu_id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_num INTEGER,
            highest_qualification VARCHAR(100),
            graduation_year INTEGER,
            FOREIGN KEY (case_num) REFERENCES dc_cases(case_num)
        )
    ''')
    
    # Table-9: ELIG_DTLS
    cur.execute('''
        CREATE TABLE IF NOT EXISTS elig_dtls (
            elig_id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_num INTEGER,
            plan_name VARCHAR(100),
            plan_status VARCHAR(50),
            plan_start_date DATE,
            plan_end_date DATE,
            benefit_amt DECIMAL(10,2),
            denial_reason TEXT,
            FOREIGN KEY (case_num) REFERENCES dc_cases(case_num)
        )
    ''')
    
    # Table-10: CO_TRIGGERS
    cur.execute('''
        CREATE TABLE IF NOT EXISTS co_triggers (
            trg_id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_num INTEGER,
            trg_status CHAR(1),
            notice TEXT,
            FOREIGN KEY (case_num) REFERENCES dc_cases(case_num)
        )
    ''')
    
    # Insert sample data
    # Default admin account
    cur.execute('''
        INSERT OR IGNORE INTO case_worker_accts 
        (fullname, email, pwd, phno, gender, ssn, dob, created_by)
        VALUES ('System Admin', 'admin@his.gov', 'admin123', '9876543210', 'M', '987654', '1990-01-01', 'SYSTEM')
    ''')
    
    # Sample plan categories
    categories = [
        ('SNAP', 'Y', 'SYSTEM'),
        ('CCAP', 'Y', 'SYSTEM'),
        ('Medicaid', 'Y', 'SYSTEM'),
        ('Medicare', 'Y', 'SYSTEM'),
        ('QHP', 'Y', 'SYSTEM')
    ]
    
    for cat_name, active, creator in categories:
        cur.execute('''
            INSERT OR IGNORE INTO plan_category (category_name, active_sw, created_by)
            VALUES (?, ?, ?)
        ''', (cat_name, active, creator))
    
    conn.commit()
    conn.close()
    print("[SUCCESS] All tables created with sample data")

# ================= AUTHENTICATION =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT * FROM case_worker_accts WHERE email = ? AND pwd = ?', 
                   (email, password))
        user = cur.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['acc_id']
            session['user_name'] = user['fullname']
            session['user_email'] = user['email']
            session['user_role'] = 'ADMIN' if user['email'] == 'admin@his.gov' else 'CASEWORKER'
            
            if session['user_role'] == 'ADMIN':
                return redirect('/admin/dashboard')
            else:
                return redirect('/caseworker/dashboard')
        else:
            flash('Invalid credentials!', 'danger')
    
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ================= ADMIN MODULE =================
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_role' not in session or session['user_role'] != 'ADMIN':
        return redirect('/login')
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get statistics
    cur.execute('SELECT COUNT(*) FROM case_worker_accts')
    total_workers = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM citizen_apps')
    total_applications = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM elig_dtls WHERE plan_status = "APPROVED"')
    approved = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM elig_dtls WHERE plan_status = "DENIED"')
    denied = cur.fetchone()[0]
    
    conn.close()
    
    return render_template('admin/dashboard.html',
                         total_workers=total_workers,
                         total_applications=total_applications,
                         approved=approved,
                         denied=denied)

@app.route('/admin/plan-category', methods=['GET', 'POST'])
def plan_category():
    if 'user_role' not in session or session['user_role'] != 'ADMIN':
        return redirect('/login')
    
    conn = get_db()
    cur = conn.cursor()
    
    if request.method == 'POST':
        category_name = request.form['category_name']
        active_sw = request.form.get('active_sw', 'Y')
        
        cur.execute('''
            INSERT INTO plan_category (category_name, active_sw, created_by, create_date)
            VALUES (?, ?, ?, DATE('now'))
        ''', (category_name, active_sw, session['user_name']))
        conn.commit()
        flash('Plan category added successfully!', 'success')
    
    cur.execute('SELECT * FROM plan_category ORDER BY create_date DESC')
    categories = cur.fetchall()
    conn.close()
    
    return render_template('admin/plan-category.html', categories=categories)

@app.route('/admin/plan-master', methods=['GET', 'POST'])
def plan_master():
    if 'user_role' not in session or session['user_role'] != 'ADMIN':
        return redirect('/login')
    
    conn = get_db()
    cur = conn.cursor()
    
    if request.method == 'POST':
        plan_name = request.form['plan_name']
        plan_start_date = request.form['plan_start_date']
        plan_end_date = request.form['plan_end_date']
        plan_category_id = request.form['plan_category_id']
        
        cur.execute('''
            INSERT INTO plan_master (plan_name, plan_start_date, plan_end_date, 
                                   plan_category_id, created_by, create_date)
            VALUES (?, ?, ?, ?, ?, DATE('now'))
        ''', (plan_name, plan_start_date, plan_end_date, plan_category_id, session['user_name']))
        conn.commit()
        flash('Plan added successfully!', 'success')
    
    # Get plans with category names
    cur.execute('''
        SELECT p.*, c.category_name 
        FROM plan_master p 
        LEFT JOIN plan_category c ON p.plan_category_id = c.category_id
        ORDER BY p.create_date DESC
    ''')
    plans = cur.fetchall()
    
    # Get categories for dropdown
    cur.execute('SELECT category_id, category_name FROM plan_category WHERE active_sw = "Y"')
    categories = cur.fetchall()
    
    conn.close()
    
    return render_template('admin/plan-master.html', plans=plans, categories=categories)

@app.route('/admin/caseworkers')
def admin_caseworkers():
    if 'user_role' not in session or session['user_role'] != 'ADMIN':
        return redirect('/login')
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM case_worker_accts ORDER BY create_date DESC')
    workers = cur.fetchall()
    conn.close()
    
    return render_template('admin/caseworkers.html', workers=workers)

# ================= APPLICATION REGISTRATION =================
@app.route('/public/register', methods=['GET', 'POST'])
def citizen_registration():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        phno = request.form['phno']
        ssn = request.form['ssn']
        gender = request.form['gender']
        state_name = request.form['state_name']
        
        conn = get_db()
        cur = conn.cursor()
        
        try:
            cur.execute('''
                INSERT INTO citizen_apps (fullname, email, phno, ssn, gender, state_name, create_date)
                VALUES (?, ?, ?, ?, ?, ?, DATE('now'))
            ''', (fullname, email, phno, ssn, gender, state_name))
            
            app_id = cur.lastrowid
            
            # Create a case number
            case_num = 10000 + app_id
            
            cur.execute('''
                INSERT INTO dc_cases (case_num, app_id, plan_id)
                VALUES (?, ?, (SELECT plan_id FROM plan_master WHERE active_sw = "Y" LIMIT 1))
            ''', (case_num, app_id))
            
            conn.commit()
            flash(f'Application submitted successfully! Your Case Number: {case_num}', 'success')
            return redirect(f'/application/{case_num}/data-collection')
            
        except sqlite3.IntegrityError:
            flash('SSN already registered!', 'danger')
        finally:
            conn.close()
    
    return render_template('public/register.html')

@app.route('/application/<int:case_num>/data-collection', methods=['GET', 'POST'])
def data_collection(case_num):
    if request.method == 'POST':
        emp_income = request.form.get('emp_income', 0)
        property_income = request.form.get('property_income', 0)
        highest_qualification = request.form.get('highest_qualification', '')
        graduation_year = request.form.get('graduation_year', '')
        
        conn = get_db()
        cur = conn.cursor()
        
        # Insert income data
        cur.execute('''
            INSERT INTO dc_income (case_num, emp_income, property_income)
            VALUES (?, ?, ?)
        ''', (case_num, emp_income, property_income))
        
        # Insert education data
        if highest_qualification:
            cur.execute('''
                INSERT INTO dc_education (case_num, highest_qualification, graduation_year)
                VALUES (?, ?, ?)
            ''', (case_num, highest_qualification, graduation_year))
        
        conn.commit()
        conn.close()
        
        flash('Data collected successfully!', 'success')
        return redirect(f'/application/{case_num}/eligibility')
    
    return render_template('public/data-collection.html', case_num=case_num)

# ================= ELIGIBILITY DETERMINATION =================
@app.route('/application/<int:case_num>/eligibility')
def check_eligibility(case_num):
    conn = get_db()
    cur = conn.cursor()
    
    # Get application and income data
    cur.execute('''
        SELECT ca.*, di.emp_income, di.property_income, p.plan_name
        FROM citizen_apps ca
        JOIN dc_cases dc ON ca.app_id = dc.app_id
        LEFT JOIN dc_income di ON dc.case_num = di.case_num
        LEFT JOIN plan_master p ON dc.plan_id = p.plan_id
        WHERE dc.case_num = ?
    ''', (case_num,))
    
    data = cur.fetchone()
    
    if not data:
        conn.close()
        return "Case not found"
    
    # Eligibility logic based on state and income
    total_income = (data['emp_income'] or 0) + (data['property_income'] or 0)
    state = data['state_name']
    plan_name = data['plan_name']
    
    # Simple eligibility rules
    if plan_name == 'SNAP' and total_income <= 200000:
        plan_status = 'APPROVED'
        benefit_amt = 5000
        denial_reason = None
    elif plan_name == 'CCAP' and total_income <= 300000:
        plan_status = 'APPROVED'
        benefit_amt = 8000
        denial_reason = None
    elif plan_name == 'Medicaid' and total_income <= 250000:
        plan_status = 'APPROVED'
        benefit_amt = 10000
        denial_reason = None
    else:
        plan_status = 'DENIED'
        benefit_amt = 0
        denial_reason = f"Income exceeds limit for {plan_name}"
    
    # Save eligibility determination
    cur.execute('''
        INSERT INTO elig_dtls (case_num, plan_name, plan_status, plan_start_date, 
                              plan_end_date, benefit_amt, denial_reason)
        VALUES (?, ?, ?, DATE('now'), DATE('now', '+1 year'), ?, ?)
    ''', (case_num, plan_name, plan_status, benefit_amt, denial_reason))
    
    # Create correspondence trigger
    notice = f"Dear {data['fullname']}, your application for {plan_name} has been {plan_status.lower()}."
    
    cur.execute('''
        INSERT INTO co_triggers (case_num, trg_status, notice)
        VALUES (?, 'P', ?)
    ''', (case_num, notice))
    
    conn.commit()
    conn.close()
    
    return render_template('public/eligibility-result.html',
                         case_num=case_num,
                         fullname=data['fullname'],
                         plan_name=plan_name,
                         plan_status=plan_status,
                         benefit_amt=benefit_amt,
                         denial_reason=denial_reason,
                         notice=notice)

# ================= CASEWORKER MODULE =================
@app.route('/caseworker/dashboard')
def caseworker_dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get assigned cases
    cur.execute('''
        SELECT COUNT(*) FROM dc_cases WHERE case_id IN 
        (SELECT case_id FROM elig_dtls WHERE plan_status = 'PENDING')
    ''')
    pending_cases = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM citizen_apps WHERE DATE(create_date) = DATE("now")')
    today_applications = cur.fetchone()[0]
    
    cur.execute('''
        SELECT COUNT(*) FROM elig_dtls 
        WHERE DATE(plan_start_date) = DATE("now") AND plan_status = 'APPROVED'
    ''')
    today_approved = cur.fetchone()[0]
    
    conn.close()
    
    return render_template('caseworker/dashboard.html',
                         pending_cases=pending_cases,
                         today_applications=today_applications,
                         today_approved=today_approved)

@app.route('/caseworker/applications')
def caseworker_applications():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT ca.*, dc.case_num, e.plan_status, e.benefit_amt
        FROM citizen_apps ca
        JOIN dc_cases dc ON ca.app_id = dc.app_id
        LEFT JOIN elig_dtls e ON dc.case_num = e.case_num
        ORDER BY ca.create_date DESC
    ''')
    
    applications = cur.fetchall()
    conn.close()
    
    return render_template('caseworker/applications.html', applications=applications)

# ================= CORRESPONDENCE MODULE =================
@app.route('/notice/<int:case_num>/download')
def download_notice(case_num):
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT ca.fullname, e.plan_name, e.plan_status, e.benefit_amt, e.denial_reason, ct.notice
        FROM citizen_apps ca
        JOIN dc_cases dc ON ca.app_id = dc.app_id
        JOIN elig_dtls e ON dc.case_num = e.case_num
        JOIN co_triggers ct ON dc.case_num = ct.case_num
        WHERE dc.case_num = ?
    ''', (case_num,))
    
    data = cur.fetchone()
    conn.close()
    
    if not data:
        return "Notice not found"
    
    # Create PDF
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    
    # Header
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawCentredString(300, 800, "Government of India")
    pdf.drawCentredString(300, 780, "Health Insurance Scheme")
    pdf.drawCentredString(300, 760, "OFFICIAL NOTICE")
    
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, 740, f"Notice ID: HIS-NOTICE-{case_num}")
    pdf.drawString(50, 725, f"Date: {datetime.now().strftime('%d/%m/%Y')}")
    
    pdf.line(50, 715, 550, 715)
    
    # Applicant Details
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 690, "Applicant Information:")
    
    pdf.setFont("Helvetica", 11)
    details = [
        f"Name: {data['fullname']}",
        f"Case Number: {case_num}",
        f"Plan: {data['plan_name']}",
        f"Status: {data['plan_status']}",
        f"Benefit Amount: ₹{data['benefit_amt']:,}" if data['benefit_amt'] else "Benefit Amount: N/A"
    ]
    
    y = 665
    for detail in details:
        pdf.drawString(70, y, detail)
        y -= 20
    
    # Notice Content
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y-30, "Official Notice:")
    
    pdf.setFont("Helvetica", 11)
    notice_lines = data['notice'].split('. ')
    y = y-60
    for line in notice_lines:
        if line.strip():
            pdf.drawString(70, y, line.strip() + ".")
            y -= 20
    
    # Footer
    pdf.setFont("Helvetica", 9)
    pdf.drawString(50, 100, "This is an official document issued by the Health Insurance Scheme System.")
    pdf.drawString(50, 85, "For verification contact: verify@his.gov.in")
    
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True,
                    download_name=f"HIS_Notice_{case_num}.pdf",
                    mimetype="application/pdf")

# ================= API ENDPOINTS =================
@app.route('/api/health')
def api_health():
    return jsonify({"status": "healthy", "service": "Health Insurance System"}), 200

@app.route('/api/stats')
def api_stats():
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute('SELECT COUNT(*) FROM citizen_apps')
    total_apps = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM elig_dtls WHERE plan_status = "APPROVED"')
    approved = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM case_worker_accts')
    workers = cur.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        "total_applications": total_apps,
        "approved_applications": approved,
        "case_workers": workers,
        "timestamp": datetime.now().isoformat()
    })

# ================= PUBLIC PAGES =================
@app.route('/')
def home():
    return render_template('public/home.html')

@app.route('/check-status')
def check_status():
    return render_template('public/check-status.html')

# ================= INITIALIZATION =================
with app.app_context():
    init_tables()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)