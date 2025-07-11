from flask import Blueprint, render_template, session
from .questions import compute_indices
import pandas as pd
import os
import subprocess
from . import get_db

analysis = Blueprint("analysis", __name__)

@analysis.route("/analysis", methods=["GET", "POST"])
def analysis_page():
    responses = session.get("responses_by_year")
    if not responses:
        return render_template("analysis.html")

    # index values
    year_index_data = {}
    for year, yr_responses in responses.items():
        try:
            indexes = compute_indices(yr_responses)
            year_index_data[year] = indexes
        except Exception as e:
            print(f"Error computing indexes for {year}: {e}")

    if not year_index_data:
        return render_template("analysis.html")

    # ensure bounds
    for year, index_dict in year_index_data.items():
        for key in index_dict:
            value = index_dict[key]
            # clamp
            index_dict[key] = max(min(value, 1), 0)

    # df and ce index
    df = pd.DataFrame.from_dict(year_index_data, orient='index')
    df.index.name = 'year'
    df = df.sort_index()
    df["CE_Index"] = df.mean(axis=1)

    # add to table
    if "assessment_id" in session:
        avg_score = float(round(df["CE_Index"].mean(), 4)) # numpy float64 to float
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "UPDATE assessments SET score = %s WHERE id = %s",
            (avg_score, session["assessment_id"])
        )
        db.commit()

    # save to csv for plots.R
    base_dir = os.path.dirname(__file__)
    static_dir = os.path.join(base_dir, "static")
    os.makedirs(static_dir, exist_ok=True)

    csv_path = os.path.join(static_dir, "index_data.csv")
    df.reset_index().to_csv(csv_path, index=False)

    # Year to use for radar plot
    if str(session["current_year"]) in year_index_data:
        radar_year = str(session["current_year"])
    else: # if user visualizes on a year with no data, pick latest that has data
        radar_year = max(year_index_data.keys())

    # other plots.R args
    r_script_path = os.path.join(base_dir, "plots.R")
    csv_path = os.path.join(static_dir, "index_data.csv")

    try:
        subprocess.run(["Rscript", r_script_path, csv_path, static_dir, radar_year], check=True)
    except subprocess.CalledProcessError as e:
        print("R script failed:", e)
        return render_template("analysis.html", error="Failed to generate plots")
    
    # render with new plots
    return render_template("analysis.html", current_year = radar_year)
