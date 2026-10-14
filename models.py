"""
MediNear AI — Smart Healthcare & Doctor Finder
SQLAlchemy Database Models and Safe Seed Data
"""

import json
from datetime import datetime, timezone
from sqlalchemy.ext.hybrid import hybrid_property
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

def get_utc_now():
    """Returns current UTC timestamp as timezone-naive datetime for SQLite compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

db = SQLAlchemy()

# -----------------------------------------------------------------------------
# User Model (Patients, Doctors, Administrators)
# -----------------------------------------------------------------------------
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='patient', nullable=False)  # 'patient', 'doctor', 'admin'
    blood_group = db.Column(db.String(15), default='Not Specified')
    emergency_contact = db.Column(db.String(50), default='+91 98110 00000')
    created_at = db.Column(db.DateTime, default=get_utc_now)

    # Relationships
    appointments = db.relationship('Appointment', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password: str):
        """Hashes password using secure Werkzeug pbkdf2 algorithm."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verifies entered password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "blood_group": self.blood_group,
            "emergency_contact": self.emergency_contact,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

# -----------------------------------------------------------------------------
# Doctor Model
# -----------------------------------------------------------------------------
class Doctor(db.Model):
    __tablename__ = 'doctors'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    specialty = db.Column(db.String(80), nullable=False, index=True)
    qualifications = db.Column(db.String(200), nullable=False)
    experience_years = db.Column(db.Integer, default=0)
    verification_status = db.Column(db.Boolean, default=True)
    clinic_name = db.Column(db.String(150), nullable=False)
    clinic_address = db.Column(db.String(250), nullable=False)
    city = db.Column(db.String(80), nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    distance_km = db.Column(db.Float, default=1.0)
    consultation_fee = db.Column(db.Integer, nullable=True)
    rating = db.Column(db.Float, default=4.5)
    reviews_count = db.Column(db.Integer, default=0)
    available_today = db.Column(db.Boolean, default=True)
    availability_info = db.Column(db.String(120), default="Available Today: Inquire with clinic")
    _languages = db.Column('languages', db.String(150), default="English, Hindi")
    about = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    avatar = db.Column(db.String(200), default="/static/images/doctor-placeholder.svg")
    created_at = db.Column(db.DateTime, default=get_utc_now)

    # Relationships
    appointments = db.relationship('Appointment', backref='doctor', lazy=True, cascade='all, delete-orphan')

    @hybrid_property
    def languages(self):
        """Returns languages as a list of strings so {{ doctor.languages|join(', ') }} renders cleanly."""
        if not self._languages:
            return ["English", "Hindi"]
        if isinstance(self._languages, list):
            return self._languages
        return [l.strip() for l in str(self._languages).split(",") if l.strip()]

    @languages.setter
    def languages(self, val):
        if isinstance(val, (list, tuple)):
            self._languages = ", ".join(val)
        else:
            self._languages = str(val) if val is not None else "English, Hindi"

    @languages.expression
    def languages(cls):
        return cls._languages

    @property
    def languages_list(self):
        return self.languages

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "specialty": self.specialty,
            "qualifications": self.qualifications,
            "experience_years": self.experience_years,
            "verification_status": self.verification_status,
            "clinic_name": self.clinic_name,
            "clinic_address": self.clinic_address,
            "city": self.city,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "distance_km": self.distance_km,
            "consultation_fee": self.consultation_fee,
            "rating": self.rating,
            "reviews_count": self.reviews_count,
            "available_today": self.available_today,
            "availability_info": self.availability_info,
            "languages": self.languages,
            "about": self.about,
            "phone": self.phone,
            "email": self.email,
            "avatar": self.avatar
        }

# -----------------------------------------------------------------------------
# Hospital Model
# -----------------------------------------------------------------------------
class Hospital(db.Model):
    __tablename__ = 'hospitals'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(250), nullable=False)
    city = db.Column(db.String(80), nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    distance_km = db.Column(db.Float, default=2.0)
    emergency_24x7 = db.Column(db.Boolean, default=True)
    icu_beds_available = db.Column(db.Integer, default=5)
    emergency_contact = db.Column(db.String(30), nullable=False)
    general_contact = db.Column(db.String(30), nullable=True)
    services_str = db.Column('services_str', db.Text, default="24x7 Emergency, ICU")
    rating = db.Column(db.Float, default=4.5)
    verification_status = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_utc_now)

    @hybrid_property
    def services(self):
        if not self.services_str:
            return []
        if isinstance(self.services_str, list):
            return self.services_str
        return [s.strip() for s in str(self.services_str).split(",") if s.strip()]

    @services.setter
    def services(self, val):
        if isinstance(val, (list, tuple)):
            self.services_str = ", ".join(val)
        else:
            self.services_str = str(val) if val is not None else ""

    @services.expression
    def services(cls):
        return cls.services_str

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "address": self.address,
            "city": self.city,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "distance_km": self.distance_km,
            "emergency_24x7": self.emergency_24x7,
            "icu_beds_available": self.icu_beds_available,
            "emergency_contact": self.emergency_contact,
            "general_contact": self.general_contact,
            "services": self.services,
            "rating": self.rating,
            "verification_status": self.verification_status
        }

# -----------------------------------------------------------------------------
# Pharmacy Model
# -----------------------------------------------------------------------------
class Pharmacy(db.Model):
    __tablename__ = 'pharmacies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(250), nullable=False)
    city = db.Column(db.String(80), nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    distance_km = db.Column(db.Float, default=1.0)
    is_24x7 = db.Column(db.Boolean, default=True)
    home_delivery = db.Column(db.Boolean, default=True)
    contact = db.Column(db.String(30), nullable=False)
    stock_sample_json = db.Column(db.Text, nullable=True)
    verification_status = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_utc_now)

    @property
    def stock_sample(self):
        if self.stock_sample_json:
            try:
                return json.loads(self.stock_sample_json)
            except Exception:
                return {}
        return {}

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "city": self.city,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "distance_km": self.distance_km,
            "is_24x7": self.is_24x7,
            "home_delivery": self.home_delivery,
            "contact": self.contact,
            "stock_sample": self.stock_sample,
            "verification_status": self.verification_status
        }

# -----------------------------------------------------------------------------
# Appointment Model (With Slot Uniqueness Constraint & State Tracking)
# -----------------------------------------------------------------------------
class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    booking_ref = db.Column(db.String(30), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    patient_name = db.Column(db.String(120), nullable=False)
    patient_phone = db.Column(db.String(20), nullable=False)
    patient_email = db.Column(db.String(120), nullable=True)
    appointment_date = db.Column(db.String(20), nullable=False)  # ISO Date 'YYYY-MM-DD'
    time_slot = db.Column(db.String(20), nullable=False)        # e.g. '10:00 AM'
    mode = db.Column(db.String(60), default="In-Person Clinic Visit")
    symptoms = db.Column(db.Text, nullable=True)
    fee = db.Column(db.String(20), default="₹600")
    status = db.Column(db.String(30), default="Confirmed")      # 'Confirmed', 'Pending', 'Completed', 'Cancelled'
    cancel_reason = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=get_utc_now)

    # Unique constraint ensuring no double booking for the same doctor, date and slot
    __table_args__ = (
        db.UniqueConstraint('doctor_id', 'appointment_date', 'time_slot', name='uq_doctor_date_slot'),
    )

    # Convenient template accessors matching existing frontend template properties
    @property
    def doctor_name(self):
        return self.doctor.name if self.doctor else "Medical Doctor"

    @property
    def specialty(self):
        return self.doctor.specialty if self.doctor else "General Practice"

    @property
    def clinic(self):
        return self.doctor.clinic_name if self.doctor else "Care Clinic"

    @property
    def date(self):
        return self.appointment_date

    @property
    def badge_class(self):
        status_clean = (self.status or '').lower()
        if 'confirm' in status_clean:
            return 'badge-status-confirmed'
        elif 'pend' in status_clean:
            return 'badge-status-pending'
        elif 'complete' in status_clean:
            return 'badge-status-completed'
        elif 'cancel' in status_clean:
            return 'badge-status-cancelled'
        return 'badge-status-pending'

    @property
    def can_cancel(self):
        return self.status in ['Confirmed', 'Pending', 'Pending Confirmation']

    def to_dict(self):
        return {
            "id": self.booking_ref,
            "db_id": self.id,
            "doctor_id": self.doctor_id,
            "doctor_name": self.doctor_name,
            "specialty": self.specialty,
            "clinic": self.clinic,
            "patient_name": self.patient_name,
            "patient_phone": self.patient_phone,
            "date": self.appointment_date,
            "time_slot": self.time_slot,
            "mode": self.mode,
            "status": self.status,
            "badge_class": self.badge_class,
            "fee": self.fee,
            "can_cancel": self.can_cancel
        }

# -----------------------------------------------------------------------------
# Database Seeder (Safe Demonstration Sample Records)
# -----------------------------------------------------------------------------
def seed_database(database: SQLAlchemy):
    """Populates safe initial data into SQLite database if tables are empty."""
    # 1. Seed Users (Demo Patient, Doctor & Admin)
    if User.query.count() == 0:
        demo_patient = User(
            name="Arun Kumar",
            email="patient@example.com",
            phone="9876543210",
            role="patient",
            blood_group="B+ (Positive)",
            emergency_contact="+91 98110 00000 (Spouse)"
        )
        demo_patient.set_password("Patient@123")

        demo_admin = User(
            name="Dr. Suresh Verma",
            email="admin@example.com",
            phone="9810011223",
            role="admin",
            blood_group="O+ (Positive)"
        )
        demo_admin.set_password("Admin@123")

        database.session.add_all([demo_patient, demo_admin])
        database.session.commit()

    # 2. Seed Doctors
    if Doctor.query.count() == 0:
        doctors_data = [
            Doctor(
                name="Dr. Ananya Sharma",
                specialty="General Physician",
                qualifications="MBBS, MD (Internal Medicine) - AIIMS",
                experience_years=11,
                verification_status=True,
                clinic_name="CareFirst Health Clinic",
                clinic_address="Suite 204, Metro Plaza, Sector 18",
                city="Delhi NCR",
                latitude=28.5700,
                longitude=77.3200,
                distance_km=1.2,
                consultation_fee=600,
                rating=4.9,
                reviews_count=184,
                available_today=True,
                availability_info="Available Today: 4:30 PM - 8:00 PM",
                languages="English, Hindi",
                about="Dr. Ananya Sharma has over 11 years of experience in internal medicine, lifestyle disorders, and preventive health checks. She is dedicated to evidence-based medical care and compassionate patient communication.",
                phone="+91 98110 24890",
                email="dr.ananya@carefirst.example.org",
                avatar="/static/images/doctor-placeholder.svg"
            ),
            Doctor(
                name="Dr. Rajesh Iyer",
                specialty="Cardiologist",
                qualifications="MBBS, MD, DM (Cardiology), FACC",
                experience_years=16,
                verification_status=True,
                clinic_name="HeartCare Advanced Center",
                clinic_address="42, Dr. Ambedkar Road, Bandra West",
                city="Mumbai",
                latitude=19.0596,
                longitude=72.8295,
                distance_km=2.4,
                consultation_fee=1200,
                rating=4.95,
                reviews_count=320,
                available_today=True,
                availability_info="Available Today: 5:00 PM - 7:30 PM",
                languages="English, Hindi, Marathi, Tamil",
                about="Dr. Rajesh Iyer is a senior consultant cardiologist specializing in clinical cardiology, hypertension control, ECG/Echocardiography evaluation, and preventative coronary care.",
                phone="+91 98200 45671",
                email="rajesh.iyer@heartcare.example.org",
                avatar="/static/images/doctor-placeholder.svg"
            ),
            Doctor(
                name="Dr. Priya Patel",
                specialty="Dermatologist",
                qualifications="MBBS, DVD, MD (Dermatology)",
                experience_years=8,
                verification_status=True,
                clinic_name="Glow & Care Skin Clinic",
                clinic_address="88, 100 Feet Road, Indiranagar",
                city="Bengaluru",
                latitude=12.9784,
                longitude=77.6408,
                distance_km=3.1,
                consultation_fee=750,
                rating=4.8,
                reviews_count=142,
                available_today=False,
                availability_info="Next Available: Tomorrow 10:00 AM",
                languages="English, Hindi, Kannada, Gujarati",
                about="Dr. Priya Patel specializes in clinical dermatology, acne management, allergy diagnostics, and hair-scalp therapies with high patient satisfaction ratings.",
                phone="+91 98450 12389",
                email="priya.patel@glowcare.example.com",
                avatar="/static/images/doctor-placeholder.svg"
            ),
            Doctor(
                name="Dr. Sameer Deshmukh",
                specialty="Dentist",
                qualifications="BDS, MDS (Prosthodontics)",
                experience_years=9,
                verification_status=True,
                clinic_name="SmileCraft Dental Studio",
                clinic_address="Shop 12, Crystal Heights, FC Road",
                city="Pune",
                latitude=18.5204,
                longitude=73.8400,
                distance_km=1.8,
                consultation_fee=500,
                rating=4.75,
                reviews_count=98,
                available_today=True,
                availability_info="Available Today: 2:00 PM - 6:30 PM",
                languages="English, Hindi, Marathi",
                about="Dr. Sameer provides painless dental treatments including restorative dentistry, root canals, teeth whitening, and preventive oral hygiene consultations.",
                phone="+91 98230 77412",
                email="sameer@smilecraft.example.com",
                avatar="/static/images/doctor-placeholder.svg"
            ),
            Doctor(
                name="Dr. Kavita Nair",
                specialty="Pediatrician",
                qualifications="MBBS, DCH, DNB (Pediatrics)",
                experience_years=12,
                verification_status=True,
                clinic_name="Little Wonders Child Health",
                clinic_address="Plot 19, Banjara Hills Road No. 12",
                city="Hyderabad",
                latitude=17.4156,
                longitude=78.4350,
                distance_km=2.9,
                consultation_fee=650,
                rating=4.9,
                reviews_count=215,
                available_today=True,
                availability_info="Available Today: 11:00 AM - 3:00 PM",
                languages="English, Hindi, Telugu, Malayalam",
                about="Dr. Kavita Nair is a renowned pediatrician with special focus on newborn screening, child nutrition, immunization schedules, and childhood asthma management.",
                phone="+91 98490 66321",
                email="kavita.nair@littlewonders.example.org",
                avatar="/static/images/doctor-placeholder.svg"
            ),
            Doctor(
                name="Dr. Arvind Varma",
                specialty="Eye Specialist",
                qualifications="MBBS, MS (Ophthalmology), Fellow Cornea",
                experience_years=14,
                verification_status=True,
                clinic_name="VisionPlus Laser Eye Center",
                clinic_address="14/2, Central Avenue, Green Park",
                city="Delhi NCR",
                latitude=28.5580,
                longitude=77.2020,
                distance_km=4.0,
                consultation_fee=700,
                rating=4.85,
                reviews_count=164,
                available_today=True,
                availability_info="Available Today: 3:00 PM - 7:00 PM",
                languages="English, Hindi",
                about="Dr. Arvind Varma is an experienced ophthalmologist handling digital eye strain, diabetic retinopathy screening, cataract consultation, and corrective vision care.",
                phone="+91 98100 88231",
                email="arvind.varma@visionplus.example.com",
                avatar="/static/images/doctor-placeholder.svg"
            ),
            Doctor(
                name="Dr. Rohan Gupta",
                specialty="General Physician",
                qualifications="MBBS, DNB (Family Medicine)",
                experience_years=6,
                verification_status=False,
                clinic_name="Gupta Family Clinic",
                clinic_address="B-41, Vikas Marg, Preet Vihar",
                city="Delhi NCR",
                latitude=28.6350,
                longitude=77.2950,
                distance_km=5.6,
                consultation_fee=None,
                rating=4.3,
                reviews_count=32,
                available_today=True,
                availability_info="Verification Pending — Inquire with clinic",
                languages="English, Hindi",
                about="Dr. Rohan Gupta offers primary care and home-visit assessments for elderly patients. Provider documentation is currently undergoing MediNear verification.",
                phone="+91 98111 99012",
                email="rohan.gupta@example.com",
                avatar="/static/images/doctor-placeholder.svg"
            ),
            Doctor(
                name="Dr. Meenakshi Sundaram",
                specialty="Cardiologist",
                qualifications="MBBS, MD, DM (Cardiology)",
                experience_years=19,
                verification_status=True,
                clinic_name="Apex Cardiac Institute",
                clinic_address="7th Floor, Tower B, Koramangala",
                city="Bengaluru",
                latitude=12.9352,
                longitude=77.6245,
                distance_km=4.5,
                consultation_fee=1100,
                rating=4.92,
                reviews_count=278,
                available_today=False,
                availability_info="Next Available: Tomorrow 4:00 PM",
                languages="English, Hindi, Tamil, Kannada",
                about="Leading consultant in cardiovascular disease management, post-stent cardiac rehabilitation, and diagnostic lipidology.",
                phone="+91 98440 33119",
                email="meenakshi.s@apexcardiac.example.org",
                avatar="/static/images/doctor-placeholder.svg"
            )
        ]
        database.session.add_all(doctors_data)
        database.session.commit()

    # 3. Seed Hospitals
    if Hospital.query.count() == 0:
        hospitals_data = [
            Hospital(
                name="Apollo Multi-Specialty Hospital",
                category="Super-Speciality Tertiary Care",
                address="Sarita Vihar, Delhi Mathura Road",
                city="Delhi NCR",
                latitude=28.5284,
                longitude=77.2917,
                distance_km=3.2,
                emergency_24x7=True,
                icu_beds_available=14,
                emergency_contact="+91 11 2692 5858",
                general_contact="+91 11 2692 5801",
                services_str="24x7 Emergency Trauma, Cardiac Cath Lab, ICU & NICU, Advanced CT/MRI, Stroke Unit, Blood Bank",
                rating=4.8
            ),
            Hospital(
                name="Fortis Healthcare & Research Institute",
                category="Multispecialty Hospital",
                address="Sector 44, Opposite Huda City Centre",
                city="Delhi NCR",
                latitude=28.4595,
                longitude=77.0726,
                distance_km=4.8,
                emergency_24x7=True,
                icu_beds_available=8,
                emergency_contact="+91 124 492 1021",
                general_contact="+91 124 492 1000",
                services_str="24x7 Emergency, Oncology Wing, Organ Transplant, Dialysis Unit, Ambulance Fleet",
                rating=4.7
            ),
            Hospital(
                name="Lilavati Hospital & Research Centre",
                category="Premier Multi-Specialty Hospital",
                address="A-791, Bandra Reclamation, Bandra West",
                city="Mumbai",
                latitude=19.0515,
                longitude=72.8290,
                distance_km=2.1,
                emergency_24x7=True,
                icu_beds_available=6,
                emergency_contact="+91 22 2675 1000",
                general_contact="+91 22 2675 1555",
                services_str="24x7 Cardiac Emergency, Pediatric Intensive Care, Neuro-trauma, Pathology Lab 24/7",
                rating=4.85
            ),
            Hospital(
                name="Manipal Hospital Whitefield",
                category="Multi-Specialty Healthcare",
                address="143, HAL Old Airport Road, Kodihalli",
                city="Bengaluru",
                latitude=12.9592,
                longitude=77.6569,
                distance_km=5.0,
                emergency_24x7=True,
                icu_beds_available=11,
                emergency_contact="+91 80 2502 4444",
                general_contact="+91 80 2502 3333",
                services_str="Accident & Emergency 24/7, Critical Care Medicine, Comprehensive Diagnostics, Pharmacy 24/7",
                rating=4.75
            )
        ]
        database.session.add_all(hospitals_data)
        database.session.commit()

    # 4. Seed Pharmacies
    if Pharmacy.query.count() == 0:
        pharmacies_data = [
            Pharmacy(
                name="MedPlus 24x7 Pharmacy & Healthcare",
                address="Shop 4, Ground Floor, Central Market, Sector 18",
                city="Delhi NCR",
                latitude=28.5710,
                longitude=77.3215,
                distance_km=0.8,
                is_24x7=True,
                home_delivery=True,
                contact="+91 11 4102 9911",
                stock_sample_json=json.dumps({
                    "Paracetamol 650mg": {"status": "In Stock", "updated": "15 mins ago"},
                    "Amoxicillin 500mg": {"status": "In Stock", "updated": "45 mins ago"},
                    "Cetirizine 10mg": {"status": "In Stock", "updated": "20 mins ago"},
                    "Azithromycin 500mg": {"status": "Limited Stock", "updated": "1 hour ago"},
                    "Insulin Glargine Pen": {"status": "Contact to Verify", "updated": "3 hours ago"}
                })
            ),
            Pharmacy(
                name="Apollo Pharmacy — Express Delivery",
                address="Plot 12, Hill Road, Bandra West",
                city="Mumbai",
                latitude=19.0550,
                longitude=72.8310,
                distance_km=1.4,
                is_24x7=True,
                home_delivery=True,
                contact="+91 22 2640 1818",
                stock_sample_json=json.dumps({
                    "Paracetamol 650mg": {"status": "In Stock", "updated": "10 mins ago"},
                    "Metformin 500mg": {"status": "In Stock", "updated": "30 mins ago"},
                    "Pantoprazole 40mg": {"status": "In Stock", "updated": "25 mins ago"},
                    "Atorvastatin 10mg": {"status": "In Stock", "updated": "1 hour ago"},
                    "Salbutamol Inhaler": {"status": "In Stock", "updated": "50 mins ago"}
                })
            ),
            Pharmacy(
                name="Wellness Forever Chemist & Superstore",
                address="100 Feet Road, Near Metro Station, Indiranagar",
                city="Bengaluru",
                latitude=12.9770,
                longitude=77.6420,
                distance_km=2.2,
                is_24x7=True,
                home_delivery=True,
                contact="+91 80 4115 8800",
                stock_sample_json=json.dumps({
                    "Paracetamol 650mg": {"status": "In Stock", "updated": "5 mins ago"},
                    "ORS Sachet": {"status": "In Stock", "updated": "15 mins ago"},
                    "Vitamin C 500mg": {"status": "In Stock", "updated": "2 hours ago"},
                    "Dolo 650": {"status": "In Stock", "updated": "20 mins ago"},
                    "Nebulizer Kit": {"status": "Limited Stock", "updated": "4 hours ago"}
                })
            ),
            Pharmacy(
                name="City Care Day Chemist",
                address="Shop 2, Laxmi Nivas, FC Road, Shivajinagar",
                city="Pune",
                latitude=18.5240,
                longitude=73.8420,
                distance_km=1.9,
                is_24x7=False,
                home_delivery=False,
                contact="+91 20 2553 4411",
                stock_sample_json=json.dumps({
                    "Paracetamol 650mg": {"status": "In Stock", "updated": "1 hour ago"},
                    "Ibuprofen 400mg": {"status": "In Stock", "updated": "2 hours ago"},
                    "Cough Syrup (Guaifenesin)": {"status": "In Stock", "updated": "2 hours ago"}
                })
            )
        ]
        database.session.add_all(pharmacies_data)
        database.session.commit()

    # 5. Seed Initial Appointments for Demo Patient
    if Appointment.query.count() == 0:
        demo_user = User.query.filter_by(email="patient@example.com").first()
        doc1 = Doctor.query.filter_by(name="Dr. Ananya Sharma").first()
        doc2 = Doctor.query.filter_by(name="Dr. Rajesh Iyer").first()
        doc4 = Doctor.query.filter_by(name="Dr. Sameer Deshmukh").first()

        sample_appointments = []
        if doc1:
            sample_appointments.append(Appointment(
                booking_ref="APT-9041",
                user_id=demo_user.id if demo_user else None,
                doctor_id=doc1.id,
                patient_name="Arun Kumar",
                patient_phone="9876543210",
                patient_email="patient@example.com",
                appointment_date="2026-10-20",
                time_slot="05:30 PM",
                mode="In-Person Clinic Visit",
                symptoms="Follow-up checkup for routine blood panel review",
                fee="₹600",
                status="Confirmed"
            ))
        if doc2:
            sample_appointments.append(Appointment(
                booking_ref="APT-8822",
                user_id=demo_user.id if demo_user else None,
                doctor_id=doc2.id,
                patient_name="Arun Kumar",
                patient_phone="9876543210",
                patient_email="patient@example.com",
                appointment_date="2026-10-25",
                time_slot="06:00 PM",
                mode="Cardiology Consultation",
                symptoms="Hypertension monitoring and ECG evaluation",
                fee="₹1,200",
                status="Pending"
            ))
        if doc4:
            sample_appointments.append(Appointment(
                booking_ref="APT-7104",
                user_id=demo_user.id if demo_user else None,
                doctor_id=doc4.id,
                patient_name="Arun Kumar",
                patient_phone="9876543210",
                patient_email="patient@example.com",
                appointment_date="2026-09-28",
                time_slot="03:00 PM",
                mode="Dental Scaling & Checkup",
                symptoms="Routine teeth cleaning",
                fee="₹500",
                status="Completed"
            ))

        database.session.add_all(sample_appointments)
        database.session.commit()

# -----------------------------------------------------------------------------
# Standalone Model Diagnostics Runner
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.modules.setdefault('models', sys.modules[__name__])
    print("=" * 60)
    print(" MediNear AI — Database Models & Diagnostics (models.py)")
    print("=" * 60)
    try:
        from app import app
        with app.app_context():
            print(f" [+] Registered Users:       {User.query.count()}")
            print(f" [+] Listed Doctors:        {Doctor.query.count()}")
            print(f" [+] Partner Hospitals:     {Hospital.query.count()}")
            print(f" [+] Verified Pharmacies:   {Pharmacy.query.count()}")
            print(f" [+] Total Appointments:    {Appointment.query.count()}")
            print("\n [SUCCESS] Models and SQLite database verified successfully.")
    except Exception as e:
        print(f" [ERROR] Could not inspect database models: {e}")
        sys.exit(1)
