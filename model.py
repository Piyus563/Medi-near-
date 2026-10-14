"""
MediNear AI — Database Model Interface (model.py / models.py)
Provides direct and backward-compatible access to all SQLAlchemy database models and utilities.
"""

from models import (
    db,
    User,
    Doctor,
    Hospital,
    Pharmacy,
    Appointment,
    seed_database,
    get_utc_now
)

__all__ = [
    "db",
    "User",
    "Doctor",
    "Hospital",
    "Pharmacy",
    "Appointment",
    "seed_database",
    "get_utc_now"
]

# -----------------------------------------------------------------------------
# Standalone Model Diagnostics Runner
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    print("=" * 60)
    print(" MediNear AI — Database Model Diagnostics (model.py)")
    print("=" * 60)
    try:
        from app import app
        with app.app_context():
            print(f" [+] Registered Users:       {User.query.count()}")
            print(f" [+] Listed Doctors:        {Doctor.query.count()}")
            print(f" [+] Partner Hospitals:     {Hospital.query.count()}")
            print(f" [+] Verified Pharmacies:   {Pharmacy.query.count()}")
            print(f" [+] Total Appointments:    {Appointment.query.count()}")
            print("\n [SUCCESS] All models loaded and verified successfully with SQLite.")
    except Exception as e:
        print(f" [ERROR] Could not inspect database models: {e}")
        sys.exit(1)
