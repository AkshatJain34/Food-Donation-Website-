from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'food_donation_secret_key'

# --- MYSQL DATABASE CONFIGURATION ---
db_config = {
    "host":     "localhost",
    "user":     "root",
    "password": "Sonu._007",   # <-- CHANGE THIS to your MySQL password
    "database": "fooddonation"
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
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

@app.route('/Forget')
def forget_page():
    return render_template('Forget.html')

@app.route('/Forgetngo')
def forgetngo_page():
    return render_template('Forgetngo.html')

@app.route('/thanks')
def thanks_page():
    return render_template('thanks.html')

# Protected: Only logged-in users can donate
@app.route('/donate')
def donate_page():
    if 'user_email' in session:
        return render_template('interface.html')
    return redirect(url_for('login_page'))

# Protected: Donations list visible to both users and NGOs
# Claim button shown to NGOs only
@app.route('/donations-list')
def donations_list():
    if 'user_email' not in session and 'ngo_email' not in session:
        return redirect(url_for('login_page'))

    is_ngo  = 'ngo_email' in session        # True = show Claim button
    message = request.args.get('message')   # success/error message after claim
    donations = []

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT DONATION_ID, DONOR_NAME, CITY, PHONE,
                       FOOD_ITEM, QUANTITY, CREATED_AT, STATUS, CLAIMED_BY
                FROM DONATIONS
                ORDER BY DONATION_ID DESC
            """)
            rows = cursor.fetchall()
            donations = list(enumerate(rows, start=1))
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Donations List Error: {e}")

    return render_template('donations_list.html', donations=donations,
                           message=message, is_ngo=is_ngo)

# Protected: Only logged-in NGOs can see dashboard
@app.route('/ngo-dashboard')
def ngo_dashboard():
    if 'ngo_email' not in session:
        return redirect(url_for('login_page'))

    message   = request.args.get('message')
    donations = []
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT DONATION_ID, DONOR_NAME, CITY, PHONE,
                       FOOD_ITEM, QUANTITY, STATUS, CLAIMED_BY
                FROM DONATIONS
                ORDER BY DONATION_ID DESC
            """)
            donations = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Dashboard Error: {e}")

    return render_template('ngointeface.html', donations=donations, message=message)


# ==========================================
# FORM PROCESSING ROUTES (POST Requests)
# ==========================================

# 1. User Signup
@app.route('/handle_signup', methods=['POST'])
def handle_signup():
    f_name = request.form.get('firstName')
    l_name = request.form.get('lastName')
    email  = request.form.get('email')
    pwd    = request.form.get('password')

    print(f">>> Signup attempt: {f_name} {l_name} | {email}")

    hashed_pwd = generate_password_hash(pwd)

    conn = get_db_connection()
    print(f">>> DB Connection: {conn}")

    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO USERS (FIRST_NAME, LAST_NAME, EMAIL, PASSWORD)
                VALUES (%s, %s, %s, %s)
            """, (f_name, l_name, email, hashed_pwd))
            conn.commit()
            cursor.close()
            conn.close()
            print(">>> Signup successful!")
            return redirect(url_for('login_page'))
        except mysql.connector.IntegrityError:
            return "Email already registered. <a href='/signup'>Try again</a>", 400
        except Exception as e:
            print(f"Signup Error: {e}")

    return "Registration Failed. Please try again.", 500


# 2. NGO Signup
@app.route('/handle_ngo_signup', methods=['POST'])
def handle_ngo_signup():
    f_name = request.form.get('firstName')
    l_name = request.form.get('lastName')
    email  = request.form.get('email')
    pwd    = request.form.get('password')

    hashed_pwd = generate_password_hash(pwd)

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO NGOS (FIRST_NAME, LAST_NAME, EMAIL, PASSWORD)
                VALUES (%s, %s, %s, %s)
            """, (f_name, l_name, email, hashed_pwd))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('login_page'))
        except mysql.connector.IntegrityError:
            return "Email already registered. <a href='/signngo'>Try again</a>", 400
        except Exception as e:
            print(f"NGO Signup Error: {e}")

    return "NGO Registration Failed. Please try again.", 500


# 3. User Login
@app.route('/user/login', methods=['POST'])
def user_login():
    email = request.form.get('email')
    pwd   = request.form.get('password')

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT EMAIL, PASSWORD FROM USERS WHERE EMAIL = %s", (email,)
            )
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user and check_password_hash(user['PASSWORD'], pwd):
                session['user_email'] = email
                return redirect(url_for('donate_page'))
        except Exception as e:
            print(f"User Login Error: {e}")

    return "Invalid email or password. <a href='/login'>Try again</a>", 401


# 4. NGO Login
@app.route('/ngo/login', methods=['POST'])
def ngo_login():
    email = request.form.get('email')
    pwd   = request.form.get('password')

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT EMAIL, PASSWORD FROM NGOS WHERE EMAIL = %s", (email,)
            )
            ngo = cursor.fetchone()
            cursor.close()
            conn.close()

            if ngo and check_password_hash(ngo['PASSWORD'], pwd):
                session['ngo_email'] = email
                return redirect(url_for('ngo_dashboard'))
        except Exception as e:
            print(f"NGO Login Error: {e}")

    return "Invalid NGO credentials. <a href='/login'>Try again</a>", 401


# 5. Submit Food Donation
@app.route('/submit-donation', methods=['POST'])
def submit_donation():
    name     = request.form.get('fullName')
    phone    = request.form.get('phone')
    city     = request.form.get('city')
    food     = request.form.get('foodItems')
    quantity = request.form.get('quantity')

    user_email = session.get('user_email')
    print(f">>> Donation form received: name={name}, phone={phone}, city={city}, food={food}, qty={quantity}, user={user_email}")

    conn = get_db_connection()
    print(f">>> DB connection for donation: {conn}")

    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO DONATIONS (DONOR_NAME, PHONE, CITY, FOOD_ITEM, QUANTITY, STATUS, USER_EMAIL)
                VALUES (%s, %s, %s, %s, %s, 'Available', %s)
            """, (name, phone, city, food, quantity, user_email))
            conn.commit()
            cursor.close()
            conn.close()
            print(">>> Donation inserted successfully!")
        except Exception as e:
            print(f">>> Donation Error: {e}")
    else:
        print(">>> Donation failed: No DB connection")

    return render_template('thanks.html')


# 6. Claim a Donation — NGOs only
@app.route('/claim-donation', methods=['POST'])
def claim_donation():
    # Only NGOs can claim donations
    if 'ngo_email' not in session:
        return "Unauthorized. Only NGOs can claim donations. <a href='/login'>Login as NGO</a>", 403

    claimer = session.get('ngo_email')

    donation_id = request.form.get('donation_id')

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()

            # First check if it's still available (prevent double-claiming)
            cursor.execute(
                "SELECT STATUS FROM DONATIONS WHERE DONATION_ID = %s", (donation_id,)
            )
            row = cursor.fetchone()

            if row and row[0] == 'Available':
                cursor.execute("""
                    UPDATE DONATIONS
                    SET STATUS = 'Claimed', CLAIMED_BY = %s
                    WHERE DONATION_ID = %s
                """, (claimer, donation_id))
                conn.commit()
                msg = f"Donation successfully claimed by {claimer}!"
            else:
                msg = "This donation was already claimed by someone else."

            cursor.close()
            conn.close()

        except Exception as e:
            print(f"Claim Error: {e}")
            msg = "An error occurred. Please try again."

        # Redirect back with success message
        if 'ngo_email' in session:
            return redirect(url_for('ngo_dashboard', message=msg))
        return redirect(url_for('donations_list', message=msg))

    return redirect(url_for('donations_list'))


# 7. Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# My Donations — shows only the logged-in user's own donations
@app.route('/my-donations')
def my_donations():
    if 'user_email' not in session:
        return redirect(url_for('login_page'))

    user_email = session.get('user_email')
    donations  = []
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT DONATION_ID, DONOR_NAME, CITY, PHONE,
                       FOOD_ITEM, QUANTITY, CREATED_AT, STATUS, CLAIMED_BY
                FROM DONATIONS
                WHERE USER_EMAIL = %s
                ORDER BY DONATION_ID DESC
            """, (user_email,))
            rows = cursor.fetchall()
            donations = list(enumerate(rows, start=1))
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"My Donations Error: {e}")

    return render_template('my_donations.html', donations=donations, user_email=user_email)


# ==========================================
# DEBUG ROUTE — remove after fixing
# ==========================================
@app.route('/debug')
def debug():
    conn = get_db_connection()
    if not conn:
        return "<h2 style='color:red'>DB CONNECTION FAILED — check your password in db_config</h2>"
    try:
        cursor = conn.cursor(dictionary=True)

        # Check table structure
        cursor.execute("DESCRIBE DONATIONS")
        columns = [row['Field'] for row in cursor.fetchall()]

        # Check all rows
        cursor.execute("SELECT * FROM DONATIONS")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        html  = f"<h2 style='color:green'>✅ DB Connected OK</h2>"
        html += f"<p><b>Columns in DONATIONS:</b> {columns}</p>"
        if rows:
            html += f"<p><b>Total rows:</b> {len(rows)}</p>"
            for r in rows:
                html += f"<p>{r}</p>"
        else:
            html += "<p style='color:red'><b>DONATIONS table is EMPTY — the INSERT is failing.</b><br>"
            html += "Check Flask terminal for 'Donation Error:' message.</p>"
        return html
    except Exception as e:
        return f"<h2 style='color:red'>Query Failed: {e}</h2>"


# Also add extra prints to submit_donation for diagnosis
# (already in the route above — check Flask terminal when submitting)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
