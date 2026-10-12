import os
import sqlite3
import threading
import time
from datetime import datetime, timedelta

import requests
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
from twilio.rest import Client


# ============================================================
# FLASK CONFIGURATION
# ============================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "cropshield-secret-key-2026"
)

DATABASE = "cropshield.db"


# ============================================================
# CROP DATA
# ============================================================

CROPS = [
    "Paddy",
    "Tomato",
    "Chilli",
    "Cotton",
    "Maize",
    "Groundnut",
    "Cucumber",
    "Capsicum",
    "Brinjal",
    "Wheat",
    "Other"
]

GROWTH_STAGES = [
    "Seedling",
    "Vegetative",
    "Flowering",
    "Fruiting / Grain Filling",
    "Mature / Harvest"
]


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

def init_db():

    conn = get_db()
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # FARMS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS farms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            farm_name TEXT NOT NULL,
            method TEXT NOT NULL,
            location TEXT NOT NULL,
            crop TEXT NOT NULL,
            growth_stage TEXT NOT NULL,
            threshold REAL NOT NULL,
            created_at TEXT NOT NULL,

            FOREIGN KEY (user_id)
            REFERENCES users(id)
        )
    """)

    # ALERTS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            farm_id INTEGER NOT NULL,
            farm_name TEXT NOT NULL,
            crop TEXT NOT NULL,
            temperature REAL NOT NULL,
            threshold REAL NOT NULL,
            created_at TEXT NOT NULL,

            FOREIGN KEY (user_id)
            REFERENCES users(id),

            FOREIGN KEY (farm_id)
            REFERENCES farms(id)
        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    # If user is already logged in,
    # take them directly to dashboard.
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return render_template(
        "index.html",
        page="home"
    )


# ============================================================
# REGISTER
# ============================================================

@app.route("/register", methods=["POST"])
def register():

    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "").strip()

    # Greenhouse/Open Field selection from home page.
    # The account can manage both, so this is only stored
    # temporarily during registration.
    method = request.form.get(
        "method",
        "Open Field"
    )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not name:
        flash(
            "Please enter your name.",
            "error"
        )
        return redirect(url_for("home"))

    if not phone:
        flash(
            "Please enter your mobile number.",
            "error"
        )
        return redirect(url_for("home"))

    if len(password) < 8:
        flash(
            "Password must be at least 8 characters.",
            "error"
        )
        return redirect(url_for("home"))

    # --------------------------------------------------------
    # CHECK EXISTING USER
    # --------------------------------------------------------

    conn = get_db()

    existing_user = conn.execute(
        """
        SELECT id
        FROM users
        WHERE phone = ?
        """,
        (phone,)
    ).fetchone()

    if existing_user:

        conn.close()

        flash(
            "This mobile number is already registered. Please login.",
            "error"
        )

        return redirect(url_for("home"))

    # --------------------------------------------------------
    # HASH PASSWORD
    # --------------------------------------------------------

    password_hash = generate_password_hash(password)

    # --------------------------------------------------------
    # CREATE USER
    # --------------------------------------------------------

    cursor = conn.execute(
        """
        INSERT INTO users (
            name,
            phone,
            password,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            name,
            phone,
            password_hash,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )
    )

    user_id = cursor.lastrowid

    conn.commit()
    conn.close()

    # --------------------------------------------------------
    # LOGIN AUTOMATICALLY
    # --------------------------------------------------------

    session.clear()

    session["user_id"] = user_id
    session["user_name"] = name
    session["phone"] = phone

    flash(
        f"Account created successfully. Selected method: {method}",
        "success"
    )

    return redirect(
        url_for("dashboard")
    )


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["POST"])
def login():

    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "").strip()

    if not phone or not password:

        flash(
            "Please enter your mobile number and password.",
            "error"
        )

        return redirect(url_for("home"))

    conn = get_db()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE phone = ?
        """,
        (phone,)
    ).fetchone()

    conn.close()

    # User does not exist
    if user is None:

        flash(
            "Account not found. Please create an account first.",
            "error"
        )

        return redirect(url_for("home"))

    # Wrong password
    if not check_password_hash(
        user["password"],
        password
    ):

        flash(
            "Incorrect password.",
            "error"
        )

        return redirect(url_for("home"))

    # --------------------------------------------------------
    # CREATE SESSION
    # --------------------------------------------------------

    session.clear()

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["phone"] = user["phone"]

    flash(
        "Login successful.",
        "success"
    )

    return redirect(
        url_for("dashboard")
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    # --------------------------------------------------------
    # LOGIN CHECK
    # --------------------------------------------------------

    if "user_id" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    user_id = session["user_id"]

    conn = get_db()

    # --------------------------------------------------------
    # GET USER
    # --------------------------------------------------------

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    # --------------------------------------------------------
    # GET FARMS
    # --------------------------------------------------------

    farms = conn.execute(
        """
        SELECT *
        FROM farms
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
    ).fetchall()

    # --------------------------------------------------------
    # GET ALERTS
    # --------------------------------------------------------

    alerts = conn.execute(
        """
        SELECT *
        FROM alerts
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 20
        """,
        (user_id,)
    ).fetchall()

    conn.close()

    if user is None:

        session.clear()

        flash(
            "User account not found.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    # --------------------------------------------------------
    # SEND DATA TO index.html
    # --------------------------------------------------------

    return render_template(
        "index.html",

        page="dashboard",

        user_name=user["name"],

        farms=farms,

        alerts=alerts,

        crops=CROPS,

        stages=GROWTH_STAGES
    )


# ============================================================
# ADD FARM
# ============================================================

@app.route("/farms", methods=["POST"])
def add_farm():

    # --------------------------------------------------------
    # LOGIN CHECK
    # --------------------------------------------------------

    if "user_id" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    # --------------------------------------------------------
    # READ FORM DATA
    # --------------------------------------------------------

    farm_name = request.form.get(
        "farm_name",
        ""
    ).strip()

    method = request.form.get(
        "method",
        ""
    ).strip()

    location = request.form.get(
        "location",
        ""
    ).strip()

    crop = request.form.get(
        "crop",
        ""
    ).strip()

    growth_stage = request.form.get(
        "growth_stage",
        ""
    ).strip()

    threshold_text = request.form.get(
        "threshold",
        ""
    ).strip()

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not farm_name:

        flash(
            "Please enter a farm name.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    if method not in [
        "Greenhouse",
        "Open Field"
    ]:

        flash(
            "Please select Greenhouse or Open Field.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    if not location:

        flash(
            "Please enter the farm location.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    if crop not in CROPS:

        flash(
            "Please select a valid crop.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    if growth_stage not in GROWTH_STAGES:

        flash(
            "Please select a valid growth stage.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    # Convert threshold to number
    try:

        threshold = float(threshold_text)

    except ValueError:

        flash(
            "Temperature threshold must be a number.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    # Check allowed range
    if threshold < 20 or threshold > 55:

        flash(
            "Temperature threshold must be between 20°C and 55°C.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    # --------------------------------------------------------
    # SAVE FARM
    # --------------------------------------------------------

    conn = get_db()

    conn.execute(
        """
        INSERT INTO farms (
            user_id,
            farm_name,
            method,
            location,
            crop,
            growth_stage,
            threshold,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session["user_id"],
            farm_name,
            method,
            location,
            crop,
            growth_stage,
            threshold,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )
    )

    conn.commit()
    conn.close()

    flash(
        f"{farm_name} added successfully.",
        "success"
    )

    return redirect(
        url_for("dashboard")
    )


# ============================================================
# EDIT FARM
# ============================================================

@app.route("/farms/<int:farm_id>/edit", methods=["POST"])
def edit_farm(farm_id):

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("home"))

    farm_name = request.form.get("farm_name", "").strip()
    method = request.form.get("method", "").strip()
    location = request.form.get("location", "").strip()
    crop = request.form.get("crop", "").strip()
    growth_stage = request.form.get("growth_stage", "").strip()
    threshold_text = request.form.get("threshold", "").strip()

    if not farm_name or method not in ["Greenhouse", "Open Field"] or not location \
            or crop not in CROPS or growth_stage not in GROWTH_STAGES:
        flash("Please enter valid farm details.", "error")
        return redirect(url_for("dashboard"))

    try:
        threshold = float(threshold_text)
    except ValueError:
        flash("Temperature threshold must be a number.", "error")
        return redirect(url_for("dashboard"))

    if threshold < 20 or threshold > 55:
        flash("Temperature threshold must be between 20°C and 55°C.", "error")
        return redirect(url_for("dashboard"))

    conn = get_db()
    cursor = conn.execute(
        """
        UPDATE farms
        SET farm_name = ?, method = ?, location = ?, crop = ?,
            growth_stage = ?, threshold = ?
        WHERE id = ? AND user_id = ?
        """,
        (farm_name, method, location, crop, growth_stage, threshold,
         farm_id, session["user_id"])
    )
    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        flash("Farm not found.", "error")
    else:
        flash(f"{farm_name} updated successfully.", "success")

    return redirect(url_for("dashboard"))


# ============================================================
# DELETE FARM
# ============================================================

@app.route("/farms/<int:farm_id>/delete", methods=["POST"])
def delete_farm(farm_id):

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("home"))

    conn = get_db()
    farm = conn.execute(
        "SELECT farm_name FROM farms WHERE id = ? AND user_id = ?",
        (farm_id, session["user_id"])
    ).fetchone()

    if farm is None:
        conn.close()
        flash("Farm not found.", "error")
        return redirect(url_for("dashboard"))

    # Remove the farm's alert history first because alerts reference farms.
    conn.execute(
        "DELETE FROM alerts WHERE farm_id = ? AND user_id = ?",
        (farm_id, session["user_id"])
    )
    conn.execute(
        "DELETE FROM farms WHERE id = ? AND user_id = ?",
        (farm_id, session["user_id"])
    )
    conn.commit()
    conn.close()

    flash(f"{farm['farm_name']} deleted successfully.", "success")
    return redirect(url_for("dashboard"))


# ============================================================
# GEOCODING
# ============================================================

def geocode_location(location):

    url = "https://geocoding-api.open-meteo.com/v1/search"

    params = {
        "name": location,
        "count": 1,
        "language": "en",
        "format": "json"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("results", [])

        if not results:
            return None

        result = results[0]

        return {
            "latitude": result.get("latitude"),
            "longitude": result.get("longitude"),
            "name": result.get(
                "name",
                location
            ),
            "state": result.get(
                "admin1",
                ""
            ),
            "country": result.get(
                "country",
                ""
            )
        }

    except requests.RequestException as error:

        print(
            "Geocoding error:",
            error
        )

        return None


# ============================================================
# GET WEATHER
# ============================================================

def get_weather(latitude, longitude):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "weather_code"
        ),
        "timezone": "auto"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        current = data.get("current")

        if not current:
            return None

        return {
            "temperature": current.get(
                "temperature_2m"
            ),
            "humidity": current.get(
                "relative_humidity_2m"
            ),
            "feels_like": current.get(
                "apparent_temperature"
            ),
            "weather_code": current.get(
                "weather_code"
            ),
            "time": current.get(
                "time"
            )
        }

    except requests.RequestException as error:

        print(
            "Weather API error:",
            error
        )

        return None


# ============================================================
# SAVE ALERT
# ============================================================

def save_alert(
    user_id,
    farm_id,
    farm_name,
    crop,
    temperature,
    threshold
):

    conn = get_db()

    conn.execute(
        """
        INSERT INTO alerts (
            user_id,
            farm_id,
            farm_name,
            crop,
            temperature,
            threshold,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            farm_id,
            farm_name,
            crop,
            temperature,
            threshold,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )
    )

    conn.commit()
    conn.close()


# ============================================================
# SEND SMS
# ============================================================

def send_sms(
    phone,
    farm_name,
    crop,
    temperature,
    threshold
):

    account_sid = os.environ.get(
        "TWILIO_ACCOUNT_SID"
    )

    auth_token = os.environ.get(
        "TWILIO_AUTH_TOKEN"
    )

    from_number = os.environ.get(
        "TWILIO_FROM_NUMBER"
    )

    # --------------------------------------------------------
    # DEMO MODE
    # --------------------------------------------------------

    if (
        not account_sid
        or not auth_token
        or not from_number
    ):

        print()
        print("=" * 60)
        print("CROPSHIELD DEMO SMS")
        print("=" * 60)
        print("TO:", phone)

        print(
            f"CropShield ALERT: {farm_name} - {crop}. "
            f"Temp {temperature:.1f}C >= limit {threshold:.1f}C. "
            f"Take heat protection measures now."
        )

        print("=" * 60)
        print()

        # Demo mode only prints the alert; it does not send an SMS.
        return False

    # --------------------------------------------------------
    # REAL TWILIO SMS
    # --------------------------------------------------------

    try:

        client = Client(
            account_sid,
            auth_token
        )

        message_body = (
            f"CropShield ALERT: {farm_name} - {crop}. "
            f"Temp {temperature:.1f}C >= limit {threshold:.1f}C. "
            f"Take heat protection measures now."
        )

        message = client.messages.create(
            body=message_body,
            from_=from_number,
            to=phone
        )

        print(
            "Twilio SMS sent successfully."
        )

        print(
            "Message SID:",
            message.sid
        )

        return True

    except Exception as error:

        print(
            "Twilio SMS error:",
            error
        )

        return False


# ============================================================
# AUTOMATIC WEATHER MONITORING
# ============================================================

AUTO_CHECK_INTERVAL_MINUTES = int(os.environ.get("CROPSHIELD_CHECK_MINUTES", "15"))
AUTO_ALERT_COOLDOWN_MINUTES = int(os.environ.get("CROPSHIELD_ALERT_COOLDOWN_MINUTES", "60"))


def check_farm_for_automatic_alert(farm):
    """Check one farm and send an alert without requiring a browser click."""
    location_data = geocode_location(farm["location"])
    if location_data is None:
        print(f"[AUTO] Could not geocode {farm['farm_name']} ({farm['location']}).")
        return

    weather_data = get_weather(location_data["latitude"], location_data["longitude"])
    if weather_data is None or weather_data["temperature"] is None:
        print(f"[AUTO] Could not get weather for {farm['farm_name']}.")
        return

    temperature = float(weather_data["temperature"])
    threshold = float(farm["threshold"])

    if temperature < threshold:
        print(f"[AUTO] {farm['farm_name']}: {temperature:.1f}°C < {threshold:.1f}°C - safe")
        return

    # Avoid sending repeated SMS every monitoring cycle while the same heat
    # event is still active. Change the cooldown with the environment variable.
    conn = get_db()
    cutoff = (datetime.now() - timedelta(minutes=AUTO_ALERT_COOLDOWN_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
    recent = conn.execute(
        """
        SELECT id FROM alerts
        WHERE farm_id = ? AND user_id = ? AND created_at >= ?
        ORDER BY id DESC LIMIT 1
        """,
        (farm["id"], farm["user_id"], cutoff)
    ).fetchone()
    user = conn.execute(
        "SELECT phone FROM users WHERE id = ?",
        (farm["user_id"],)
    ).fetchone()
    conn.close()

    if recent:
        print(f"[AUTO] {farm['farm_name']}: heat alert already sent recently; skipping duplicate.")
        return

    save_alert(
        farm["user_id"], farm["id"], farm["farm_name"], farm["crop"],
        temperature, threshold
    )

    sms_sent = False
    if user and user["phone"]:
        sms_sent = send_sms(
            user["phone"], farm["farm_name"], farm["crop"],
            temperature, threshold
        )

    print(
        f"[AUTO] HEAT ALERT: {farm['farm_name']} at {temperature:.1f}°C "
        f"(limit {threshold:.1f}°C). SMS sent={sms_sent}"
    )


def automatic_monitor_loop():
    """Continuously monitor all registered farms while Flask is running."""
    print(
        f"[AUTO] Automatic weather monitoring started. "
        f"Checking every {AUTO_CHECK_INTERVAL_MINUTES} minutes."
    )

    while True:
        try:
            conn = get_db()
            farms = conn.execute("SELECT * FROM farms ORDER BY id").fetchall()
            conn.close()

            for farm in farms:
                try:
                    check_farm_for_automatic_alert(farm)
                except Exception as error:
                    print(f"[AUTO] Error checking {farm['farm_name']}: {error}")

        except Exception as error:
            print(f"[AUTO] Monitoring error: {error}")

        time.sleep(AUTO_CHECK_INTERVAL_MINUTES * 60)


def start_automatic_monitor():
    monitor_thread = threading.Thread(
        target=automatic_monitor_loop,
        name="CropShield-AutoMonitor",
        daemon=True
    )
    monitor_thread.start()


# WEATHER ROUTE
# ============================================================
@app.route("/weather/<int:farm_id>",methods=["GET","POST"])
def weather(farm_id):

    # --------------------------------------------------------
    # LOGIN CHECK
    # --------------------------------------------------------

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    user_id = session["user_id"]

    try:

        # ----------------------------------------------------
        # GET FARM
        # ----------------------------------------------------

        conn = get_db()

        farm = conn.execute(
            """
            SELECT *
            FROM farms
            WHERE id = ?
            AND user_id = ?
            """,
            (farm_id, user_id)
        ).fetchone()

        conn.close()

        if farm is None:
            return jsonify({
                "success": False,
                "message": "Farm not found."
            }), 404

        # ----------------------------------------------------
        # GEOCODE LOCATION
        # ----------------------------------------------------

        location_data = geocode_location(
            farm["location"]
        )

        if location_data is None:
            return jsonify({
                "success": False,
                "message": (
                    "Could not find the location "
                    f"'{farm['location']}'. "
                    "Please enter a valid city or town."
                )
            }), 400

        # ----------------------------------------------------
        # GET WEATHER
        # ----------------------------------------------------

        weather_data = get_weather(
            location_data["latitude"],
            location_data["longitude"]
        )

        if weather_data is None:
            return jsonify({
                "success": False,
                "message": (
                    "Could not get weather data. "
                    "Please try again."
                )
            }), 503

        temperature = weather_data["temperature"]

        threshold = float(
            farm["threshold"]
        )

        # ----------------------------------------------------
        # CHECK TEMPERATURE
        # ----------------------------------------------------

        heat_alert = (
            temperature is not None
            and temperature >= threshold
        )

        sms_sent = False
        alert_saved = False
        duplicate_alert = False  # Kept for compatibility with the frontend.

        # ----------------------------------------------------
        # IMMEDIATE HEAT ALERT (NO SIX-HOUR COOLDOWN)
        # ----------------------------------------------------
        if heat_alert:
            # Save each detected threshold breach to the alert history.
            save_alert(
                user_id,
                farm_id,
                farm["farm_name"],
                farm["crop"],
                temperature,
                threshold
            )
            alert_saved = True

            # Retrieve the current user's phone number.
            conn = get_db()
            user = conn.execute(
                "SELECT phone FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()
            conn.close()

            # Attempt SMS delivery immediately. A real SMS is sent only
            # when valid Twilio environment variables are configured.
            if user and user["phone"]:
                sms_sent = send_sms(
                    user["phone"],
                    farm["farm_name"],
                    farm["crop"],
                    temperature,
                    threshold
                )

        # ----------------------------------------------------
        # RESPONSE MESSAGE
        # ----------------------------------------------------
        if heat_alert:
            if sms_sent:
                message = (
                    "HEAT ALERT: Temperature exceeded the threshold. "
                    "SMS was accepted by Twilio for delivery."
                )
            else:
                message = (
                    "HEAT ALERT: Temperature exceeded the threshold. "
                    "Alert saved in history, but no real SMS was sent. "
                    "Configure valid Twilio credentials to enable SMS."
                )
        else:
            message = (
                "Temperature is below your configured heat threshold."
            )

        # ----------------------------------------------------
        # RETURN JSON
        # ----------------------------------------------------

        return jsonify({
            "success": True,

            "farm": {
                "id": farm["id"],
                "name": farm["farm_name"],
                "method": farm["method"],
                "location": farm["location"],
                "crop": farm["crop"],
                "growth_stage": farm["growth_stage"],
                "threshold": threshold
            },

            "location": {
                "name": location_data["name"],
                "state": location_data["state"],
                "country": location_data["country"],
                "latitude": location_data["latitude"],
                "longitude": location_data["longitude"]
            },

            "weather": {
                "temperature": temperature,
                "humidity": weather_data["humidity"],
                "feels_like": weather_data["feels_like"],
                "weather_code": weather_data["weather_code"],
                "time": weather_data["time"]
            },

            "alert": {
                "triggered": heat_alert,
                "message": message,
                "sms_sent": sms_sent,
                "saved": alert_saved,
                "duplicate": duplicate_alert
            }
        })

    except Exception as error:

        # Print the real error in the VS Code terminal
        print()
        print("=" * 60)
        print("WEATHER ROUTE ERROR")
        print("=" * 60)
        print(error)
        print("=" * 60)
        print()

        # IMPORTANT:
        # Return JSON instead of Flask's HTML error page.
        return jsonify({
            "success": False,
            "message": (
                "Weather check failed. "
                "Please check the terminal for details."
            ),
            "error": str(error)
        }), 500
    # ============================================================
# LOGOUT
# ============================================================

@app.route("/logout", methods=["POST"])
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("home")
    )


# ============================================================
# INITIALIZE DATABASE
# ============================================================

init_db()


# ============================================================
# START FLASK SERVER
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("CropShield - Extreme Heat Crop Protection")
    print("=" * 60)
    print("Server: http://127.0.0.1:5000")
    print("Database:", DATABASE)
    print()
    print("Greenhouse + Open Field")
    print("Weather: Open-Meteo")
    print("SMS: Twilio / Demo Mode")
    print("=" * 60)
    print()

    # Flask's debug reloader creates two processes. Start the background
    # monitor only in the serving process so alerts are not duplicated.
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not True:
        start_automatic_monitor()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )

    
       