import os
import csv
import io
from datetime import datetime, date
from argparse import ArgumentParser

from flask import Flask, render_template, request, redirect, url_for, flash, send_file, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy

# --- Config ---
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///blood_bank.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# --- Models ---
class Donor(db.Model):
    __tablename__ = "donors"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    blood_group = db.Column(db.String(3), nullable=False)  # e.g., A+, O-
    last_donation = db.Column(db.Date, nullable=True)

class Donation(db.Model):
    __tablename__ = "donations"
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey("donors.id"), nullable=True)
    blood_group = db.Column(db.String(3), nullable=False)
    units = db.Column(db.Integer, nullable=False, default=1)
    date = db.Column(db.Date, nullable=False, default=date.today)
    donor = db.relationship("Donor", backref="donations")

class Stock(db.Model):
    __tablename__ = "stock"
    blood_group = db.Column(db.String(3), primary_key=True)
    units = db.Column(db.Integer, nullable=False, default=0)
    threshold = db.Column(db.Integer, nullable=False, default=5)

# --- Helpers ---
ALL_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

def ensure_stock_rows():
    for g in ALL_GROUPS:
        if not Stock.query.get(g):
            db.session.add(Stock(blood_group=g, units=0, threshold=5))
    db.session.commit()

def group_stock_dict():
    rows = Stock.query.order_by(Stock.blood_group).all()
    return {r.blood_group: r.units for r in rows}

def low_stock_list():
    rows = Stock.query.order_by(Stock.blood_group).all()
    return [r for r in rows if r.units <= r.threshold]

# --- Routes ---
@app.route("/")
def dashboard():
    ensure_stock_rows()
    stock = Stock.query.order_by(Stock.blood_group).all()
    alerts = low_stock_list()
    # Chart data
    labels = ALL_GROUPS
    data = [next((s.units for s in stock if s.blood_group == g), 0) for g in labels]
    return render_template("dashboard.html", stock=stock, alerts=alerts, labels=labels, data=data)

@app.route("/donors", methods=["GET", "POST"])
def donors():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        group = request.form.get("blood_group")
        last = request.form.get("last_donation") or None
        if not name or group not in ALL_GROUPS:
            flash("Please provide a valid name and blood group.", "danger")
            return redirect(url_for("donors"))
        last_dt = datetime.strptime(last, "%Y-%m-%d").date() if last else None
        d = Donor(name=name, blood_group=group, last_donation=last_dt)
        db.session.add(d)
        db.session.commit()
        flash("Donor added.", "success")
        return redirect(url_for("donors"))

    # --- Search + Filter + Pagination ---
    search = request.args.get("search", "").strip()
    group = request.args.get("group", "")
    page = request.args.get("page", 1, type=int)

    query = Donor.query
    if search:
        query = query.filter(Donor.name.ilike(f"%{search}%"))
    if group and group in ALL_GROUPS:
        query = query.filter(Donor.blood_group == group)

    donors = query.order_by(Donor.name).paginate(page=page, per_page=10)

    return render_template(
        "donors.html",
        donors=donors,
        groups=ALL_GROUPS,
        search=search,
        group=group
    )

from datetime import datetime

@app.route("/donate", methods=["GET", "POST"])
def donate():
    if request.method == "POST":
        donor_id = request.form.get("donor_id")
        blood_group = request.form["blood_group"]
        units = int(request.form["units"])
        date_input = request.form.get("date")

        # agar date khali hai to today use karo
        if not date_input:
            donation_date = date.today()
        else:
            donation_date = datetime.strptime(date_input, "%Y-%m-%d").date()

        # donor fetch karo (agar none select hua hai to None pass karna hai)
        donor = None
        if donor_id and donor_id != "none":
            donor = Donor.query.get(int(donor_id))

        donation = Donation(
            donor_id=donor.id if donor else None,
            blood_group=blood_group,
            units=units,
            date=donation_date
        )
        db.session.add(donation)

        # stock update
        stock = Stock.query.get(blood_group)
        stock.units += units
        db.session.commit()

        flash("Donation recorded successfully!", "success")
        return redirect(url_for("donations"))

    donors = Donor.query.all()
    today = date.today().strftime("%Y-%m-%d")
    return render_template("donate.html", donors=donors, groups=ALL_GROUPS, today=today)

@app.route("/donations")
def donations():
    all_donations = Donation.query.all()
    return render_template("donations.html", donations=all_donations)

@app.route("/use", methods=["GET", "POST"])
def use():
    if request.method == "POST":
        group = request.form.get("blood_group")
        units = int(request.form.get("units", "1"))
        if group not in ALL_GROUPS:
            flash("Please select a valid blood group.", "danger")
            return redirect(url_for("use"))
        ensure_stock_rows()
        s = Stock.query.get(group)
        if s.units < units:
            flash("Not enough stock to issue.", "danger")
            return redirect(url_for("use"))
        s.units -= units
        db.session.commit()
        flash(f"Issued {units} unit(s) of {group}.", "success")
        return redirect(url_for("dashboard"))
    return render_template("use.html", groups=ALL_GROUPS)

@app.route("/export/donors.csv")
def export_donors():
    donors = Donor.query.order_by(Donor.name).all()
    proxy = io.StringIO()
    writer = csv.writer(proxy)
    writer.writerow(["id", "name", "blood_group", "last_donation"])
    for d in donors:
        writer.writerow([d.id, d.name, d.blood_group, d.last_donation.isoformat() if d.last_donation else ""])
    mem = io.BytesIO()
    mem.write(proxy.getvalue().encode("utf-8"))
    mem.seek(0)
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name="donors.csv")

@app.route("/report/pdf")
def report_pdf():
    # Generate a simple PDF with stock and alerts
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import inch

    ensure_stock_rows()
    stock = Stock.query.order_by(Stock.blood_group).all()
    alerts = low_stock_list()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title="Blood Bank Status Report")
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Blood Bank Status Report", styles["Title"]))
    elements.append(Paragraph(datetime.now().strftime("%Y-%m-%d %H:%M"), styles["Normal"]))
    elements.append(Spacer(1, 0.2*inch))

    # Stock table
    data = [["Blood Group", "Units", "Threshold", "Status"]]
    for s in stock:
        status = "LOW" if s.units <= s.threshold else "OK"
        data.append([s.blood_group, str(s.units), str(s.threshold), status])
    tbl = Table(data, hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ALIGN", (1,1), (-1,-1), "CENTER"),
    ]))
    elements.append(Paragraph("Stock Summary", styles["Heading2"]))
    elements.append(tbl)
    elements.append(Spacer(1, 0.2*inch))

    # Alerts
    elements.append(Paragraph("Low Stock Alerts", styles["Heading2"]))
    if alerts:
        for a in alerts:
            elements.append(Paragraph(f"{a.blood_group}: {a.units} units (<= threshold {a.threshold})", styles["Normal"]))
    else:
        elements.append(Paragraph("No low stock alerts.", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, mimetype="application/pdf", as_attachment=True, download_name="blood_bank_report.pdf")

# --- Init DB ---
def init_db():
    db.drop_all()
    db.create_all()
    ensure_stock_rows()

    # Seed donors
    rahul = Donor(name="Rahul", blood_group="A+", last_donation=datetime.strptime("2025-06-25", "%Y-%m-%d").date())
    sneha = Donor(name="Sneha", blood_group="O-", last_donation=datetime.strptime("2025-07-01", "%Y-%m-%d").date())
    db.session.add_all([rahul, sneha])
    db.session.commit()

    # Seed one donation for Rahul on 2025-07-01 (1 unit)
    donation = Donation(donor_id=rahul.id, blood_group="A+", units=1, date=datetime.strptime("2025-07-01", "%Y-%m-%d").date())
    db.session.add(donation)
    # Update stock: A+ +1, O- +1 sample baseline
    aplus = Stock.query.get("A+"); aplus.units += 1
    oneg = Stock.query.get("O-"); oneg.units += 1
    db.session.commit()
    print("Database initialized with sample data.")

    @app.route("/dashboard")
    def dashboard():
     stocks = Stock.query.all()
     low_stock_alerts = [s for s in stocks if s.units < 5]  # threshold = 5

    return render_template(
        "dashboard.html",
        stocks=stocks,
        low_stock_alerts=low_stock_alerts
    )



if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--initdb", action="store_true", help="Recreate and seed the database")
    args = parser.parse_args()
    if args.initdb:
        with app.app_context():
            init_db()
    else:
        app.run(debug=True)
