from flask import Flask, render_template, request, redirect, send_file, jsonify, session, flash
import psycopg2
import os
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

app = Flask(__name__)
app.secret_key = "health_insurance_system_2025"
app.config['SESSION_TYPE'] = 'filesystem'

# ================= DATABASE CONFIG =================

import os

def get_db():
    """Get PostgreSQL connection"""
    try:
        # Use environment variables from Render
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST', 'dpg-d702i27kijhs73d5c280-a.oregon-postgres.render.com'),
            port=os.environ.get('DB_PORT', 5432),
            database=os.environ.get('DB_NAME', 'his_db_fefp'),
            user=os.environ.get('DB_USER', 'his_user'),
            password=os.environ.get('DB_PASSWORD', '4iR6UV9XMeCZF8x0dKuMfzRMIkAahBs5'),
            sslmode='require'
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

def init_tables():
    """Create all tables"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Create citizen_apps table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS citizen_apps (
                app_id SERIAL PRIMARY KEY,
                fullname VARCHAR(200) NOT NULL,
                email VARCHAR(100),
                phno VARCHAR(20),
                ssn VARCHAR(20) UNIQUE,
                gender CHAR(1),
                state_name VARCHAR(100),
                create_date DATE DEFAULT CURRENT_DATE,
                update_date DATE,
                created_by VARCHAR(50)
            )
        ''')
        
        # Check if data exists
        cur.execute("SELECT COUNT(*) FROM citizen_apps")
        count = cur.fetchone()[0]
        
        if count == 0:
            cur.execute('''
                INSERT INTO citizen_apps (fullname, email, phno, ssn, gender, state_name, created_by)
                VALUES 
                ('Robert Brown', 'robert@email.com', '555-1234', '987-65-4321', 'M', 'New York', 'SYSTEM'),
                ('Alice Green', 'alice@email.com', '555-5678', '001-00-3003', 'F', 'Rhode Island', 'SYSTEM'),
                ('Mike Wilson', 'mike@email.com', '555-9012', '343-43-4343', 'M', 'California', 'SYSTEM'),
                ('Lisa Taylor', 'lisa@email.com', '555-3456', '268-30-2002', 'F', 'Ohio', 'SYSTEM'),
                ('David Miller', 'david@email.com', '555-7890', '135-15-8158', 'M', 'New Jersey', 'SYSTEM')
            ''')
        
        conn.commit()
        print("✅ citizen_apps table ready")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error in init_tables: {e}")    
    # Table-1: PLAN_CATEGORY
    cur.execute('''
        CREATE TABLE IF NOT EXISTS public.plan_category (
            category_id SERIAL PRIMARY KEY,
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
        CREATE TABLE IF NOT EXISTS public.plan_master (
            plan_id SERIAL PRIMARY KEY,
            plan_name VARCHAR(100) NOT NULL,
            plan_start_date DATE,
            plan_end_date DATE,
            plan_category_id INTEGER REFERENCES public.plan_category(category_id),
            active_sw CHAR(1) DEFAULT 'Y',
            create_date DATE DEFAULT CURRENT_DATE,
            update_date DATE,
            created_by VARCHAR(50),
            updated_by VARCHAR(50)
        )
    ''')
    
    # Table-3: CASE_WORKER_ACCTS
    cur.execute('''
        CREATE TABLE IF NOT EXISTS public.case_worker_accts (
            worker_id SERIAL PRIMARY KEY,
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
    
    # Table-4: CITIZEN_APPS (main table)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS public.citizen_apps (
            app_id SERIAL PRIMARY KEY,
            fullname VARCHAR(200) NOT NULL,
            email VARCHAR(100),
            phno VARCHAR(20),
            ssn VARCHAR(20) UNIQUE,
            gender CHAR(1),
            state_name VARCHAR(100),
            create_date DATE DEFAULT CURRENT_DATE,
            update_date DATE,
            created_by VARCHAR(50)
        )
    ''')
    
    # Table-5: DC_CASES
    cur.execute('''
        CREATE TABLE IF NOT EXISTS public.dc_cases (
            case_id SERIAL PRIMARY KEY,
            case_num INTEGER UNIQUE NOT NULL,
            app_id INTEGER REFERENCES public.citizen_apps(app_id),
            plan_id INTEGER REFERENCES public.plan_master(plan_id)
        )
    ''')
    
    # Table-6: DC_INCOME
    cur.execute('''
        CREATE TABLE IF NOT EXISTS public.dc_income (
            income_id SERIAL PRIMARY KEY,
            case_num INTEGER REFERENCES public.dc_cases(case_num),
            emp_income DECIMAL(10,2) DEFAULT 0,
            property_income DECIMAL(10,2) DEFAULT 0
        )
    ''')
    
    # Table-7: DC_CHILDRENS
    cur.execute('''
        CREATE TABLE IF NOT EXISTS public.dc_childrens (
            child_id SERIAL PRIMARY KEY,
            case_num INTEGER REFERENCES public.dc_cases(case_num),
            children_dob DATE NOT NULL,
            children_ssn VARCHAR(20)
        )
    ''')
    
    # Table-8: DC_EDUCATION
    cur.execute('''
        CREATE TABLE IF NOT EXISTS public.dc_education (
            edu_id SERIAL PRIMARY KEY,
            case_num INTEGER REFERENCES public.dc_cases(case_num),
            highest_qualification VARCHAR(100),
            graduation_year INTEGER
        )
    ''')
    
    # Table-9: ELIG_DTLS
    cur.execute('''
        CREATE TABLE IF NOT EXISTS public.elig_dtls (
            elig_id SERIAL PRIMARY KEY,
            case_num INTEGER REFERENCES public.dc_cases(case_num),
            plan_name VARCHAR(100) NOT NULL,
            plan_status VARCHAR(20) NOT NULL,
            plan_start_date DATE,
            plan_end_date DATE,
            benefit_amt DECIMAL(10,2),
            denial_reason VARCHAR(500),
            create_date DATE DEFAULT CURRENT_DATE
        )
    ''')
    
    # Table-10: CO_TRIGGERS
    cur.execute('''
        CREATE TABLE IF NOT EXISTS public.co_triggers (
            trigger_id SERIAL PRIMARY KEY,
            case_num INTEGER REFERENCES public.dc_cases(case_num),
            trg_status CHAR(1) DEFAULT 'P',
            notice TEXT,
            create_date DATE DEFAULT CURRENT_DATE,
            update_date DATE
        )
    ''')
    
    conn.commit()
    print("✅ All tables created in public schema")
    
    cur.close()
    conn.close()
    
    # ================= INSERT DEFAULT DATA =================
    
    # Insert case workers
    cur.execute("SELECT COUNT(*) FROM case_worker_accts")
    worker_count = cur.fetchone()[0]
    
    if worker_count == 0:
        cur.execute('''
            INSERT INTO case_worker_accts 
            (fullname, email, pwd, phno, gender, ssn, dob, created_by)
            VALUES 
            (%s, %s, %s, %s, %s, %s, %s, %s),
            (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            'Admin User', 'admin@his.gov', 'admin123', '9876543210', 'M', '987654', '1990-01-01', 'SYSTEM',
            'Case Worker 1', 'worker1@his.gov', 'worker123', '9876543211', 'F', '001003', '1992-05-15', 'SYSTEM'
        ))
        print("✅ Case workers added")
    
    # Insert plan categories
    cur.execute("SELECT COUNT(*) FROM plan_category")
    category_count = cur.fetchone()[0]
    
    if category_count == 0:
        categories = ['SNAP', 'CCAP', 'Medicaid', 'Medicare', 'QHP']
        for cat in categories:
            cur.execute('''
                INSERT INTO plan_category (category_name, created_by)
                VALUES (%s, %s)
            ''', (cat, 'SYSTEM'))
        print("✅ Plan categories added")
    
    # Insert sample plans
    cur.execute("SELECT COUNT(*) FROM plan_master")
    plan_count = cur.fetchone()[0]
    
    if plan_count == 0:
        # Get category IDs
        cur.execute("SELECT category_id FROM plan_category WHERE category_name = 'SNAP'")
        snap_id = cur.fetchone()
        
        cur.execute("SELECT category_id FROM plan_category WHERE category_name = 'Medicaid'")
        medicaid_id = cur.fetchone()
        
        if snap_id:
            cur.execute('''
                INSERT INTO plan_master 
                (plan_name, plan_start_date, plan_end_date, plan_category_id, created_by)
                VALUES (%s, %s, %s, %s, %s)
            ''', ('SNAP Benefits', '2024-01-01', '2024-12-31', snap_id[0], 'SYSTEM'))
        
        if medicaid_id:
            cur.execute('''
                INSERT INTO plan_master 
                (plan_name, plan_start_date, plan_end_date, plan_category_id, created_by)
                VALUES (%s, %s, %s, %s, %s)
            ''', ('Medicaid Basic', '2024-01-01', '2024-12-31', medicaid_id[0], 'SYSTEM'))
        print("✅ Sample plans added")
    
    # Insert sample citizen applications
    cur.execute("SELECT COUNT(*) FROM citizen_apps")
    citizen_count = cur.fetchone()[0]
    
    if citizen_count == 0:
        citizens_data = [
            ('Robert Brown', 'robert@email.com', '555-1234', '987-65-4321', 'M', 'New York'),
            ('Alice Green', 'alice@email.com', '555-5678', '001-00-3003', 'F', 'Rhode Island'),
            ('Mike Wilson', 'mike@email.com', '555-9012', '343-43-4343', 'M', 'California'),
            ('Lisa Taylor', 'lisa@email.com', '555-3456', '268-30-2002', 'F', 'Ohio'),
            ('David Miller', 'david@email.com', '555-7890', '135-15-8158', 'M', 'New Jersey')
        ]
        
        for citizen in citizens_data:
            cur.execute('''
                INSERT INTO citizen_apps 
                (fullname, email, phno, ssn, gender, state_name, create_date, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_DATE, %s)
            ''', (citizen[0], citizen[1], citizen[2], citizen[3], citizen[4], citizen[5], 'SYSTEM'))
        print("✅ Sample citizens added")
    
    conn.commit()
    
    # Verify tables created
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    
    print("\n" + "="*50)
    print("📊 PostgreSQL Database Setup Complete!")
    print("="*50)
    print(f"✅ Total tables created: {len(tables)}")
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cur.fetchone()[0]
        print(f"   - {table[0]}: {count} records")
    print("="*50)
    
    cur.close()
    conn.close()

# ================= DATA COLLECTION MODULE APIS =================

@app.route('/api/dc/create-case', methods=['POST'])
def api_create_case():
    """Create a new case for data collection"""
    data = request.json
    conn = get_db()
    cur = conn.cursor()

    try:
        # Generate case number
        cur.execute('SELECT MAX(case_num) FROM dc_cases')
        max_case = cur.fetchone()[0]
        case_num = 1000 if max_case is None else max_case + 1

        cur.execute('''
            INSERT INTO dc_cases (case_num, app_id, plan_id)
            VALUES (%s, %s, %s)
            RETURNING case_id
        ''', (case_num, data['app_id'], data['plan_id']))

        case_id = cur.fetchone()[0]
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Case created successfully",
            "case_id": case_id,
            "case_num": case_num
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        conn.close()

@app.route('/api/dc/add-income/<int:case_num>', methods=['POST'])
def api_add_income(case_num):
    """Add income data for a case"""
    data = request.json
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute('''
            INSERT INTO dc_income (case_num, emp_income, property_income)
            VALUES (%s, %s, %s)
            RETURNING income_id
        ''', (case_num, data.get('emp_income', 0), data.get('property_income', 0)))

        conn.commit()
        return jsonify({"success": True, "message": "Income data added"}), 201

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        conn.close()

@app.route('/api/dc/add-child/<int:case_num>', methods=['POST'])
def api_add_child(case_num):
    """Add child data for a case"""
    data = request.json
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute('''
            INSERT INTO dc_childrens (case_num, children_dob, children_ssn)
            VALUES (%s, %s, %s)
            RETURNING child_id
        ''', (case_num, data['children_dob'], data.get('children_ssn')))

        conn.commit()
        return jsonify({"success": True, "message": "Child data added"}), 201

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        conn.close()

@app.route('/api/dc/add-education/<int:case_num>', methods=['POST'])
def api_add_education(case_num):
    """Add education data for a case"""
    data = request.json
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute('''
            INSERT INTO dc_education (case_num, highest_qualification, graduation_year)
            VALUES (%s, %s, %s)
            RETURNING edu_id
        ''', (case_num, data['highest_qualification'], data.get('graduation_year')))

        conn.commit()
        return jsonify({"success": True, "message": "Education data added"}), 201

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        conn.close()

# ================= ELIGIBILITY MODULE APIS =================

@app.route('/api/eligibility/check/<int:case_num>', methods=['POST'])
def api_check_eligibility(case_num):
    """Check eligibility for a case"""
    conn = get_db()
    cur = conn.cursor()

    try:
        # Get case details - using column names properly
        cur.execute('''
            SELECT dc.case_num, ca.fullname, ca.state_name, ca.ssn, pm.plan_name
            FROM dc_cases dc
            JOIN citizen_apps ca ON dc.app_id = ca.app_id
            JOIN plan_master pm ON dc.plan_id = pm.plan_id
            WHERE dc.case_num = %s
        ''', (case_num,))
        case_data = cur.fetchone()

        if not case_data:
            return jsonify({"success": False, "error": "Case not found"}), 404

        # Convert to dict for easier access
        case_dict = dict(zip(['case_num', 'fullname', 'state_name', 'ssn', 'plan_name'], case_data))

        # Get income data
        cur.execute('SELECT * FROM dc_income WHERE case_num = %s', (case_num,))
        income_row = cur.fetchone()
        income_data = dict(zip([desc[0] for desc in cur.description], income_row)) if income_row else None

        # Get children count
        cur.execute('SELECT COUNT(*) FROM dc_childrens WHERE case_num = %s', (case_num,))
        children_count = cur.fetchone()[0]

        # Eligibility logic based on SSN (from your mapping)
        ssn = case_dict['ssn']
        ssn_rules = {
            '987654': {'eligible': True, 'plan': 'SNAP', 'amount': 5000},
            '001003': {'eligible': True, 'plan': 'CCAP', 'amount': 8000},
            '343434': {'eligible': True, 'plan': 'Medicaid', 'amount': 10000},
            '268302': {'eligible': False, 'reason': 'Income exceeds limit'},
            '135158': {'eligible': True, 'plan': 'Medicare', 'amount': 12000}
        }

        if ssn in ssn_rules:
            result = ssn_rules[ssn]
            status = 'APPROVED' if result['eligible'] else 'DENIED'
            benefit_amt = result.get('amount', 0)
            denial_reason = None if result['eligible'] else result.get('reason')
            plan_name = result.get('plan', case_dict['plan_name'])
        else:
            # Default logic
            if income_data and (income_data['emp_income'] + income_data['property_income']) < 30000:
                status = 'APPROVED'
                benefit_amt = 500 + (children_count * 200)
                denial_reason = None
                plan_name = case_dict['plan_name']
            else:
                status = 'DENIED'
                benefit_amt = 0
                denial_reason = 'Income exceeds threshold'
                plan_name = case_dict['plan_name']

        # Save eligibility decision
        cur.execute('''
            INSERT INTO elig_dtls 
            (case_num, plan_name, plan_status, plan_start_date, plan_end_date, benefit_amt, denial_reason)
            VALUES (%s, %s, %s, CURRENT_DATE, CURRENT_DATE + INTERVAL '1 year', %s, %s)
            RETURNING elig_id
        ''', (case_num, plan_name, status, benefit_amt, denial_reason))

        # Create correspondence trigger
        notice_text = f"Eligibility Status: {status}. "
        if status == 'APPROVED':
            notice_text += f"Approved for {plan_name} with benefit amount: ${benefit_amt}"
        else:
            notice_text += f"Denied. Reason: {denial_reason}"

        cur.execute('''
            INSERT INTO co_triggers (case_num, trg_status, notice)
            VALUES (%s, 'P', %s)
            RETURNING trigger_id
        ''', (case_num, notice_text))

        conn.commit()

        return jsonify({
            "success": True,
            "case_num": case_num,
            "applicant": case_dict['fullname'],
            "plan_name": plan_name,
            "status": status,
            "benefit_amount": benefit_amt,
            "denial_reason": denial_reason,
            "notice_generated": True
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        conn.close()

# ================= REPORTS APIS =================

@app.route('/api/reports/case-status')
def api_case_status_report():
    """Get report of all cases with status"""
    conn = get_db()
    cur = conn.cursor()

    cur.execute('''
        SELECT 
            dc.case_num,
            ca.fullname,
            ca.state_name,
            pm.plan_name,
            COALESCE(ed.plan_status, 'PENDING') as status,
            ed.benefit_amt,
            ed.create_date as decision_date
        FROM dc_cases dc
        JOIN citizen_apps ca ON dc.app_id = ca.app_id
        JOIN plan_master pm ON dc.plan_id = pm.plan_id
        LEFT JOIN elig_dtls ed ON dc.case_num = ed.case_num
        ORDER BY dc.case_num DESC
    ''')

    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    result = [dict(zip(columns, row)) for row in rows]
    conn.close()

    return jsonify(result)

@app.route('/api/reports/state-wise')
def api_state_wise_report():
    """Get report of applications by state"""
    conn = get_db()
    cur = conn.cursor()

    cur.execute('''
        SELECT 
            state_name,
            COUNT(*) as total_applications,
            SUM(CASE WHEN gender = 'M' THEN 1 ELSE 0 END) as male_count,
            SUM(CASE WHEN gender = 'F' THEN 1 ELSE 0 END) as female_count
        FROM citizen_apps
        GROUP BY state_name
        ORDER BY total_applications DESC
    ''')

    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    result = [dict(zip(columns, row)) for row in rows]
    conn.close()

    return jsonify(result)

@app.route('/api/reports/pending-triggers')
def api_pending_triggers():
    """Get pending correspondence triggers"""
    conn = get_db()
    cur = conn.cursor()

    cur.execute('''
        SELECT 
            ct.trigger_id,
            ct.case_num,
            ca.fullname,
            ca.email,
            ct.trg_status,
            ct.create_date,
            SUBSTRING(ct.notice, 1, 100) as notice_preview
        FROM co_triggers ct
        JOIN dc_cases dc ON ct.case_num = dc.case_num
        JOIN citizen_apps ca ON dc.app_id = ca.app_id
        WHERE ct.trg_status = 'P'
        ORDER BY ct.create_date DESC
    ''')

    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    result = [dict(zip(columns, row)) for row in rows]
    conn.close()

    return jsonify(result)

# ================= UTILITY APIS =================

@app.route('/api/get-citizen-by-ssn/<ssn>')
def api_get_citizen_by_ssn(ssn):
    """Get citizen details by SSN"""
    conn = get_db()
    cur = conn.cursor()

    cur.execute('SELECT * FROM citizen_apps WHERE ssn = %s', (ssn,))
    row = cur.fetchone()
    conn.close()

    if row:
        columns = [desc[0] for desc in cur.description]
        return jsonify(dict(zip(columns, row)))
    else:
        return jsonify({"error": "Citizen not found"}), 404

@app.route('/api/get-cases-by-app/<int:app_id>')
def api_get_cases_by_app(app_id):
    """Get all cases for an application"""
    conn = get_db()
    cur = conn.cursor()

    cur.execute('''
        SELECT dc.*, pm.plan_name, ca.fullname
        FROM dc_cases dc
        JOIN plan_master pm ON dc.plan_id = pm.plan_id
        JOIN citizen_apps ca ON dc.app_id = ca.app_id
        WHERE dc.app_id = %s
        ORDER BY dc.case_num DESC
    ''', (app_id,))

    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    result = [dict(zip(columns, row)) for row in rows]
    conn.close()

    return jsonify(result)

@app.route('/api/get-case-details/<int:case_num>')
def api_get_case_details(case_num):
    """Get complete details of a case"""
    conn = get_db()
    cur = conn.cursor()

    # Case info
    cur.execute('''
        SELECT dc.*, ca.*, pm.plan_name, pc.category_name
        FROM dc_cases dc
        JOIN citizen_apps ca ON dc.app_id = ca.app_id
        JOIN plan_master pm ON dc.plan_id = pm.plan_id
        LEFT JOIN plan_category pc ON pm.plan_category_id = pc.category_id
        WHERE dc.case_num = %s
    ''', (case_num,))
    case_row = cur.fetchone()

    if not case_row:
        conn.close()
        return jsonify({"error": "Case not found"}), 404

    case_columns = [desc[0] for desc in cur.description]
    case_info = dict(zip(case_columns, case_row))

    # Income data
    cur.execute('SELECT * FROM dc_income WHERE case_num = %s', (case_num,))
    income_row = cur.fetchone()
    income = dict(zip([desc[0] for desc in cur.description], income_row)) if income_row else None

    # Children data
    cur.execute('SELECT * FROM dc_childrens WHERE case_num = %s', (case_num,))
    children_rows = cur.fetchall()
    children_columns = [desc[0] for desc in cur.description]
    children = [dict(zip(children_columns, row)) for row in children_rows]

    # Education data
    cur.execute('SELECT * FROM dc_education WHERE case_num = %s', (case_num,))
    edu_row = cur.fetchone()
    education = dict(zip([desc[0] for desc in cur.description], edu_row)) if edu_row else None

    # Eligibility data
    cur.execute('SELECT * FROM elig_dtls WHERE case_num = %s ORDER BY create_date DESC LIMIT 1', (case_num,))
    elig_row = cur.fetchone()
    eligibility = dict(zip([desc[0] for desc in cur.description], elig_row)) if elig_row else None

    conn.close()

    response = {
        "case_info": case_info,
        "income": income,
        "children": children,
        "education": education,
        "eligibility": eligibility
    }

    return jsonify(response)

@app.route('/debug/all-tables')
def debug_all_tables():
    """Debug endpoint to see all tables and their data"""
    conn = get_db()
    cur = conn.cursor()
    
    # Get all tables from PostgreSQL
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = cur.fetchall()
    
    result = {}
    
    for table in tables:
        table_name = table[0]
        
        # Get row count
        cur.execute(f'SELECT COUNT(*) as count FROM {table_name}')
        count = cur.fetchone()[0]
        
        # Get sample data (first 5 rows)
        cur.execute(f'SELECT * FROM {table_name} LIMIT 5')
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description] if cur.description else []
        
        result[table_name] = {
            'row_count': count,
            'columns': columns,
            'sample_data': [dict(zip(columns, row)) for row in rows]
        }
    
    conn.close()
    return jsonify(result)

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
            # Server-side validation
            fullname = request.form.get('fullname', '').strip()
            email = request.form.get('email', '').strip()
            phno = request.form.get('phno', '').strip()
            ssn = request.form.get('ssn', '').strip()
            gender = request.form.get('gender', '').strip()
            state_name = request.form.get('state_name', 'New York').strip()

            def valid_email(e):
                import re
                return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", e)) if e else True

            if not fullname:
                flash('Full name is required', 'danger')
                return redirect('/public/register')
            if not ssn:
                flash('SSN is required', 'danger')
                return redirect('/public/register')
            if email and not valid_email(email):
                flash('Enter a valid email address', 'danger')
                return redirect('/public/register')

            cur.execute('''
                INSERT INTO citizen_apps 
                (fullname, email, phno, ssn, gender, state_name, create_date)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_DATE)
                RETURNING app_id
            ''', (
                fullname,
                email,
                phno,
                ssn,
                gender,
                state_name
            ))
            
            app_id = cur.fetchone()[0]
            conn.commit()
            flash(f'✅ Application submitted! Your Application ID: {app_id}', 'success')
            return redirect(f'/application/{app_id}/status')

        except psycopg2.IntegrityError as e:
            if 'ssn' in str(e).lower():
                flash('❌ SSN already registered!', 'danger')
            else:
                flash('❌ Email already registered!', 'danger')
        except Exception as e:
            flash(f'❌ Error: {str(e)}', 'danger')
        finally:
            conn.close()
    
    return render_template('public/register.html')

@app.route('/application/<int:app_id>/status')
def application_status(app_id):
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute('SELECT * FROM citizen_apps WHERE app_id = %s', (app_id,))
    row = cur.fetchone()
    
    if not row:
        conn.close()
        return "Application not found"
    
    columns = [desc[0] for desc in cur.description]
    application = dict(zip(columns, row))
    conn.close()
    
    return render_template('public/status.html', application=application)


@app.route('/application-status-search')
def application_status_search():
    """Simple helper to redirect from a search form to the application status page."""
    app_id = request.args.get('app_id')
    if not app_id:
        flash('Please provide an Application ID', 'warning')
        return redirect('/public/check-status')

    # sanitize numeric id
    try:
        int_app_id = int(app_id)
    except Exception:
        flash('Invalid Application ID', 'danger')
        return redirect('/public/check-status')

    return redirect(f'/application/{int_app_id}/status')

@app.route('/check-status')
@app.route('/public/check-status')
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
        cur.execute('SELECT * FROM case_worker_accts WHERE email = %s AND pwd = %s', 
                   (email, password))
        row = cur.fetchone()
        conn.close()
        
        if row:
            columns = [desc[0] for desc in cur.description]
            user = dict(zip(columns, row))
            session['user_id'] = user['worker_id']
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
            VALUES (%s, %s, %s, CURRENT_DATE)
        ''', (category_name, active_sw, session['user_name']))
        conn.commit()
        flash('✅ Plan category added successfully!', 'success')
        return redirect('/admin/plan-category')
    
    cur.execute('SELECT * FROM plan_category ORDER BY create_date DESC')
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    categories = [dict(zip(columns, row)) for row in rows]
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
            VALUES (%s, %s, %s, %s, %s, CURRENT_DATE)
            RETURNING plan_id
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
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    plans = [dict(zip(columns, row)) for row in rows]
    
    # Get categories for dropdown
    cur.execute('SELECT category_id, category_name FROM plan_category WHERE active_sw = %s', ('Y',))
    cat_rows = cur.fetchall()
    categories = [dict(zip([desc[0] for desc in cur.description], row)) for row in cat_rows]
    
    conn.close()
    
    return render_template('admin/plan-master.html', plans=plans, categories=categories)

@app.route('/admin/caseworkers', methods=['GET', 'POST'])
def admin_caseworkers():
    if 'user_role' not in session or session['user_role'] != 'ADMIN':
        return redirect('/login')
    
    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST':
        # Create a new caseworker from admin form
        fullname = request.form.get('fullname', '').strip()
        email = request.form.get('email', '').strip()
        pwd = request.form.get('pwd', 'changeme')
        phno = request.form.get('phno', '').strip()
        gender = request.form.get('gender', '').strip()
        ssn = request.form.get('ssn', '').strip()
        dob = request.form.get('dob', '').strip()

        # server-side validation
        import re
        def valid_email(e):
            return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", e))

        if not fullname:
            msg = 'Full name is required'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'danger')
            cur.close(); conn.close();
            return redirect('/admin/caseworkers')

        if email and not valid_email(email):
            msg = 'Enter a valid email address'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'danger')
            cur.close(); conn.close();
            return redirect('/admin/caseworkers')

        if not pwd or len(pwd) < 6:
            msg = 'Password must be at least 6 characters'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'danger')
            cur.close(); conn.close();
            return redirect('/admin/caseworkers')

        try:
            cur.execute('''
                INSERT INTO case_worker_accts
                (fullname, email, pwd, phno, gender, ssn, dob, created_by, create_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE)
                RETURNING worker_id
            ''', (fullname, email, pwd, phno, gender, ssn, dob, session.get('user_name', 'SYSTEM')))
            new_id = cur.fetchone()[0]
            conn.commit()

            # Respond differently for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({'success': True, 'message': 'Caseworker added', 'worker_id': new_id}), 201

            flash('✅ Caseworker added successfully!', 'success')
            return redirect('/admin/caseworkers')
        except psycopg2.IntegrityError as e:
            msg = '❌ Email or SSN already exists!'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'danger')
        except Exception as e:
            msg = f'❌ Error creating caseworker: {e}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({'success': False, 'message': msg}), 500
            flash(msg, 'danger')

    cur.execute('SELECT * FROM case_worker_accts ORDER BY create_date DESC')
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    workers = [dict(zip(columns, row)) for row in rows]
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
    
    cur.execute('SELECT COUNT(*) FROM citizen_apps WHERE DATE(create_date) = CURRENT_DATE')
    today_apps = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM citizen_apps WHERE state_name = %s', ('New York',))
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
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    applications = [dict(zip(columns, row)) for row in rows]
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
    cur.execute('SELECT * FROM citizen_apps WHERE app_id = %s', (app_id,))
    row = cur.fetchone()
    conn.close()
    
    if not row:
        return "Application not found"
    
    columns = [desc[0] for desc in cur.description]
    application = dict(zip(columns, row))
    
    return render_template('caseworker/data-collection.html', application=application)

# ================= ELIGIBILITY MODULE =================
@app.route('/eligibility/<int:app_id>')
def check_eligibility(app_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get application
    cur.execute('SELECT * FROM citizen_apps WHERE app_id = %s', (app_id,))
    row = cur.fetchone()
    
    if not row:
        conn.close()
        return "Application not found"
    
    columns = [desc[0] for desc in cur.description]
    application = dict(zip(columns, row))
    
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
    cur.execute('SELECT * FROM citizen_apps WHERE app_id = %s', (app_id,))
    row = cur.fetchone()
    conn.close()
    
    if not row:
        return "Application not found"
    
    columns = [desc[0] for desc in cur.description]
    application = dict(zip(columns, row))
    
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


@app.route('/download-notice/<int:app_id>')
def download_notice(app_id):
    """Alias for /generate-notice to keep older templates working."""
    return generate_notice(app_id)

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
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    categories = [dict(zip(columns, row)) for row in rows]
    conn.close()
    
    return jsonify(categories)

@app.route('/api/admin/plan-category', methods=['POST'])
def api_create_plan_category():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute('''
        INSERT INTO plan_category (category_name, active_sw, create_date)
        VALUES (%s, 'Y', CURRENT_DATE)
        RETURNING category_id
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
        result[table] = cur.fetchone()[0]
    
    conn.close()
    return jsonify(result)

@app.route('/debug/tables')
def debug_tables():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = cur.fetchall()
    conn.close()
    
    return jsonify([table[0] for table in tables])

# ================= INITIALIZATION =================
#with app.app_context():
 #   init_tables()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)