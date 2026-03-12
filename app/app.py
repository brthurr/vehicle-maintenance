"""
app.py
------
Flask application factory and all route handlers for the
Vehicle Maintenance Tracker.

Routes
------
GET  /                          – dashboard / vehicle list
GET  /vehicles/add              – add-vehicle form
POST /vehicles/add              – create vehicle
GET  /vehicles/<id>             – vehicle detail + log list
GET  /vehicles/<id>/edit        – edit vehicle form
POST /vehicles/<id>/edit        – update vehicle
POST /vehicles/<id>/delete      – delete vehicle
GET  /vehicles/<id>/log/add     – add maintenance log form
POST /vehicles/<id>/log/add     – create maintenance log + optional receipt upload
GET  /log/<id>                  – log detail with receipts
POST /log/<id>/delete           – delete log
GET  /receipts/<id>/download    – download a receipt file
POST /receipts/<id>/delete      – delete a receipt
GET  /maintenance-types         – list and manage maintenance types
POST /maintenance-types/add     – add a custom type
POST /maintenance-types/<id>/delete – delete a type
GET  /reports                   – cost and interval summary report
"""

import os
import uuid
from datetime import datetime, date
from flask import (
    Flask,
    render_template_string,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
    abort,
)
from werkzeug.utils import secure_filename

from .database import get_connection, init_db, seed_maintenance_types, DB_PATH
from .templates import (
    BASE_TEMPLATE,
    DASHBOARD_TEMPLATE,
    VEHICLE_FORM_TEMPLATE,
    VEHICLE_DETAIL_TEMPLATE,
    LOG_FORM_TEMPLATE,
    LOG_DETAIL_TEMPLATE,
    TYPES_TEMPLATE,
    REPORTS_TEMPLATE,
)

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename: str) -> bool:
    """Return True if the file extension is in the allowed set."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def create_app(db_path: str = DB_PATH, upload_folder: str = "uploads") -> Flask:
    """
    Application factory.

    Parameters
    ----------
    db_path       : path to the SQLite database file
    upload_folder : directory where receipt files are stored

    Returns
    -------
    A configured Flask application instance.
    """
    app = Flask(__name__, instance_relative_config=False)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    app.config["UPLOAD_FOLDER"] = upload_folder
    app.config["DB_PATH"] = db_path
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload

    os.makedirs(upload_folder, exist_ok=True)

    # Initialise schema and seed default maintenance types
    init_db(db_path)
    seed_maintenance_types(db_path)

    # ------------------------------------------------------------------ #
    #  Helper
    # ------------------------------------------------------------------ #
    def db():
        """Return a connection to the application database."""
        return get_connection(app.config["DB_PATH"])

    # ------------------------------------------------------------------ #
    #  Dashboard
    # ------------------------------------------------------------------ #
    @app.route("/")
    def dashboard():
        conn = db()
        vehicles = conn.execute(
            "SELECT * FROM vehicles ORDER BY name"
        ).fetchall()

        # For each vehicle, grab last log date and upcoming services
        vehicle_data = []
        for v in vehicles:
            last_log = conn.execute(
                """SELECT ml.service_date, mt.name AS type_name
                   FROM maintenance_logs ml
                   JOIN maintenance_types mt ON mt.id = ml.type_id
                   WHERE ml.vehicle_id = ?
                   ORDER BY ml.service_date DESC, ml.id DESC
                   LIMIT 1""",
                (v["id"],),
            ).fetchone()

            overdue = conn.execute(
                """SELECT COUNT(*) AS cnt
                   FROM maintenance_logs ml
                   WHERE ml.vehicle_id = ?
                     AND ml.next_due_miles IS NOT NULL
                     AND ml.next_due_miles <= ?""",
                (v["id"], v["mileage"]),
            ).fetchone()["cnt"]

            vehicle_data.append(
                {"vehicle": dict(v), "last_log": last_log, "overdue": overdue}
            )

        conn.close()
        return render_template_string(
            DASHBOARD_TEMPLATE, vehicles=vehicle_data, base=BASE_TEMPLATE
        )

    # ------------------------------------------------------------------ #
    #  Vehicles – CRUD
    # ------------------------------------------------------------------ #
    @app.route("/vehicles/add", methods=["GET", "POST"])
    def add_vehicle():
        if request.method == "POST":
            name  = request.form.get("name", "").strip()
            make  = request.form.get("make", "").strip()
            model = request.form.get("model", "").strip()
            year  = request.form.get("year", "").strip()
            vin   = request.form.get("vin", "").strip()
            mileage = request.form.get("mileage", "0").strip()
            vtype = request.form.get("vehicle_type", "Car/Truck").strip()

            errors = []
            if not name:  errors.append("Nickname is required.")
            if not make:  errors.append("Make is required.")
            if not model: errors.append("Model is required.")
            if not year.isdigit() or not (1885 <= int(year) <= date.today().year + 2):
                errors.append("Please enter a valid 4-digit year.")
            if not mileage.isdigit():
                errors.append("Mileage must be a whole number.")

            if errors:
                for e in errors:
                    flash(e, "error")
                return render_template_string(
                    VEHICLE_FORM_TEMPLATE, base=BASE_TEMPLATE, vehicle=None
                )

            conn = db()
            with conn:
                conn.execute(
                    """INSERT INTO vehicles (name, make, model, year, vin, mileage, vehicle_type)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (name, make, model, int(year), vin or None, int(mileage), vtype),
                )
            conn.close()
            flash(f"Vehicle '{name}' added successfully.", "success")
            return redirect(url_for("dashboard"))

        return render_template_string(
            VEHICLE_FORM_TEMPLATE, base=BASE_TEMPLATE, vehicle=None
        )

    @app.route("/vehicles/<int:vehicle_id>")
    def vehicle_detail(vehicle_id):
        conn = db()
        vehicle = conn.execute(
            "SELECT * FROM vehicles WHERE id = ?", (vehicle_id,)
        ).fetchone()
        if not vehicle:
            conn.close()
            abort(404)

        logs = conn.execute(
            """SELECT ml.*, mt.name AS type_name,
                      (SELECT COUNT(*) FROM receipts r WHERE r.log_id = ml.id) AS receipt_count
               FROM maintenance_logs ml
               JOIN maintenance_types mt ON mt.id = ml.type_id
               WHERE ml.vehicle_id = ?
               ORDER BY ml.service_date DESC, ml.id DESC""",
            (vehicle_id,),
        ).fetchall()

        upcoming = conn.execute(
            """SELECT ml.next_due_miles, ml.next_due_date, mt.name AS type_name
               FROM maintenance_logs ml
               JOIN maintenance_types mt ON mt.id = ml.type_id
               WHERE ml.vehicle_id = ?
                 AND (ml.next_due_miles IS NOT NULL OR ml.next_due_date IS NOT NULL)
               ORDER BY ml.next_due_date, ml.next_due_miles""",
            (vehicle_id,),
        ).fetchall()

        conn.close()
        return render_template_string(
            VEHICLE_DETAIL_TEMPLATE,
            base=BASE_TEMPLATE,
            vehicle=dict(vehicle),
            logs=logs,
            upcoming=upcoming,
        )

    @app.route("/vehicles/<int:vehicle_id>/edit", methods=["GET", "POST"])
    def edit_vehicle(vehicle_id):
        conn = db()
        vehicle = conn.execute(
            "SELECT * FROM vehicles WHERE id = ?", (vehicle_id,)
        ).fetchone()
        if not vehicle:
            conn.close()
            abort(404)

        if request.method == "POST":
            name    = request.form.get("name", "").strip()
            make    = request.form.get("make", "").strip()
            model   = request.form.get("model", "").strip()
            year    = request.form.get("year", "").strip()
            vin     = request.form.get("vin", "").strip()
            mileage = request.form.get("mileage", "0").strip()
            vtype   = request.form.get("vehicle_type", "Car/Truck").strip()

            errors = []
            if not name:  errors.append("Nickname is required.")
            if not make:  errors.append("Make is required.")
            if not model: errors.append("Model is required.")
            if not year.isdigit() or not (1885 <= int(year) <= date.today().year + 2):
                errors.append("Please enter a valid 4-digit year.")
            if not mileage.isdigit():
                errors.append("Mileage must be a whole number.")

            if errors:
                for e in errors:
                    flash(e, "error")
                return render_template_string(
                    VEHICLE_FORM_TEMPLATE, base=BASE_TEMPLATE, vehicle=dict(vehicle)
                )

            with conn:
                conn.execute(
                    """UPDATE vehicles
                       SET name=?, make=?, model=?, year=?, vin=?, mileage=?, vehicle_type=?
                       WHERE id=?""",
                    (name, make, model, int(year), vin or None, int(mileage), vtype, vehicle_id),
                )
            conn.close()
            flash("Vehicle updated.", "success")
            return redirect(url_for("vehicle_detail", vehicle_id=vehicle_id))

        conn.close()
        return render_template_string(
            VEHICLE_FORM_TEMPLATE, base=BASE_TEMPLATE, vehicle=dict(vehicle)
        )

    @app.route("/vehicles/<int:vehicle_id>/delete", methods=["POST"])
    def delete_vehicle(vehicle_id):
        conn = db()
        vehicle = conn.execute(
            "SELECT name FROM vehicles WHERE id = ?", (vehicle_id,)
        ).fetchone()
        if vehicle:
            with conn:
                conn.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
            flash(f"Vehicle '{vehicle['name']}' deleted.", "success")
        conn.close()
        return redirect(url_for("dashboard"))

    # ------------------------------------------------------------------ #
    #  Maintenance Logs
    # ------------------------------------------------------------------ #
    @app.route("/vehicles/<int:vehicle_id>/log/add", methods=["GET", "POST"])
    def add_log(vehicle_id):
        conn = db()
        vehicle = conn.execute(
            "SELECT * FROM vehicles WHERE id = ?", (vehicle_id,)
        ).fetchone()
        if not vehicle:
            conn.close()
            abort(404)

        mtypes = conn.execute(
            "SELECT * FROM maintenance_types ORDER BY name"
        ).fetchall()

        if request.method == "POST":
            type_id  = request.form.get("type_id", "").strip()
            sdate    = request.form.get("service_date", "").strip()
            mileage  = request.form.get("mileage_at_service", "").strip()
            notes    = request.form.get("notes", "").strip()
            cost     = request.form.get("cost", "").strip()
            nxt_mi   = request.form.get("next_due_miles", "").strip()
            nxt_dt   = request.form.get("next_due_date", "").strip()
            receipt  = request.files.get("receipt")

            errors = []
            if not type_id.isdigit(): errors.append("Please select a service type.")
            if not sdate:             errors.append("Service date is required.")
            if not mileage.isdigit(): errors.append("Mileage must be a whole number.")

            cost_val   = None
            nxt_mi_val = None
            if cost:
                try:
                    cost_val = float(cost)
                except ValueError:
                    errors.append("Cost must be a number.")
            if nxt_mi:
                if nxt_mi.isdigit():
                    nxt_mi_val = int(nxt_mi)
                else:
                    errors.append("Next due mileage must be a whole number.")

            if errors:
                for e in errors:
                    flash(e, "error")
                conn.close()
                return render_template_string(
                    LOG_FORM_TEMPLATE,
                    base=BASE_TEMPLATE,
                    vehicle=dict(vehicle),
                    mtypes=mtypes,
                )

            # Insert log
            with conn:
                cursor = conn.execute(
                    """INSERT INTO maintenance_logs
                       (vehicle_id, type_id, service_date, mileage_at_service,
                        notes, cost, next_due_miles, next_due_date)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        vehicle_id,
                        int(type_id),
                        sdate,
                        int(mileage),
                        notes or None,
                        cost_val,
                        nxt_mi_val,
                        nxt_dt or None,
                    ),
                )
                log_id = cursor.lastrowid

                # Update vehicle mileage if higher than current
                conn.execute(
                    "UPDATE vehicles SET mileage = MAX(mileage, ?) WHERE id = ?",
                    (int(mileage), vehicle_id),
                )

            # Handle receipt upload
            if receipt and receipt.filename and allowed_file(receipt.filename):
                original_name = secure_filename(receipt.filename)
                ext = original_name.rsplit(".", 1)[1].lower()
                stored_name = f"{uuid.uuid4().hex}.{ext}"
                receipt.save(os.path.join(app.config["UPLOAD_FOLDER"], stored_name))
                with conn:
                    conn.execute(
                        "INSERT INTO receipts (log_id, filename, stored_name) VALUES (?, ?, ?)",
                        (log_id, original_name, stored_name),
                    )
            elif receipt and receipt.filename and not allowed_file(receipt.filename):
                flash("Receipt not saved – unsupported file type.", "warning")

            conn.close()
            flash("Maintenance log added.", "success")
            return redirect(url_for("vehicle_detail", vehicle_id=vehicle_id))

        conn.close()
        return render_template_string(
            LOG_FORM_TEMPLATE,
            base=BASE_TEMPLATE,
            vehicle=dict(vehicle),
            mtypes=mtypes,
        )

    @app.route("/log/<int:log_id>")
    def log_detail(log_id):
        conn = db()
        log = conn.execute(
            """SELECT ml.*, mt.name AS type_name, v.name AS vehicle_name,
                      v.id AS vehicle_id
               FROM maintenance_logs ml
               JOIN maintenance_types mt ON mt.id = ml.type_id
               JOIN vehicles v ON v.id = ml.vehicle_id
               WHERE ml.id = ?""",
            (log_id,),
        ).fetchone()
        if not log:
            conn.close()
            abort(404)

        receipts = conn.execute(
            "SELECT * FROM receipts WHERE log_id = ? ORDER BY uploaded_at",
            (log_id,),
        ).fetchall()
        conn.close()
        return render_template_string(
            LOG_DETAIL_TEMPLATE,
            base=BASE_TEMPLATE,
            log=dict(log),
            receipts=receipts,
        )

    @app.route("/log/<int:log_id>/delete", methods=["POST"])
    def delete_log(log_id):
        conn = db()
        log = conn.execute(
            "SELECT vehicle_id FROM maintenance_logs WHERE id = ?", (log_id,)
        ).fetchone()
        if log:
            vehicle_id = log["vehicle_id"]
            # Delete stored receipt files
            receipts = conn.execute(
                "SELECT stored_name FROM receipts WHERE log_id = ?", (log_id,)
            ).fetchall()
            for r in receipts:
                fpath = os.path.join(app.config["UPLOAD_FOLDER"], r["stored_name"])
                if os.path.exists(fpath):
                    os.remove(fpath)
            with conn:
                conn.execute("DELETE FROM maintenance_logs WHERE id = ?", (log_id,))
            conn.close()
            flash("Log deleted.", "success")
            return redirect(url_for("vehicle_detail", vehicle_id=vehicle_id))
        conn.close()
        abort(404)

    # ------------------------------------------------------------------ #
    #  Receipts
    # ------------------------------------------------------------------ #
    @app.route("/receipts/<int:receipt_id>/download")
    def download_receipt(receipt_id):
        conn = db()
        receipt = conn.execute(
            "SELECT * FROM receipts WHERE id = ?", (receipt_id,)
        ).fetchone()
        conn.close()
        if not receipt:
            abort(404)
        return send_from_directory(
            app.config["UPLOAD_FOLDER"],
            receipt["stored_name"],
            as_attachment=True,
            download_name=receipt["filename"],
        )

    @app.route("/receipts/<int:receipt_id>/delete", methods=["POST"])
    def delete_receipt(receipt_id):
        conn = db()
        receipt = conn.execute(
            """SELECT r.*, ml.id AS log_id
               FROM receipts r
               JOIN maintenance_logs ml ON ml.id = r.log_id
               WHERE r.id = ?""",
            (receipt_id,),
        ).fetchone()
        if receipt:
            fpath = os.path.join(app.config["UPLOAD_FOLDER"], receipt["stored_name"])
            if os.path.exists(fpath):
                os.remove(fpath)
            with conn:
                conn.execute("DELETE FROM receipts WHERE id = ?", (receipt_id,))
            conn.close()
            flash("Receipt deleted.", "success")
            return redirect(url_for("log_detail", log_id=receipt["log_id"]))
        conn.close()
        abort(404)

    # ------------------------------------------------------------------ #
    #  Maintenance Types
    # ------------------------------------------------------------------ #
    @app.route("/maintenance-types")
    def maintenance_types():
        conn = db()
        mtypes = conn.execute(
            "SELECT * FROM maintenance_types ORDER BY name"
        ).fetchall()
        conn.close()
        return render_template_string(
            TYPES_TEMPLATE, base=BASE_TEMPLATE, mtypes=mtypes
        )

    @app.route("/maintenance-types/add", methods=["POST"])
    def add_maintenance_type():
        name    = request.form.get("name", "").strip()
        desc    = request.form.get("description", "").strip()
        i_miles = request.form.get("interval_miles", "").strip()
        i_mos   = request.form.get("interval_months", "").strip()

        if not name:
            flash("Type name is required.", "error")
            return redirect(url_for("maintenance_types"))

        im = int(i_miles) if i_miles.isdigit() else None
        imo = int(i_mos)  if i_mos.isdigit()  else None

        conn = db()
        try:
            with conn:
                conn.execute(
                    """INSERT INTO maintenance_types
                       (name, description, interval_miles, interval_months)
                       VALUES (?, ?, ?, ?)""",
                    (name, desc or None, im, imo),
                )
            flash(f"Type '{name}' added.", "success")
        except Exception:
            flash("A type with that name already exists.", "error")
        finally:
            conn.close()
        return redirect(url_for("maintenance_types"))

    @app.route("/maintenance-types/<int:type_id>/delete", methods=["POST"])
    def delete_maintenance_type(type_id):
        conn = db()
        mtype = conn.execute(
            "SELECT name FROM maintenance_types WHERE id = ?", (type_id,)
        ).fetchone()
        if mtype:
            in_use = conn.execute(
                "SELECT COUNT(*) AS c FROM maintenance_logs WHERE type_id = ?", (type_id,)
            ).fetchone()["c"]
            if in_use:
                flash("Cannot delete – this type is used by existing logs.", "error")
            else:
                with conn:
                    conn.execute(
                        "DELETE FROM maintenance_types WHERE id = ?", (type_id,)
                    )
                flash(f"Type '{mtype['name']}' deleted.", "success")
        conn.close()
        return redirect(url_for("maintenance_types"))

    # ------------------------------------------------------------------ #
    #  Reports
    # ------------------------------------------------------------------ #
    @app.route("/reports")
    def reports():
        vehicle_id = request.args.get("vehicle_id", type=int)
        conn = db()
        vehicles = conn.execute(
            "SELECT * FROM vehicles ORDER BY name"
        ).fetchall()

        cost_by_type = []
        total_cost   = 0
        log_count    = 0

        query_filter = "WHERE ml.vehicle_id = ?" if vehicle_id else ""
        params = (vehicle_id,) if vehicle_id else ()

        cost_by_type = conn.execute(
            f"""SELECT mt.name, COUNT(*) AS cnt, SUM(ml.cost) AS total,
                       AVG(ml.cost) AS avg_cost
                FROM maintenance_logs ml
                JOIN maintenance_types mt ON mt.id = ml.type_id
                {query_filter}
                GROUP BY mt.name
                ORDER BY total DESC""",
            params,
        ).fetchall()

        totals = conn.execute(
            f"""SELECT COUNT(*) AS cnt, SUM(cost) AS total
                FROM maintenance_logs ml {query_filter}""",
            params,
        ).fetchone()

        log_count  = totals["cnt"]
        total_cost = totals["total"] or 0

        recent_logs = conn.execute(
            f"""SELECT ml.service_date, v.name AS vehicle_name,
                       mt.name AS type_name, ml.cost, ml.mileage_at_service
                FROM maintenance_logs ml
                JOIN vehicles v  ON v.id  = ml.vehicle_id
                JOIN maintenance_types mt ON mt.id = ml.type_id
                {query_filter}
                ORDER BY ml.service_date DESC, ml.id DESC
                LIMIT 20""",
            params,
        ).fetchall()

        conn.close()
        return render_template_string(
            REPORTS_TEMPLATE,
            base=BASE_TEMPLATE,
            vehicles=vehicles,
            selected_vehicle_id=vehicle_id,
            cost_by_type=cost_by_type,
            total_cost=total_cost,
            log_count=log_count,
            recent_logs=recent_logs,
        )

    return app
