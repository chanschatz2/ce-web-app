from flask import Blueprint, render_template, request, session, send_file, redirect, url_for
from .questions import questions, categories
import pandas as pd
import io
import copy
import datetime
from flask import flash
from . import get_db

data_input = Blueprint("data_input", __name__)

YEAR_CURRENT = str(datetime.datetime.now().year)
current_year = YEAR_CURRENT

def get_questions(sector):
    question_ids = categories.get(sector, [])
    return {str(q_id): questions[int(q_id)] for q_id in question_ids if q_id in questions}

# This should be called after any modification to responses_by_year
#   ensures all keys are strings so serializable into json
def session_responses(resp_by_year):
    session['responses_by_year'] = {
        str(year): {str(q_id): resp for q_id, resp in q_dict.items()}
        for year, q_dict in resp_by_year.items()
    }

# ensure years have at least one response
def clean_responses(responses):
    cleaned = {}

    valid_years = [
        year for year, year_responses in responses.items()
        if any(resp not in [None, ''] for resp in year_responses.values())
    ]

    for year in valid_years:
        cleaned[year] = copy.deepcopy(responses[year])

    return cleaned

def excel_download(responses):
    # ensure years have at least one response
    valid_years = [
        year for year, year_responses in responses.items()
        if any(resp not in [None, ''] for resp in year_responses.values())
    ]

    if len(valid_years) == 0:
        valid_years = [YEAR_CURRENT]

    data = []

    for q_id, question_text in questions.items():
        row = [str(q_id), question_text]
        for year in valid_years:
            row.append(responses.get(str(year), {}).get(str(q_id), ''))
            
        data.append(row)

    columns = ['Question ID', 'Question'] + [str(y) for y in valid_years]
    df = pd.DataFrame(data, columns=columns)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Responses')

    output.seek(0)
    return send_file(output, download_name='responses_template.xlsx', as_attachment=True)

def excel_upload(file, responses):
    df = pd.read_excel(file)

    # Expects first two columns to be 'Question ID' and 'Question'
    year_columns = df.columns[2:]

    for _, row in df.iterrows():
        q_id = row['Question ID']
        for year in year_columns:
            year_int = year
            if year_int not in responses:
                responses[year] = {}

            if str(row[year]) != 'nan':
                responses[year][str(q_id)] = str(float(row[year]))
            elif str(row[year]) == "nan":
                responses[year][str(q_id)] = ""

    return responses

def print_db(cur):
    print("\n DEBUG: Users", flush=True)
    cur.execute("SELECT * FROM users")
    for row in cur.fetchall():
        print(row, flush=True)

    print("\n DEBUG: Assessments", flush=True)
    cur.execute("SELECT * FROM assessments")
    for row in cur.fetchall():
        print(row, flush=True)

    print("\n DEBUG: Responses", flush=True)
    cur.execute("""
        SELECT r.*, a.user_id FROM responses r
        JOIN assessments a ON r.assessment_id = a.id
        ORDER BY a.user_id, r.year, r.question_id
    """)
    for row in cur.fetchall():
        print(row, flush=True)


@data_input.route('/data_input', methods=['GET', 'POST'])
def data_input_page():
    session.setdefault("YEAR_CURRENT", str(datetime.datetime.now().year))
    session.setdefault("current_year", int(session["YEAR_CURRENT"]))
    session.setdefault("responses_by_year", {})

    if "year" in request.args:
        try:
            session["current_year"] = int(request.args["year"])
        except ValueError:
            pass  # invalid year, ignore

    sector = session["sector"]
    sec_questions = get_questions(sector)
    responses_by_year = session["responses_by_year"]
    current_year = session["current_year"]

    # If arriving from analysis page Edit Responses, re-pull for db
    if request.args.get("from_analysis") == "true":
        session.pop("responses_loaded", None)

    """
    
        Current SQL logic (Jun 3 25):
        - Read and write user responses only when entering and leaving data_input page
        - To be wary of data_input route refreshes (year change, download, etc), track entering
            page with session["responses_loaded"] to flag when to pull responses
        - Unflag session["responses_loaded"] when outside data_input
            - e.g., analysis page Edit Responses button, root route, etc

    """

    if request.method == "GET":
        # LOAD RESPONSES FROM DATABASE ONCE
        if "responses_loaded" not in session:
            # Set current assessment being worked on
            assessment_id = request.args.get("assessment_id") or session["assessment_id"]

            # Load sector and industry from DB if arriving via URL ("View assessment button on dashboard")
            if request.args.get("assessment_id"):
                db = get_db()
                cur = db.cursor()
                cur.execute("SELECT sector, industry FROM assessments WHERE id = %s", (assessment_id,))
                row = cur.fetchone()
                if row:
                    session["sector"], session["industry"] = row

            if not assessment_id:
                flash("Assessment ID not provided", "danger")
                return redirect(url_for("views.dashboard"))
            session["assessment_id"] = int(assessment_id)


            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT year, question_id, response FROM responses WHERE assessment_id = %s", (assessment_id,))
            rows = cur.fetchall()

            responses_by_year = {}
            for year, qid, val in rows:
                year = str(year)
                if year not in responses_by_year:
                    responses_by_year[year] = {}
                responses_by_year[year][qid] = val

            session["responses_by_year"] = responses_by_year
            session["responses_loaded"] = True

    if request.method == "POST":        
        request_year = int(request.form.get("year", current_year))

        # Input Processing: Map question IDs to responses to ensure correct loading
        # Flag if non-numeric found
        flash_flag = False

        responses = {}
        for key, value in request.form.items():
            if key.startswith("response_"):
                q_id = key.split("response_")[1]
                value = value.strip()

                # Flash if non-numeric found, and stop button
                if value and not value.replace('.', '', 1).isdigit(): # removes decimal char
                    flash_flag = True
                    #responses[q_id] = value <- UNCOMMENT IF WANT TO KEEP ON FLASH
                else:
                    responses[q_id] = value

        # If non-numeric found, flash error and stop POST request
        if flash_flag:
            flash(f"Responses must be numerics. Non-numeric response(s) removed.", "danger")
            return render_template("data_input.html", questions=sec_questions,
                        responses=responses, current_year=current_year)

        if str(request_year) not in session["responses_by_year"]:
            session["responses_by_year"][str(request_year)] = {}

        session["responses_by_year"][str(request_year)] = responses
        session["responses_by_year"] = clean_responses(session["responses_by_year"])

        # Importing Excel handling
        if request.form.get("upload_excel") == "true":
            file = request.files.get("excel_file")

            if file and file.filename.endswith('.xlsx'):
                new_resp = excel_upload(file, responses_by_year)
                session_responses(new_resp)
            
            # fill in open responses on page load
            responses = session['responses_by_year'].get(current_year, {})

            return render_template("data_input.html", questions=sec_questions,
                           responses=responses, current_year=current_year, sector=session["sector"], industry=session["industry"])

        # Excel download handling
        if request.form.get("download_excel") == "true":
            session_responses(responses_by_year)
            return excel_download(session['responses_by_year'])

        if 'change_year' in request.form: # can't compare for "true" since value = direction
            current_year = int(current_year)

            if request.form['change_year'] == 'prev':
                current_year -= 1
            elif request.form['change_year'] == 'next':
                current_year += 1
            current_year = str(current_year)

            # update year
            session['current_year'] = current_year
            # re-render template
            responses = responses_by_year.get(str(current_year), {})
            session_responses(responses_by_year)
            return render_template("data_input.html", questions=sec_questions,
                           responses=responses, current_year=current_year, sector=session["sector"], industry=session["industry"])
        
        if request.form.get("visualize") == "true" or request.form.get("back_to_dash") == "true":
            assessment_id = session.get("assessment_id") # ensure current assessment being worked on
            print(assessment_id)
            if not assessment_id:
                flash("No active assessment found.", "danger")
                return redirect(url_for("views.dashboard"))

            # Only writing to db when done editing responses
            current_year = session["current_year"]
            responses_by_year = session["responses_by_year"]
            db = get_db()
            cur = db.cursor()

            for year, year_data in responses_by_year.items():
                for q_id, value in year_data.items():
                    cur.execute("""
                        INSERT INTO responses (assessment_id, year, question_id, response)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (assessment_id, year, question_id)
                        DO UPDATE SET response = EXCLUDED.response
                    """, (assessment_id, int(year), q_id, value))
            db.commit()

            print("----- AFTER INSERTION ------")
            print_db(cur)
            
            return redirect(url_for("analysis.analysis_page"))

        # Ensure responses_by_year is not sparse
        session["responses_by_year"] = clean_responses(session["responses_by_year"])

    # retrieve the responses for the current year (if any)
    responses = responses_by_year.get(str(current_year), {})
    # ensure session updated
    session_responses(responses_by_year)

    # reload webpage
    return render_template("data_input.html", questions=sec_questions,
                           responses=responses, current_year=current_year, sector=session["sector"], industry=session["industry"])