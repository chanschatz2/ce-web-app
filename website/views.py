from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from . import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from create_db import init_schema
import datetime

views = Blueprint("views", __name__)

energy_i = ["Energy", "Waste Management", "Water Utilities", "Logistics", "Railroad", "Telecommunications"]
services_i = []
manufacturing_i = ["Manufacturing"]
automotive_i = []

INDUSTRIES = {
    "Energy": energy_i,
    "Services": services_i,
    "Manufacturing": manufacturing_i,
    "Automotive": automotive_i
}

@views.route("/", methods=["GET", "POST"])
def root():
    return render_template("landing.html", current_year=datetime.datetime.now().year)

@views.route("/login", methods=["GET", "POST"])
def login():
    if 'user_id' in session: # if logged in, redirects to dashboard
        return redirect(url_for("views.dashboard"))

    if request.method == "POST":
        user_id = request.form.get("user_id")
        password = request.form.get("password")

        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT password FROM users WHERE id = %s", (user_id,))
        result = cur.fetchone()

        if result and check_password_hash(result[0], password):
            session['user_id'] = user_id
            return redirect(url_for("views.dashboard"))
        else:
            flash("Invalid credentials.", "danger")

    return render_template("login.html")

@views.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user_id = request.form.get("user_id")
        password = request.form.get("password")
        hashed_pw = generate_password_hash(password)

        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("INSERT INTO users (id, password) VALUES (%s, %s)", (user_id, hashed_pw))
            db.commit()
            session['user_id'] = user_id
            return redirect(url_for("views.dashboard"))
        except:
            flash("User ID already exists.", "danger")

    return render_template("register.html")

@views.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT id, created_at, sector, industry, score
        FROM assessments
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (session["user_id"],))
    assessments = cur.fetchall()

    return render_template("dashboard.html", assessments=assessments)

# Delete Assessment
@views.route("/delete_assessment", methods=["POST"])
def delete_assessment():
    if 'user_id' not in session:
        return redirect(url_for("views.login"))

    assessment_id = request.form.get("assessment_id")
    if not assessment_id:
        flash("No assessment ID provided.", "danger")
        return redirect(url_for("views.dashboard"))

    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM assessments WHERE id = %s AND user_id = %s", (assessment_id, session["user_id"]))
    db.commit()

    # Unset if it was the one in session
    if session.get("assessment_id") == int(assessment_id):
        session.pop("assessment_id", None)

    flash("Assessment deleted.", "success")
    return redirect(url_for("views.dashboard"))


@views.route("/selection", methods=["GET", "POST"])
def selection():
    if request.method == "POST":
        sector = request.form.get("sector")
        industry = request.form.get("industry")

        # TODO: CHANGE LATER, JUST FOR PROTOTYPE:
        if sector == "Energy":
            sector = "Energy&Utilities"

        session['sector'] = sector
        session['industry'] = industry

        # Ensures responses will be pulled from db on Start Over
        session.pop("responses_loaded", None)
        session.pop("responses_by_year", None)

        # create new assessment
        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO assessments (user_id, sector, industry) VALUES (%s, %s, %s) RETURNING id",
            (session['user_id'], sector, industry)) # return assessment "id" for session storage
        session['assessment_id'] = cur.fetchone()[0] # current assessment being worked on
        db.commit()

        return redirect(url_for("data_input.data_input_page", sector=sector, industry=industry))
    return render_template("selection.html", industries=INDUSTRIES)

# DEBUG ROUTE
@views.route("/clear_session")
def clear_session():
    session.clear()
    return redirect(url_for("views.root"))

# DEBUG ROUTE
# WIPES DB ON CREATION - ONLY RUN ON INIT
@views.route("/init_db")
def init_db_route(): # creates schema
    try:
        init_schema()
        return "Schema initialized successfully"
    except Exception as e:
        return f"Error initalizing db"