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
DB_NAME = os.path.join(BASE_DIR, "his.db")

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_tables():
    """Create all tables from your project description"""
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
            updated_by VARCHAR(50)
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
    
    # Insert default data
    cur.execute('''
        INSERT OR IGNORE INTO case_worker_accts 
        (fullname, email, pwd, phno, gender, ssn, dob, created_by)
        VALUES 
        ('Admin User', 'admin@his.gov', 'admin123', '9876543210', 'M', '987654', '1990-01-01', 'SYSTEM'),
        ('Case Worker 1', 'worker1@his.gov', 'worker123', '9876543211', 'F', '001003', '1992-05-15', 'SYSTEM')
    ''')
    
    # Insert plan categories
    categories = ['SNAP', 'CCAP', 'Medicaid', 'Medicare', 'QHP']
    for cat in categories:
        cur.execute('''
            INSERT OR IGNORE INTO plan_category (category_name, created_by)
            VALUES (?, 'SYSTEM')
        ''', (cat,))
    
    conn.commit()
    conn.close()
    print("✅ Database initialized with all tables")

# ================= PUBLIC ROUTES =================
@app.route('/')
def home():
    """Public landing page"""
    return render_template('public/home.html')

@app.route('/public/register', methods=['GET', 'POST'])
def citizen_register():
    if request.method == 'POST':
        conn = get_db()
        cur = conn.cursor()
        
        try:
            cur.execute('''
                INSERT INTO citizen_apps 
                (fullname, email, phno, ssn, gender, state_name, create_date)
                VALUES (?, ?, ?, ?, ?, ?, DATE('now'))
            ''', (
                request.form['fullname'],
                request.form.get('email', ''),
                request.form.get('phno', ''),
                request.form['ssn'],
                request.form.get('gender', ''),
                request.form.get('state_name', 'New York')
            ))
            
            app_id = cur.lastrowid
            conn.commit()
            flash(f'✅ Application submitted! Your Application ID: {app_id}', 'success')
            return redirect(f'/application/{app_id}/status')
            
        except sqlite3.IntegrityError:
            flash('❌ SSN already registered!', 'danger')
        finally:
            conn.close()
    
    return render_template('public/register.html')

@app.route('/application/<int:app_id>/status')
def application_status(app_id):
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute('SELECT * FROM citizen_apps WHERE app_id = ?', (app_id,))
    application = cur.fetchone()
    
    if not application:
        conn.close()
        return "Application not found"
    
    conn.close()
    return render_template('public/status.html', application=application)

@app.route('/check-status')
def check_status_page():
    return render_template('public/check-status.html')

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
    return redirect('/')

# ================= ADMIN MODULE =================
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_role' not in session or session['user_role'] != 'ADMIN':
        return redirect('/login')
    
    conn = get_db()
    cur = conn.cursor()
    
    # Statistics
    cur.execute('SELECT COUNT(*) FROM citizen_apps')
    total_apps = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM case_worker_accts')
    total_workers = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM plan_category')
    total_categories = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM plan_master')
    total_plans = cur.fetchone()[0]
    
    conn.close()
    
    return render_template('admin/dashboard.html',
                         total_apps=total_apps,
                         total_workers=total_workers,
                         total_categories=total_categories,
                         total_plans=total_plans)

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
        flash('✅ Plan category added successfully!', 'success')
        return redirect('/admin/plan-category')
    
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
        cur.execute('''
            INSERT INTO plan_master 
            (plan_name, plan_start_date, plan_end_date, plan_category_id, created_by, create_date)
            VALUES (?, ?, ?, ?, ?, DATE('now'))
        ''', (
            request.form['plan_name'],
            request.form['plan_start_date'],
            request.form['plan_end_date'],
            request.form['plan_category_id'],
            session['user_name']
        ))
        conn.commit()
        flash('✅ Plan added successfully!', 'success')
        return redirect('/admin/plan-master')
    
    # Get all plans
    cur.execute('''
        SELECT pm.*, pc.category_name 
        FROM plan_master pm
        LEFT JOIN plan_category pc ON pm.plan_category_id = pc.category_id
        ORDER BY pm.create_date DESC
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

# ================= CASEWORKER MODULE =================
@app.route('/caseworker/dashboard')
def caseworker_dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get statistics
    cur.execute('SELECT COUNT(*) FROM citizen_apps')
    total_apps = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM citizen_apps WHERE DATE(create_date) = DATE("now")')
    today_apps = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM citizen_apps WHERE state_name = "New York"')
    ny_apps = cur.fetchone()[0]
    
    conn.close()
    
    return render_template('caseworker/dashboard.html',
                         total_apps=total_apps,
                         today_apps=today_apps,
                         ny_apps=ny_apps)

@app.route('/caseworker/applications')
def caseworker_applications():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM citizen_apps ORDER BY create_date DESC')
    applications = cur.fetchall()
    conn.close()
    
    return render_template('caseworker/applications.html', applications=applications)

# ================= DATA COLLECTION MODULE =================
@app.route('/data-collection/<int:app_id>', methods=['GET', 'POST'])
def data_collection(app_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        # In real app, you would save to dc_cases, dc_income, dc_childrens, dc_education tables
        flash('✅ Data collected successfully!', 'success')
        return redirect(f'/eligibility/{app_id}')
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM citizen_apps WHERE app_id = ?', (app_id,))
    application = cur.fetchone()
    conn.close()
    
    if not application:
        return "Application not found"
    
    return render_template('caseworker/data-collection.html', application=application)

# ================= ELIGIBILITY MODULE =================
@app.route('/eligibility/<int:app_id>')
def check_eligibility(app_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get application
    cur.execute('SELECT * FROM citizen_apps WHERE app_id = ?', (app_id,))
    application = cur.fetchone()
    
    if not application:
        conn.close()
        return "Application not found"
    
    # Simple eligibility logic based on state
    state = application['state_name']
    ssn = application['ssn']
    
    # Map SSN to eligibility
    ssn_rules = {
        '987654': {'eligible': True, 'plan': 'SNAP', 'amount': 5000},
        '001003': {'eligible': True, 'plan': 'CCAP', 'amount': 8000},
        '343434': {'eligible': True, 'plan': 'Medicaid', 'amount': 10000},
        '268302': {'eligible': False, 'reason': 'Income exceeds limit'},
        '135158': {'eligible': True, 'plan': 'Medicare', 'amount': 12000}
    }
    
    if ssn in ssn_rules:
        result = ssn_rules[ssn]
    else:
        result = {'eligible': True, 'plan': 'QHP', 'amount': 3000}
    
    conn.close()
    
    return render_template('caseworker/eligibility-result.html',
                         application=application,
                         result=result)

# ================= CORRESPONDENCE MODULE =================
@app.route('/generate-notice/<int:app_id>')
def generate_notice(app_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM citizen_apps WHERE app_id = ?', (app_id,))
    application = cur.fetchone()
    conn.close()
    
    if not application:
        return "Application not found"
    
    # Create PDF notice
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    
    # Header
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(300, 800, "Government of India")
    pdf.drawCentredString(300, 780, "Health Insurance Scheme")
    pdf.drawCentredString(300, 760, "OFFICIAL NOTICE")
    
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, 740, f"Notice ID: HIS-NOTICE-{app_id:04d}")
    pdf.drawString(50, 725, f"Date: {datetime.now().strftime('%d/%m/%Y')}")
    
    pdf.line(50, 715, 550, 715)
    
    # Applicant Details
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 690, "Applicant Information:")
    
    pdf.setFont("Helvetica", 11)
    details = [
        f"Name: {application['fullname']}",
        f"SSN: {application['ssn']}",
        f"State: {application['state_name']}",
        f"Application ID: {app_id}",
        f"Application Date: {application['create_date']}"
    ]
    
    y = 665
    for detail in details:
        pdf.drawString(70, y, detail)
        y -= 20
    
    # Notice Content
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y-30, "Notice:")
    
    pdf.setFont("Helvetica", 11)
    notice = f"Dear {application['fullname']}, your health insurance application has been processed."
    pdf.drawString(70, y-60, notice)
    pdf.drawString(70, y-80, "Please contact your case worker for further details.")
    
    # Footer
    pdf.setFont("Helvetica", 9)
    pdf.drawString(50, 100, "Official Document - Health Insurance Scheme System")
    pdf.drawString(50, 85, "For verification: verify@his.gov.in")
    
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True,
                    download_name=f"HIS_Notice_{app_id}.pdf",
                    mimetype="application/pdf")

# ================= SYSTEM API ROUTES =================
@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Health Insurance System",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@app.route('/api/health')
def api_health():
    return jsonify({"status": "healthy", "api": "operational"}), 200

@app.route('/test')
def test():
    return "✅ Test route is working!"

@app.route('/api/admin/plan-categories', methods=['GET'])
def api_plan_categories():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM plan_category')
    categories = cur.fetchall()
    conn.close()
    
    return jsonify([dict(cat) for cat in categories])

@app.route('/api/admin/plan-category', methods=['POST'])
def api_create_plan_category():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute('''
        INSERT INTO plan_category (category_name, active_sw, create_date)
        VALUES (?, 'Y', DATE('now'))
    ''', (data['category_name'],))
    
    conn.commit()
    conn.close()
    return jsonify({"message": "Plan category created"})

# ================= DEBUG ROUTES =================
@app.route('/debug/db')
def debug_db():
    conn = get_db()
    cur = conn.cursor()
    
    tables = ['plan_category', 'plan_master', 'case_worker_accts', 'citizen_apps']
    result = {}
    
    for table in tables:
        cur.execute(f'SELECT COUNT(*) as count FROM {table}')
        result[table] = cur.fetchone()['count']
    
    conn.close()
    return jsonify(result)

@app.route('/debug/tables')
def debug_tables():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cur.fetchall()
    conn.close()
    
    return jsonify([dict(table) for table in tables])

# ================= INITIALIZATION =================
with app.app_context():
    init_tables()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)