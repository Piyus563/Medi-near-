
"""
MediNear AI — Automated Backend & Database Test Suite
Tests: SQLite models, search queries, password hashing, session auth,
       duplicate booking prevention, and CSRF protection.
"""

import re
from app import app, db
from models import User, Doctor, Hospital, Pharmacy, Appointment

def extract_csrf_token(response_text):
    """Extracts CSRF token from HTML form or meta tag."""
    match = re.search(r'name="csrf_token"\s+value="([^"]+)"', response_text)
    if not match:
        match = re.search(r'name="csrf-token"\s+content="([^"]+)"', response_text)
    return match.group(1) if match else None

def run_tests():
    print("=" * 60)
    print(" MediNear AI — Automated Backend & SQLite Test Suite")
    print("=" * 60)

    client = app.test_client()

    # 1. Health & Database Check
    print("\n[1] Testing /health Endpoint & SQLite Database Connection...")
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed with {res.status_code}"
    health_data = res.get_json()
    assert health_data["status"] == "healthy"
    assert health_data["database"] == "connected"
    print("    [PASS] /health is healthy and SQLite is connected.")

    with app.app_context():
        doc_count = Doctor.query.count()
        hosp_count = Hospital.query.count()
        pharm_count = Pharmacy.query.count()
        user_count = User.query.count()
        apt_count = Appointment.query.count()
        print(f"    [INFO] Verified SQLite Seed Data: {doc_count} Doctors, {hosp_count} Hospitals, {pharm_count} Pharmacies, {user_count} Users, {apt_count} Appointments.")
        assert doc_count >= 8
        assert hosp_count >= 4
        assert pharm_count >= 4
        assert user_count >= 2

    # 2. SQLite-Driven Doctor Search & Filters
    print("\n[2] Testing Doctor Search & Filtering in SQLite...")
    # By specialty
    res = client.get("/doctors?specialty=Dentist")
    assert res.status_code == 200
    assert "Sameer Deshmukh" in res.get_data(as_text=True)
    print("    [PASS] Filter by specialty 'Dentist' returned Dr. Sameer Deshmukh.")

    # By keyword search
    res = client.get("/doctors?q=Ananya")
    assert res.status_code == 200
    assert "Dr. Ananya Sharma" in res.get_data(as_text=True)
    print("    [PASS] Search by name 'Ananya' returned Dr. Ananya Sharma.")

    # By fee sorting
    res = client.get("/doctors?sort=fee_asc")
    assert res.status_code == 200
    print("    [PASS] Sorting by consultation fee (low to high) executed successfully.")

    # 3. User Registration with Password Hashing & Validation
    print("\n[3] Testing User Registration & Password Hashing...")
    get_reg = client.get("/register")
    csrf_token = extract_csrf_token(get_reg.get_data(as_text=True))
    assert csrf_token is not None, "Failed to retrieve CSRF token from /register"

    test_email = "vikram.patient@example.com"
    with app.app_context():
        existing = User.query.filter_by(email=test_email).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()

    reg_res = client.post("/register", data={
        "csrf_token": csrf_token,
        "name": "Vikram Malhotra",
        "email": test_email,
        "phone": "9812345678",
        "password": "PatientPassword@123",
        "role": "patient"
    }, follow_redirects=True)
    assert reg_res.status_code == 200
    assert "Account created successfully" in reg_res.get_data(as_text=True)
    print("    [PASS] User registration submitted with valid CSRF token.")

    with app.app_context():
        registered_user = User.query.filter_by(email=test_email).first()
        assert registered_user is not None
        assert registered_user.password_hash != "PatientPassword@123"
        assert registered_user.check_password("PatientPassword@123")
        assert not registered_user.check_password("WrongPassword")
        print("    [PASS] Werkzeug secure password hashing verified in SQLite.")

    # Duplicate email registration check
    get_reg2 = client.get("/register")
    csrf_token2 = extract_csrf_token(get_reg2.get_data(as_text=True))
    dup_res = client.post("/register", data={
        "csrf_token": csrf_token2,
        "name": "Duplicate Vikram",
        "email": test_email,
        "phone": "9812345678",
        "password": "AnotherPassword@123",
        "role": "patient"
    }, follow_redirects=True)
    assert "already exists" in dup_res.get_data(as_text=True)
    print("    [PASS] Duplicate email registration cleanly prevented with warning message.")

    # 4. User Login & Session-Based Authentication
    print("\n[4] Testing Login & Session-Based Authentication...")
    get_login = client.get("/login")
    login_csrf = extract_csrf_token(get_login.get_data(as_text=True))

    # Bad credentials
    bad_login = client.post("/login", data={
        "csrf_token": login_csrf,
        "email": test_email,
        "password": "IncorrectPassword"
    }, follow_redirects=True)
    assert "Invalid email address or password" in bad_login.get_data(as_text=True)
    print("    [PASS] Invalid login attempt rejected with error message.")

    # Successful login
    login_csrf2 = extract_csrf_token(client.get("/login").get_data(as_text=True))
    good_login = client.post("/login", data={
        "csrf_token": login_csrf2,
        "email": test_email,
        "password": "PatientPassword@123"
    }, follow_redirects=True)
    assert good_login.status_code == 200
    assert "Welcome back" in good_login.get_data(as_text=True)
    print("    [PASS] Correct login authenticated and session created.")

    # 5. Role-Based Authorization
    print("\n[5] Testing Role-Based Authorization for Admin Area...")
    # While logged in as regular patient, accessing /admin must be denied
    admin_access = client.get("/admin", follow_redirects=True)
    assert "Access restricted" in admin_access.get_data(as_text=True)
    print("    [PASS] Non-admin patient blocked from /admin.")

    # Sign out and sign in as seeded admin
    client.get("/logout")
    admin_login_csrf = extract_csrf_token(client.get("/login").get_data(as_text=True))
    admin_login = client.post("/login", data={
        "csrf_token": admin_login_csrf,
        "email": "admin@example.com",
        "password": "Admin@123"
    }, follow_redirects=True)
    assert admin_login.status_code == 200
    admin_page = client.get("/admin")
    assert admin_page.status_code == 200
    assert "Healthcare Provider Operations" in admin_page.get_data(as_text=True)
    print("    [PASS] Administrator successfully authenticated and granted access to /admin.")

    # 6. Appointment Booking & Duplicate Slot Prevention (Tasks 8 & 9)
    print("\n[6] Testing Appointment Booking & Duplicate Slot Prevention...")
    with app.app_context():
        doc = Doctor.query.filter_by(name="Dr. Ananya Sharma").first()
        doc_id = doc.id
        doc_name = doc.name

    test_date = "2026-11-20"
    test_slot = "04:30 PM"

    # Ensure clean test slot
    with app.app_context():
        Appointment.query.filter_by(doctor_id=doc_id, appointment_date=test_date, time_slot=test_slot).delete()
        db.session.commit()

    # Get CSRF token for JSON API request
    page = client.get("/")
    api_csrf = extract_csrf_token(page.get_data(as_text=True))

    # Booking 1
    book_res1 = client.post("/api/appointments/request", json={
        "doctor_id": doc_id,
        "patient_name": "First Patient",
        "patient_phone": "9876543210",
        "date": test_date,
        "time_slot": test_slot,
        "mode": "In-Person Clinic Visit"
    }, headers={"X-CSRFToken": api_csrf})
    assert book_res1.status_code == 201, f"Booking 1 failed with {book_res1.status_code}: {book_res1.get_data(as_text=True)}"
    booking_data1 = book_res1.get_json()
    assert booking_data1["success"] is True
    booking_ref = booking_data1["appointment_id"]
    print(f"    [PASS] Slot successfully booked in SQLite (Ref: {booking_ref}).")

    # Booking 2: Attempting to book the EXACT SAME DOCTOR, DATE, AND SLOT!
    book_res2 = client.post("/api/appointments/request", json={
        "doctor_id": doc_id,
        "patient_name": "Second Patient",
        "patient_phone": "9123456789",
        "date": test_date,
        "time_slot": test_slot,
        "mode": "In-Person Clinic Visit"
    }, headers={"X-CSRFToken": api_csrf})
    assert book_res2.status_code == 409, f"Expected 409 Conflict, got {book_res2.status_code}"
    booking_data2 = book_res2.get_json()
    assert booking_data2["success"] is False
    assert "already booked" in booking_data2["message"]
    print("    [PASS] DUPLICATE BOOKING PREVENTED: Returned 409 Conflict with warning message.")

    # Test Cancellation
    cancel_res = client.post(f"/api/appointments/{booking_ref}/cancel", json={
        "reason": "Rescheduled appointment"
    }, headers={"X-CSRFToken": api_csrf})
    assert cancel_res.status_code == 200
    assert cancel_res.get_json()["success"] is True
    with app.app_context():
        apt = Appointment.query.filter_by(booking_ref=booking_ref).first()
        assert apt.status == "Cancelled"
    print("    [PASS] Appointment cancellation updated status to 'Cancelled' in SQLite.")

    # 7. AI Specialty Triaging Endpoint Check
    print("\n[7] Testing AI Assistant & Clinical Red-Flag Triage...")
    ai_emergency = client.post("/api/ai-chat", json={
        "message": "I have sudden acute chest pain and shortness of breath",
        "language": "en"
    }, headers={"X-CSRFToken": api_csrf})
    assert ai_emergency.status_code == 200
    assert ai_emergency.get_json()["is_emergency"] is True
    print("    [PASS] Acute cardiovascular emergency red flag detected (calls 108/112).")

    ai_triage = client.post("/api/ai-chat", json={
        "message": "I have skin allergy with redness and rash",
        "language": "en"
    }, headers={"X-CSRFToken": api_csrf})
    assert ai_triage.status_code == 200
    assert ai_triage.get_json()["recommended_specialty"] == "Dermatologist"
    print("    [PASS] AI symptom matching recommended 'Dermatologist' specialist.")

    print("\n" + "=" * 60)
    print(" ALL 7 BACKEND & SQLITE TEST PHASES PASSED WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
