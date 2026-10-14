# MediNear AI — Smart Healthcare & Doctor Finder

A modern, responsive healthcare discovery and navigation web platform built for a **BTech CSE (AI/ML) Major Project** and **Digital Health Startup Prototype**.

MediNear AI connects patients with nearby verified medical doctors, 24/7 emergency hospitals, clinical diagnostic centers, and local pharmacies with stock availability reporting and AI-assisted specialty triaging.

---

## 🌟 Key Features

1. **Intelligent Healthcare Search & Geolocation**:
   - Search by specialty, doctor name, symptoms, or medical condition.
   - GPS-enabled "Auto Detect Location" and city/locality filtering.
2. **Medical Practitioner Listings**:
   - Clear distinction between Verified and Pending medical practitioners.
   - Real-time client-side sorting by nearest distance, highest rating, clinical experience, and consultation fees.
   - Comprehensive doctor profiles with qualifications, languages, consultation fees, clinic hours, and OpenStreetMap/Leaflet route visualization.
3. **24/7 Emergency Hospital Locator**:
   - Interactive Leaflet map with emergency markers.
   - One-tap national ambulance calling (`108` / `112`).
   - Verified hospital emergency phone desk numbers and active ICU bed availability indicators.
4. **Pharmacy & Medicine Stock Finder**:
   - Search by common medicine name (e.g. Paracetamol, Amoxicillin, Insulin) or pharmacy brand.
   - 24/7 chemist filter and home delivery badges.
   - Explicit last-updated timestamps for reported inventory with medical disclaimers.
   - Prescription inquiry modal for contacting partner pharmacies.
5. **AI Healthcare Assistant & Clinical Triage**:
   - Bilingual support (**English** & **हिन्दी**).
   - Acute emergency red-flag detection (chest pain, shortness of breath) routing users directly to ambulance helplines and trauma centers.
   - Symptom-to-specialist matching cards linking directly into filtered provider listings.
   - Safe client-side fallback if the AI endpoint is offline.
6. **Patient Portal & Dashboard**:
   - Session-managed upcoming appointment requests.
   - Instant appointment scheduling modal with date constraints and time-slot selection.
   - Appointment history, saved/bookmarked doctors, and cancellation workflow with confirmation modal.
7. **Administrative & Moderation Console**:
   - Summary KPI cards (Doctors, Partner Hospitals, Active Pharmacies, Pending Inquiries).
   - Provider management table with live search and verification status toggles.
   - Add new healthcare provider modal.
   - Appointment queue review (Approve / Decline).

---

## 💻 Tech Stack & Architecture

- **Backend**: Python 3.12, Flask 3.0.3, Jinja2 template engine
- **Frontend Core**: Semantic HTML5, Vanilla CSS3, Vanilla ES6+ JavaScript
- **CSS Framework**: Bootstrap 5.3.3 via CDN (clean medical design system)
- **Icons**: Bootstrap Icons & Font Awesome 6.5.2
- **Maps**: Leaflet.js with OpenStreetMap tiles (free, open, no proprietary API keys needed)
- **Zero Frontend Framework Lock-in**: No React, Next.js, or TypeScript — 100% lightweight and directly integrated with Flask templates.

---

## 📁 Directory Structure

```
MediNear AI – Smart Healthcare and Doctor Finder/
├── app.py                      # Flask application routes, session management & AI API
├── models.py                   # Data classes, demo provider records & helper queries
├── requirements.txt            # Python dependencies (Flask, Jinja2, Werkzeug)
├── README.md                   # Project documentation and execution instructions
├── templates/
│   ├── base.html               # Master layout with navbar, footer, emergency banner & toasts
│   ├── index.html              # Home page with hero, search, categories, and verified previews
│   ├── doctors.html            # Doctor listings with sorting, filters, and empty states
│   ├── doctor_details.html     # Doctor profile, clinic hours, Leaflet map, and booking card
│   ├── hospitals.html          # Hospitals directory with interactive Leaflet map & emergency desks
│   ├── pharmacies.html         # Pharmacies with stock reporting, 24x7 filter, and inquiry modal
│   ├── ai_assistant.html       # AI triage chat interface with English/Hindi language toggle
│   ├── dashboard.html          # Patient portal with appointments, history, and cancel action
│   ├── login.html              # Clean sign-in screen with password visibility reveal
│   ├── register.html           # Registration form with patient/doctor role selector
│   ├── admin.html              # Healthcare provider moderation and appointment queue console
│   └── components/
│       └── appointment_modal.html # Reusable modal for doctor appointment requests
└── static/
    ├── css/
    │   ├── style.css           # Core medical design system, color tokens, cards, and animations
    │   └── dashboard.css       # SaaS dashboard layouts, KPI widgets, and status pills
    ├── js/
    │   ├── main.js             # Global utilities (toasts, geolocation, favorites in localStorage)
    │   ├── doctors.js          # Live search, specialty filtering, and multi-criteria sorting
    │   ├── ai_assistant.js     # AI triage chatbot engine with emergency detection & Hindi toggle
    │   └── appointments.js     # Appointment modal handler, validation, and session persistence
    └── images/
        ├── logo.svg            # Custom vector MediNear AI brand logo
        └── doctor-placeholder.svg # Neutral medical doctor avatar with verified badge
```

---

## 🚀 How to Run the Application

### 1. Prerequisites
Ensure you have **Python 3.10+** installed on your system.

### 2. Install Dependencies
Open your terminal in the project directory and run:
```bash
pip install -r requirements.txt
```

### 3. Start the Flask Server
Run the application entry point:
```bash
python app.py
```

### 4. Open in Your Web Browser
Navigate to:
```
http://127.0.0.1:5000
```

### 5. Run the Automated Test Suite
To verify the database, search queries, password hashing, authentication, and duplicate booking prevention:
```bash
python test_backend.py
```

---

## 🔑 Demo Testing Accounts

| Role | Email | Password | Access Privileges |
|---|---|---|---|
| **Patient** | `patient@example.com` | `Patient@123` | Patient Portal, Bookings, Dashboard |
| **Administrator** | `admin@example.com` | `Admin@123` | Provider Moderation, Verification, Queue Review |

---

## 🌐 Supported Application Routes

| Route | Template / Method | Description |
|---|---|---|
| `/` | `GET` &rarr; `index.html` | Home landing page with hero, search, categories, and verified previews |
| `/doctors` | `GET` &rarr; `doctors.html` | Doctor listing page with filtering by keyword, specialty, and city |
| `/doctor/<int:doctor_id>` | `GET` &rarr; `doctor_details.html` | Doctor profile with clinic Leaflet map and appointment booking form |
| `/hospitals` | `GET` &rarr; `hospitals.html` | Emergency hospital directory with interactive Leaflet locator |
| `/pharmacies` | `GET` &rarr; `pharmacies.html` | Local chemist directory with stock status and inquiry modal |
| `/ai-assistant` | `GET` &rarr; `ai_assistant.html` | AI healthcare specialty navigator (English & Hindi) |
| `/dashboard` | `GET` &rarr; `dashboard.html` | Patient dashboard for upcoming and past appointments |
| `/login` | `GET` & `POST` &rarr; `login.html` | Secure sign-in with password hashing and session management |
| `/register` | `GET` & `POST` &rarr; `register.html` | User registration with patient/doctor role selection |
| `/logout` | `GET` | Clears user session and logs out |
| `/admin` | `GET` &rarr; `admin.html` | Healthcare provider moderation and request queue console (Admin only) |
| `/health` | `GET` | Health check endpoint returning database connectivity status |
| `/api/appointments/request` | `POST` (JSON) | Appointment request with duplicate slot prevention and database transactions |
| `/api/appointments/<ref>/cancel` | `POST` (JSON) | Cancels an appointment in SQLite |
| `/api/admin/providers/<id>/toggle-status` | `POST` (JSON) | Moderation endpoint toggling doctor verification status |
| `/api/admin/providers/add` | `POST` (JSON) | Adds a new doctor to the SQLite database |
| `/api/admin/appointments/<id>/status` | `POST` (JSON) | Updates appointment status (Confirmed/Cancelled) |
| `/api/ai-chat` | `POST` (JSON) | AI specialty triaging and red-flag emergency detection |

---

## 🛡️ Medical Disclaimer
MediNear AI is an informational discovery and navigation directory designed for educational and prototype demonstration purposes. It does **not** provide formal medical advice, medical diagnoses, or prescriptions. In the event of acute symptoms, chest discomfort, shortness of breath, or trauma, contact emergency medical response immediately (Call **108** or **112**).
