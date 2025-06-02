from flask import Blueprint, render_template, request, redirect, url_for, session

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
def index():
    if request.method == "POST":
        company_id = request.form.get("company_id")
        sector = request.form.get("sector")
        industry = request.form.get("industry")

        # TODO: CHANGE LATER, JUST FOR PROTOTYPE:
        if sector == "Energy":
            sector = "Energy&Utilities"

        session['company_id'] = company_id
        session['sector'] = sector

        return redirect(url_for("data_input.data_input_page", sector=sector, industry=industry))
    return render_template("index.html", industries=INDUSTRIES)