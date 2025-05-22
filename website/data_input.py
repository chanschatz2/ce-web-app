from flask import Blueprint, render_template, request, session, send_file, redirect, url_for
from .questions import questions, categories
import pandas as pd
import io
import copy
import datetime

data_input = Blueprint("data_input", __name__)

# stores responses per year
#responses_by_year = None
YEAR_CURRENT = str(datetime.datetime.now().year)
current_year = YEAR_CURRENT
#sector = None

def get_questions(sector):
    question_ids = categories.get(sector, [])
    return {str(q_id): questions[int(q_id)] for q_id in question_ids if q_id in questions}

# ensure all keys are strings so serializable into json
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
    # TODO: can replace with clean_resposnes() defined above 
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

    # Expect first two columns to be 'Question ID' and 'Question'
    year_columns = df.columns[2:]

    for _, row in df.iterrows():
        q_id = row['Question ID']
        for year in year_columns:
            year_int = year
            if year_int not in responses:
                responses[year] = {}

            if str(row[year]) != 'nan':
                responses[year][str(q_id)] = str(int(row[year]))
            elif str(row[year]) == "nan":
                responses[year][str(q_id)] = ""

    return responses

@data_input.route('/data_input', methods=['GET', 'POST'])
def data_input_page():
    if "year" in request.args:
        try:
            session["current_year"] = int(request.args["year"])
        except ValueError:
            pass  # invalid year, ignore

    session["YEAR_CURRENT"] = str(datetime.datetime.now().year)
    
    try:
        responses_by_year = session.get('responses_by_year')

        if responses_by_year == None:
            raise Exception("responses_by_year is None")
    except Exception as e:
        # if not yet set, set to empty dict
        print(e)
        print("setting resp by year as {}")
        session['responses_by_year'] = {}
        responses_by_year = session['responses_by_year']

    global current_year
    sector = session.get('sector')

    sec_questions = get_questions(sector)

    if request.method == "POST":
        responses_by_year = session.get('responses_by_year')
        
        # ------ Saving Current Response Data ------ 
        year = int(request.form.get("year", current_year))

        # Create a clean response dictionary mapping question IDs to submitted answers
        responses = {}
        for key, value in request.form.items():
            if key.startswith("response_"):
                q_id = key.split("response_")[1]
                responses[q_id] = value

        if str(year) not in session["responses_by_year"]:
            session["responses_by_year"][str(year)] = {}

        session["responses_by_year"][str(year)] = responses

        if request.form.get("upload_excel") == "true":
            file = request.files.get("excel_file")

            if file and file.filename.endswith('.xlsx'):
                new_resp = excel_upload(file, responses_by_year)
                print(new_resp)
                session_responses(new_resp)
            
            # fill in open responses on page load
            responses = session['responses_by_year'].get(current_year, {})

            return render_template("data_input.html", questions=sec_questions,
                           responses=responses, current_year=current_year)

        if request.form.get("download_excel") == "true":
            """current_responses = request.form.getlist('responses')
            responses_by_year[current_year] = {
                q_id: resp for q_id, resp in zip(questions.keys(), current_responses)
            }"""

            session_responses(responses_by_year)

            return excel_download(session['responses_by_year'])

        if 'change_year' in request.form:
            """
            # save current responses before switching years
            current_responses = request.form.getlist('responses')

            print(f"CURR for {current_year}:")
            print(current_responses)
            responses_by_year[current_year] = {
                q_id: resp for q_id, resp in zip(questions.keys(), current_responses)
            }

            session_responses(responses_by_year)
            """

            # change year
            current_year = int(current_year)
            if request.form['change_year'] == 'prev':
                current_year -= 1
            elif request.form['change_year'] == 'next':
                current_year += 1
            current_year = str(current_year)

            # update year
            session['current_year'] = current_year
            print(responses_by_year)

        else:
            year = int(request.form.get("year", current_year))

            responses = {}
            for key, value in request.form.items():
                if key.startswith("response_"):
                    q_id = key.split("response_")[1]
                    responses[q_id] = value

            if str(year) not in session["responses_by_year"]:
                session["responses_by_year"][str(year)] = {}

            session["responses_by_year"][str(year)] = responses
            session["responses_by_year"] = clean_responses(session["responses_by_year"])

            # -- 
            """
            # save responses for the current year
            current_responses = request.form.getlist('responses') # 18 for energy
            year_key = request.form['year']
            
            responses_by_year[year_key] = {
                q_id: resp for q_id, resp in zip(sec_questions.keys(), current_responses)
            }

            session_responses(clean_responses(responses_by_year))
            """

            return redirect(url_for("analysis.analysis_page"))

    # retrieve the responses for the current year (if any)
    responses = responses_by_year.get(str(current_year), {})
    # ensure session updated
    session_responses(responses_by_year)

    return render_template("data_input.html", questions=sec_questions,
                           responses=responses, current_year=current_year)