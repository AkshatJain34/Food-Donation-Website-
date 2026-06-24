from flask import Flask, render_template, request, redirect, url_for, session
import oracledb
app = Flask(__name__)
app.secret_key = 'mriirs_engineering_secret'

# --- ORACLE DATABASE CONFIGURATION ---
db_config = {
    "user": "KRITPAL1601_SCHEMA_AHLFK",
    "password": "Sonu._007", # Update with your actual password
    "dsn": "localhost:1521/xe"   # or XEPDB1 depending on your listener status
}

def get_db_connection():
    try:
        return oracledb.connect(**db_config)
    except Exception as e:
        print(f"--- DB CONNECTION ERROR: {e} ---")
        return None

# ==========================================
# PAGE ROUTES (GET Requests)
# ==========================================

@app.route('/')
def index():
    return render_template('front.html')

@app.route('/about')
def about():
    return render_template('About.html')

@app.route('/ngos')
def ngos():
    return render_template('NGO.html')

@app.route('/login')
def login_page():
    return render_template('login11.html')

@app.route('/signup')
def signup_page():
    return render_template('signup.html')

@app.route('/signngo')
def signngo_page():
    return render_template('signngo.html')

@app.route('/forget')
def forget_page():
    return render_template('Forget.html')

@app.route('/forgetngo')
def forgetngo_page():
    return render_template('Forgetngo.html')

# Protected Route: Only logged-in users can see the donation form
@app.route('/donate')
def donate_page():
    if 'user_email' in session:
        return render_template('interface.html')
    return redirect(url_for('login_page'))

# Protected Route: Only logged-in NGOs can see the dashboard
@app.route('/ngo-dashboard')
def ngo_dashboard():
    if 'ngo_email' in session:
        return render_template('ngointeface.html')
    return redirect(url_for('login_page'))

# ==========================================
# FORM PROCESSING ROUTES (POST Requests)
# ==========================================

# 1. User Signup
@app.route('/handle_signup', methods=['POST'])
def handle_signup():
    f_name = request.form.get('firstName')
    l_name = request.form.get('lastName')
    email = request.form.get('email')
    pwd = request.form.get('password')

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO USERS (FIRST_NAME, LAST_NAME, EMAIL, PASSWORD) 
                VALUES (:1, :2, :3, :4)""", (f_name, l_name, email, pwd))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('login_page'))
        except Exception as e:
            print(f"Signup Error: {e}")
    return "Registration Failed"

# 2. User Login
@app.route('/user/login', methods=['POST'])
def user_login():
    email = request.form.get('email')
    pwd = request.form.get('password')

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT EMAIL FROM USERS WHERE EMAIL = :1 AND PASSWORD = :2", (email, pwd))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['user_email'] = email
            return redirect(url_for('donate_page'))
    
    return "Invalid User Credentials"

# 3. NGO Login
@app.route('/ngo/login', methods=['POST'])
def ngo_login():
    email = request.form.get('email')
    pwd = request.form.get('password')
    
    # For now, bypassing DB check for NGO to allow immediate testing.
    # You can add an 'NGOS' table check here later, similar to the User login.
    if email and pwd:
        session['ngo_email'] = email
        return redirect(url_for('ngo_dashboard'))
    
    return "Invalid NGO Credentials"

# 4. Submit Food Donation
@app.route('/submit-donation', methods=['POST'])
def submit_donation():
    name = request.form.get('fullName')
    phone = request.form.get('phone')
    city = request.form.get('city')
    food = request.form.get('foodItems')
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO DONATIONS (DONOR_NAME, PHONE, CITY, FOOD_ITEM)
                VALUES (:1, :2, :3, :4)""", (name, phone, city, food))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Donation Error: {e}")
            
    return render_template('thanks.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
