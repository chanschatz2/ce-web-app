from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from . import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from create_db import init_schema

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
def root(): # reroutes to dashboard if logged in, otherwise to login
    if 'company_id' in session:
        return redirect(url_for("views.dashboard"))
    return redirect(url_for("views.login"))

@views.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        company_id = request.form.get("company_id")
        password = request.form.get("password")

        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT password FROM companies WHERE id = %s", (company_id,))
        result = cur.fetchone()

        if result and check_password_hash(result[0], password):
            session['company_id'] = company_id
            return redirect(url_for("views.dashboard"))
        else:
            flash("Invalid credentials.", "danger")

    return render_template("login.html")

@views.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        company_id = request.form.get("company_id")
        password = request.form.get("password")
        hashed_pw = generate_password_hash(password)

        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("INSERT INTO companies (id, password) VALUES (%s, %s)", (company_id, hashed_pw))
            db.commit()
            session['company_id'] = company_id
            return redirect(url_for("views.dashboard"))
        except:
            flash("Company ID already exists.", "danger")

    return render_template("register.html")

@views.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if 'company_id' not in session:
        return redirect(url_for('views.login'))
    return render_template("dashboard.html")

@views.route("/selection", methods=["GET", "POST"])
def selection():
    if request.method == "POST":
        sector = request.form.get("sector")
        industry = request.form.get("industry")

        # TODO: CHANGE LATER, JUST FOR PROTOTYPE:
        if sector == "Energy":
            sector = "Energy&Utilities"

        session['sector'] = sector

        # Ensures responses will be pulled from db on Start Over
        session.pop("responses_loaded", None)
        session.pop("responses_by_year", None)

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