"""
MediNear AI — Smart Healthcare & Doctor Finder
Flask Application Entry Point with SQLite & SQLAlchemy Integration
"""

import os
import re
import random
from datetime import datetime, date, timezone
from functools import wraps

from flask import (
    Flask, render_template, request, jsonify, redirect,
    url_for, flash, session, abort
)
from flask_wtf.csrf import CSRFProtect, CSRFError
from sqlalchemy.exc import IntegrityError

try:
    from models import (
        db, User, Doctor, Hospital, Pharmacy, Appointment, seed_database
    )
except ImportError:
    from model import (
        db, User, Doctor, Hospital, Pharmacy, Appointment, seed_database
    )

# -----------------------------------------------------------------------------
# Application Configuration
# -----------------------------------------------------------------------------
app = Flask(__name__)

# Security & Session Settings
app.secret_key = os.environ.get("SECRET_KEY", "medinear-ai-prototype-secret-2026")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///medinear.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Initialize SQLAlchemy & CSRF Protection
db.init_app(app)
csrf = CSRFProtect(app)

# -----------------------------------------------------------------------------
# Database Initialization & Seeding on Startup
# -----------------------------------------------------------------------------
with app.app_context():
    db.create_all()
    seed_database(db)

# -----------------------------------------------------------------------------
# Context Processors & Auth Helpers
# -----------------------------------------------------------------------------
@app.context_processor
def inject_context():
    """Injects current_user and active user info across all templates."""
    user_id = session.get("user_id")
    current_user = db.session.get(User, user_id) if user_id else None
    return {
        "current_user": current_user,
        "logged_in": current_user is not None,
        "user_role": session.get("user_role", "guest")
    }

def login_required(f):
    """Decorator to protect routes requiring authenticated patient or user."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to access your patient dashboard and bookings.", "info")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to protect healthcare moderation and administrative consoles."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Administrator authentication required.", "warning")
            return redirect(url_for("login", next=request.path))
        if session.get("user_role") != "admin":
            flash("Access restricted. Administrator privileges required.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function

# -----------------------------------------------------------------------------
# Deployment & Health Check Route
# -----------------------------------------------------------------------------
@app.route("/health")
def health_check():
    """Health check endpoint for deployment monitoring and uptime verification."""
    try:
        # Check SQLite connection
        db.session.execute(db.text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return jsonify({
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "service": "MediNear AI Healthcare Engine",
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }), (200 if db_status == "connected" else 503)

# -----------------------------------------------------------------------------
# Frontend Page Routes (Connected to SQLite Models)
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    """Home landing page with verified doctors, emergency hospitals, and pharmacies."""
    featured_doctors = (
        Doctor.query.filter_by(verification_status=True)
        .order_by(Doctor.rating.desc())
        .limit(6)
        .all()
    )
    hospitals = Hospital.query.limit(2).all()
    pharmacies = Pharmacy.query.limit(2).all()

    return render_template(
        "index.html",
        active_page="home",
        featured_doctors=featured_doctors,
        hospitals=hospitals,
        pharmacies=pharmacies
    )

@app.route("/doctors")
def doctors():
    """
    Doctor listings with SQL-driven filtering:
    Search query (name/specialty/clinic), specialty dropdown, city, and sorting.
    """
    keyword = request.args.get("q", "").strip()
    specialty = request.args.get("specialty", "").strip()
    city = request.args.get("city", "").strip()
    sort_by = request.args.get("sort", "distance_asc")

    query = Doctor.query

    # Keyword filter (doctor name, specialty, or clinic)
    if keyword:
        kw_pattern = f"%{keyword}%"
        query = query.filter(
            db.or_(
                Doctor.name.ilike(kw_pattern),
                Doctor.specialty.ilike(kw_pattern),
                Doctor.clinic_name.ilike(kw_pattern),
                Doctor.clinic_address.ilike(kw_pattern)
            )
        )

    # Specialty filter
    if specialty:
        query = query.filter(Doctor.specialty == specialty)

    # City filter (exclude auto-geolocation placeholder text)
    if city and "current location" not in city.lower() and "near you" not in city.lower():
        query = query.filter(Doctor.city.ilike(f"%{city}%"))

    # Sorting
    if sort_by == "rating_desc":
        query = query.order_by(Doctor.rating.desc())
    elif sort_by == "experience_desc":
        query = query.order_by(Doctor.experience_years.desc())
    elif sort_by == "fee_asc":
        query = query.order_by(Doctor.consultation_fee.asc().nullslast())
    elif sort_by == "fee_desc":
        query = query.order_by(Doctor.consultation_fee.desc().nullslast())
    else:
        query = query.order_by(Doctor.distance_km.asc())

    doctors_list = query.all()

    return render_template(
        "doctors.html",
        active_page="doctors",
        doctors=doctors_list,
        query=keyword,
        selected_specialty=specialty,
        selected_city=city,
        current_sort=sort_by
    )

@app.route("/doctor/<int:doctor_id>")
def doctor_details(doctor_id):
    """Doctor details page with credentials, clinic map coordinates, and booking form."""
    doctor = Doctor.query.get_or_404(doctor_id)

    # Query similar doctors with same specialty
    similar_doctors = (
        Doctor.query.filter(Doctor.id != doctor.id, Doctor.specialty == doctor.specialty)
        .order_by(Doctor.rating.desc())
        .limit(2)
        .all()
    )

    # Fallback to general practitioners if no other same-specialty doctor exists
    if not similar_doctors:
        similar_doctors = (
            Doctor.query.filter(Doctor.id != doctor.id)
            .order_by(Doctor.rating.desc())
            .limit(2)
            .all()
        )

    return render_template(
        "doctor_details.html",
        active_page="doctors",
        doctor=doctor,
        similar_doctors=similar_doctors
    )

@app.route("/hospitals")
def hospitals():
    """Hospitals directory with interactive Leaflet map and verified emergency contacts."""
    all_hospitals = Hospital.query.all()
    return render_template(
        "hospitals.html",
        active_page="hospitals",
        hospitals=all_hospitals
    )

@app.route("/pharmacies")
def pharmacies():
    """Pharmacies directory with reported stock status and prescription inquiry modal."""
    all_pharmacies = Pharmacy.query.all()
    return render_template(
        "pharmacies.html",
        active_page="pharmacies",
        pharmacies=all_pharmacies
    )

@app.route("/ai-assistant")
def ai_assistant():
    """AI Healthcare Assistant for symptom triaging and specialty navigation."""
    return render_template(
        "ai_assistant.html",
        active_page="ai_assistant"
    )

@app.route("/dashboard")
def dashboard():
    """
    Patient dashboard showing real database-stored appointments and profile details.
    Allows guest access with demo records or authenticated user view.
    """
    user_id = session.get("user_id")

    if user_id:
        user = db.session.get(User, user_id)
        appointments = (
            Appointment.query.filter_by(user_id=user_id)
            .order_by(Appointment.created_at.desc())
            .all()
        )
    else:
        # If not logged in, retrieve demo patient records from SQLite
        user = User.query.filter_by(email="patient@example.com").first()
        appointments = (
            Appointment.query.order_by(Appointment.created_at.desc())
            .limit(10)
            .all()
        )

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        patient=user,
        appointments=appointments
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    """Secure user sign-in with password hashing verification and session management."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        next_url = request.args.get("next") or request.form.get("next")

        if not email or not password:
            flash("Please provide both email and password.", "warning")
            return render_template("login.html", active_page="login")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session.clear()
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["user_email"] = user.email
            session["user_role"] = user.role

            flash(f"Welcome back, {user.name}!", "success")

            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            if user.role == "admin":
                return redirect(url_for("admin"))
            return redirect(url_for("dashboard"))

        flash("Invalid email address or password. Please try again.", "danger")

    return render_template("login.html", active_page="login")

@app.route("/register", methods=["GET", "POST"])
def register():
    """User registration with role selection, validation, and password hashing."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "patient").strip().lower()

        # Input Validations
        if not name or len(name) < 2:
            flash("Please enter a valid full name.", "warning")
            return render_template("register.html", active_page="register")

        if not email or "@" not in email:
            flash("Please enter a valid email address.", "warning")
            return render_template("register.html", active_page="register")

        # Clean 10-digit phone
        phone_digits = re.sub(r"\D", "", phone)
        if len(phone_digits) != 10:
            flash("Please enter a valid 10-digit mobile number.", "warning")
            return render_template("register.html", active_page="register")

        if not password or len(password) < 6:
            flash("Password must be at least 6 characters long.", "warning")
            return render_template("register.html", active_page="register")

        # Check existing email
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("An account with this email address already exists. Please sign in.", "warning")
            return redirect(url_for("login"))

        # Create new user with hashed password
        new_user = User(
            name=name,
            email=email,
            phone=phone_digits,
            role=role if role in ["patient", "doctor"] else "patient"
        )
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()

            # Automatically log in new user
            session.clear()
            session["user_id"] = new_user.id
            session["user_name"] = new_user.name
            session["user_email"] = new_user.email
            session["user_role"] = new_user.role

            flash(f"Account created successfully for {name}! Welcome to MediNear AI.", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            db.session.rollback()
            flash("Registration failed due to a database error. Please try again.", "danger")

    return render_template("register.html", active_page="register")

@app.route("/logout")
def logout():
    """Logs the user out and clears session data."""
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("login"))

@app.route("/admin")
@admin_required
def admin():
    """Administrator console for provider verification and appointment queue management."""
    doctors_list = Doctor.query.order_by(Doctor.id.desc()).all()
    hospitals_list = Hospital.query.all()
    pharmacies_list = Pharmacy.query.all()
    appointments_list = Appointment.query.order_by(Appointment.created_at.desc()).all()

    return render_template(
        "admin.html",
        active_page="admin",
        doctors=doctors_list,
        hospitals=hospitals_list,
        pharmacies=pharmacies_list,
        appointments=appointments_list
    )

# -----------------------------------------------------------------------------
# Appointment Booking & Management Endpoints (Tasks 8 & 9)
# -----------------------------------------------------------------------------
@app.route("/api/appointments/request", methods=["POST"])
def api_request_appointment():
    """
    Connects appointment forms to SQLite with strict duplicate slot prevention.
    Validates patient data and handles concurrent booking race conditions with transactions.
    """
    data = request.get_json() or {}

    doctor_id = data.get("doctor_id")
    patient_name = (data.get("patient_name") or "").strip()
    patient_phone = (data.get("patient_phone") or "").strip()
    patient_email = (data.get("patient_email") or "").strip()
    appointment_date = (data.get("date") or "").strip()
    time_slot = (data.get("time_slot") or "").strip()
    mode = data.get("mode") or "In-Person Clinic Visit"
    symptoms = (data.get("symptoms") or "").strip()

    # 1. Server-Side Input Validation
    if not doctor_id:
        return jsonify({"success": False, "message": "Doctor ID is required."}), 400

    doctor = db.session.get(Doctor, doctor_id)
    if not doctor:
        return jsonify({"success": False, "message": "Selected doctor was not found in directory."}), 404

    if not patient_name or len(patient_name) < 2:
        return jsonify({"success": False, "message": "Please provide a valid patient name."}), 400

    phone_digits = re.sub(r"\D", "", patient_phone)
    if len(phone_digits) != 10:
        return jsonify({"success": False, "message": "Please provide a valid 10-digit phone number."}), 400

    if not appointment_date:
        return jsonify({"success": False, "message": "Please select an appointment date."}), 400

    try:
        parsed_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
        if parsed_date < date.today():
            return jsonify({
                "success": False,
                "message": "Appointment date cannot be in the past. Please select an upcoming date."
            }), 400
    except ValueError:
        return jsonify({"success": False, "message": "Invalid date format. Expected YYYY-MM-DD."}), 400

    if not time_slot:
        return jsonify({"success": False, "message": "Please select an available time slot."}), 400

    # 2. Duplicate Booking Check (Task 9: Prevent duplicate slot for the same doctor)
    existing_booking = Appointment.query.filter_by(
        doctor_id=doctor.id,
        appointment_date=appointment_date,
        time_slot=time_slot
    ).filter(Appointment.status != "Cancelled").first()

    if existing_booking:
        return jsonify({
            "success": False,
            "error": "SLOT_UNAVAILABLE",
            "message": (
                f"The slot '{time_slot}' on {appointment_date} is already booked for {doctor.name}. "
                "Please choose an alternative time slot or date."
            )
        }), 409

    # 3. Create Unique Booking Reference
    booking_ref = f"APT-{random.randint(1000, 9999)}"
    while Appointment.query.filter_by(booking_ref=booking_ref).first():
        booking_ref = f"APT-{random.randint(1000, 9999)}"

    # 4. Transaction Handling
    try:
        new_appointment = Appointment(
            booking_ref=booking_ref,
            user_id=session.get("user_id"),
            doctor_id=doctor.id,
            patient_name=patient_name,
            patient_phone=phone_digits,
            patient_email=patient_email or None,
            appointment_date=appointment_date,
            time_slot=time_slot,
            mode=mode,
            symptoms=symptoms or None,
            fee=f"₹{doctor.consultation_fee}" if doctor.consultation_fee else "₹600",
            status="Confirmed"
        )
        db.session.add(new_appointment)
        db.session.commit()

        return jsonify({
            "success": True,
            "appointment_id": booking_ref,
            "message": f"Appointment request confirmed with {doctor.name} on {appointment_date} at {time_slot}!"
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": "SLOT_CONFLICT",
            "message": f"This slot for {doctor.name} was just reserved by another patient. Please select an alternative time."
        }), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": "INTERNAL_ERROR",
            "message": "Failed to book appointment due to a database error. Please try again."
        }), 500

@app.route("/api/appointments/<booking_ref>/cancel", methods=["POST"])
def api_cancel_appointment(booking_ref):
    """Cancels an existing appointment in SQLite and records optional reason."""
    appointment = Appointment.query.filter_by(booking_ref=booking_ref).first()
    if not appointment:
        return jsonify({"success": False, "message": "Appointment record not found."}), 404

    payload = request.get_json() or {}
    reason = payload.get("reason", "Cancelled by patient")

    try:
        appointment.status = "Cancelled"
        appointment.cancel_reason = reason
        db.session.commit()
        return jsonify({
            "success": True,
            "message": f"Appointment {booking_ref} has been cancelled successfully."
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": "Failed to cancel appointment."}), 500

# -----------------------------------------------------------------------------
# Admin API Moderation Endpoints
# -----------------------------------------------------------------------------
@app.route("/api/admin/providers/<int:doctor_id>/toggle-status", methods=["POST"])
@admin_required
def api_admin_toggle_doctor(doctor_id):
    """Toggles verification status of a doctor in SQLite."""
    doctor = Doctor.query.get_or_404(doctor_id)
    doctor.verification_status = not doctor.verification_status
    db.session.commit()

    return jsonify({
        "success": True,
        "doctor_id": doctor.id,
        "verification_status": doctor.verification_status,
        "message": f"Provider {doctor.name} verification status set to {doctor.verification_status}."
    })

@app.route("/api/admin/providers/add", methods=["POST"])
@admin_required
def api_admin_add_doctor():
    """Adds a new healthcare practitioner to SQLite database with validation."""
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    specialty = (data.get("specialty") or "").strip()
    qualifications = (data.get("qualifications") or "").strip()
    clinic_name = (data.get("clinic_name") or "").strip()
    city = (data.get("city") or "").strip()

    if not name or not specialty or not qualifications or not clinic_name or not city:
        return jsonify({"success": False, "message": "All required fields must be provided."}), 400

    try:
        new_doc = Doctor(
            name=name,
            specialty=specialty,
            qualifications=qualifications,
            experience_years=int(data.get("experience_years") or 5),
            clinic_name=clinic_name,
            clinic_address=data.get("clinic_address") or f"Main Road, {city}",
            city=city,
            latitude=float(data.get("latitude") or 28.5700),
            longitude=float(data.get("longitude") or 77.3200),
            distance_km=float(data.get("distance_km") or 2.5),
            consultation_fee=int(data["consultation_fee"]) if data.get("consultation_fee") else 600,
            verification_status=bool(data.get("verification_status", True)),
            available_today=True,
            availability_info="Available Today: By Appointment",
            languages="English, Hindi",
            about=f"{name} is a dedicated {specialty} at {clinic_name}.",
            avatar="/static/images/doctor-placeholder.svg"
        )
        db.session.add(new_doc)
        db.session.commit()

        return jsonify({
            "success": True,
            "doctor": new_doc.to_dict(),
            "message": f"Dr. {name} successfully added to provider directory."
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/admin/appointments/<int:appointment_id>/status", methods=["POST"])
@admin_required
def api_admin_update_appointment_status(appointment_id):
    """Updates appointment status (Approved/Confirmed or Declined/Cancelled)."""
    appointment = Appointment.query.get_or_404(appointment_id)
    data = request.get_json() or {}
    new_status = data.get("status")

    if new_status not in ["Confirmed", "Cancelled", "Completed", "Pending"]:
        return jsonify({"success": False, "message": "Invalid appointment status."}), 400

    appointment.status = new_status
    db.session.commit()

    return jsonify({
        "success": True,
        "appointment_id": appointment.id,
        "status": appointment.status,
        "message": f"Appointment #{appointment.booking_ref} status updated to {new_status}."
    })

# -----------------------------------------------------------------------------
# AI Healthcare Assistant Endpoint (Symptom Triage & Red-Flag Detection)
# -----------------------------------------------------------------------------
@app.route("/api/ai-chat", methods=["POST"])
@csrf.exempt
def api_ai_chat():
    """
    Intelligent Specialty Triaging Endpoint:
    Checks emergency red-flags, analyzes symptoms, and connects to real SQLite doctors.
    """
    payload = request.get_json() or {}
    user_msg = payload.get("message", "").strip().lower()
    lang = payload.get("language", "en")

    # 1. Emergency Red Flags (Acute symptoms requiring 108/112 intervention)
    emergency_keywords = [
        "chest pain", "heart attack", "shortness of breath", "severe breathing",
        "unconscious", "stroke", "paralysis", "heavy bleeding", "seizure",
        "छाती", "सांस", "बेहोश", "दौरा"
    ]
    for kw in emergency_keywords:
        if kw in user_msg:
            return jsonify({
                "reply_text": (
                    "चेतावनी: सीने में तेज दर्द, सांस लेने में गंभीर तकलीफ या बेहोशी संभावित आपातकालीन चिकित्सा स्थिति का संकेत हो सकती है। कृपया समय न गंवाएं।"
                    if lang == "hi" else
                    "CRITICAL MEDICAL ADVISORY: Acute chest pain, shortness of breath, or sudden weakness can indicate a severe cardiovascular or respiratory emergency. Do not wait for a routine appointment."
                ),
                "recommended_specialty": "Cardiologist",
                "specialty_reason": "Emergency Acute Care / Cardiology",
                "is_emergency": True,
                "emergency_note": "Dial emergency ambulance (108 / 112) or go to the nearest hospital trauma unit immediately."
            })

    # 2. Clinical Specialty Rules & Database Doctor Matching
    specialty_mapping = [
        (["skin", "rash", "acne", "hair", "itching", "eczema", "allergy", "त्वचा", "खुजली", "मुंहासे"], "Dermatologist", "Specialized in clinical dermatology and allergy diagnostics."),
        (["tooth", "teeth", "gum", "cavity", "dental", "दांत", "मसूड़े"], "Dentist", "Oral health, restorative dental care, and tooth diagnostics."),
        (["eye", "vision", "blur", "cornea", "glasses", "strain", "आंख", "दृष्टि"], "Eye Specialist", "Refraction testing, cornea care, and eye health."),
        (["child", "baby", "infant", "pediatric", "vaccine", "शिशु", "बच्चे"], "Pediatrician", "Pediatric healthcare and developmental checkups."),
        (["bp", "blood pressure", "palpitation", "cholesterol", "heart", "बीपी", "हृदय"], "Cardiologist", "Preventive cardiology and cardiovascular health.")
    ]

    matched_specialty = "General Physician"
    matched_reason = "Comprehensive primary medical care and initial clinical triage."

    for keywords, spec, reason in specialty_mapping:
        if any(k in user_msg for k in keywords):
            matched_specialty = spec
            matched_reason = reason
            break

    # Look up a verified doctor in SQLite for this specialty
    recommended_doctor = (
        Doctor.query.filter_by(specialty=matched_specialty, verification_status=True)
        .order_by(Doctor.rating.desc())
        .first()
    )

    doc_hint = f" Verified provider available: {recommended_doctor.name} at {recommended_doctor.clinic_name}." if recommended_doctor else ""

    if lang == "hi":
        reply = f"आपके लक्षणों के लिए {matched_specialty} से परामर्श करना उचित है।{doc_hint}"
    else:
        reply = f"Based on your symptoms, consulting a certified {matched_specialty} is recommended.{doc_hint}"

    return jsonify({
        "reply_text": reply,
        "recommended_specialty": matched_specialty,
        "specialty_reason": matched_reason,
        "is_emergency": False
    })

# -----------------------------------------------------------------------------
# CSRF Error Handler
# -----------------------------------------------------------------------------
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    if request.is_json or request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "CSRF_ERROR", "message": "CSRF token validation failed."}), 400
    flash("Session security token expired or missing. Please submit the form again.", "warning")
    return redirect(request.referrer or url_for("index"))

# -----------------------------------------------------------------------------
# Main Application Runner
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n=======================================================")
    print(f" MediNear AI — Smart Healthcare & Doctor Finder")
    print(f" SQLite Database: instance/medinear.db or medinear.db")
    print(f" Serving live at: http://127.0.0.1:{port}")
    print(f"=======================================================\n")
    app.run(host="127.0.0.1", port=port, debug=True)
