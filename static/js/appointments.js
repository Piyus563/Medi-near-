/**
 * MediNear AI — Smart Healthcare & Doctor Finder
 * Appointment Booking Modal Script (appointments.js)
 */

document.addEventListener('DOMContentLoaded', () => {
  initAppointmentModalTriggers();
  initAppointmentFormSubmission();
  initDateConstraints();
});

function initDateConstraints() {
  const dateInput = document.getElementById('appointmentDateInput');
  if (dateInput) {
    const today = new Date();
    // Default to tomorrow or today
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const dd = String(today.getDate()).padStart(2, '0');
    dateInput.min = `${yyyy}-${mm}-${dd}`;
    dateInput.value = `${yyyy}-${mm}-${dd}`;
  }
}

function initAppointmentModalTriggers() {
  const modalElement = document.getElementById('appointmentBookingModal');
  if (!modalElement) return;

  const bsModal = new bootstrap.Modal(modalElement);

  document.addEventListener('click', (e) => {
    const trigger = e.target.closest('.btn-request-appointment-modal');
    if (!trigger) return;

    e.preventDefault();

    const doctorId = trigger.getAttribute('data-doctor-id') || '';
    const doctorName = trigger.getAttribute('data-doctor-name') || 'Healthcare Provider';
    const doctorSpecialty = trigger.getAttribute('data-doctor-specialty') || 'General Practice';
    const doctorFee = trigger.getAttribute('data-doctor-fee');

    // Populate modal fields
    const modalDocId = document.getElementById('modalDoctorId');
    const modalDocName = document.getElementById('modalDoctorName');
    const modalDocSpecialty = document.getElementById('modalDoctorSpecialty');
    const modalDocFee = document.getElementById('modalDoctorFee');

    if (modalDocId) modalDocId.value = doctorId;
    if (modalDocName) modalDocName.textContent = doctorName;
    if (modalDocSpecialty) modalDocSpecialty.textContent = doctorSpecialty;
    if (modalDocFee) {
      modalDocFee.textContent = doctorFee && doctorFee !== 'None' ? `₹${doctorFee}` : 'Inquire Clinic';
    }

    bsModal.show();
  });
}

function initAppointmentFormSubmission() {
  const form = document.getElementById('appointmentRequestForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!form.checkValidity()) {
      e.stopPropagation();
      form.classList.add('was-validated');
      return;
    }

    const submitBtn = document.getElementById('submitAppointmentBtn');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span> Confirming...';

    const formData = new FormData(form);
    const appointmentData = {
      doctor_id: formData.get('doctor_id'),
      doctor_name: document.getElementById('modalDoctorName')?.textContent || 'Doctor',
      specialty: document.getElementById('modalDoctorSpecialty')?.textContent || '',
      patient_name: formData.get('patient_name'),
      patient_phone: formData.get('patient_phone'),
      patient_email: formData.get('patient_email'),
      mode: formData.get('mode'),
      date: formData.get('date'),
      time_slot: formData.get('time_slot'),
      symptoms: formData.get('symptoms'),
      fee: document.getElementById('modalDoctorFee')?.textContent || '₹600'
    };

    try {
      // Send request to Flask API endpoint
      const response = await fetch('/api/appointments/request', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': window.getCsrfToken ? window.getCsrfToken() : ''
        },
        body: JSON.stringify(appointmentData)
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        showToast(result.message || 'This time slot is already reserved. Please select another slot.', 'warning', 6500);
        return;
      }

      // Close modal on verified database confirmation
      const modalElement = document.getElementById('appointmentBookingModal');
      const bsModal = bootstrap.Modal.getInstance(modalElement);
      if (bsModal) bsModal.hide();

      form.reset();
      form.classList.remove('was-validated');

      showToast(result.message || `Appointment request confirmed for ${appointmentData.doctor_name}! Booking ID: ${result.appointment_id}.`, 'success', 6000);

    } catch (err) {
      console.error('API appointment request error:', err);
      showToast('Connection error while contacting server. Please try again.', 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;
    }
  });
}

function persistAppointmentLocally(data, bookingId) {
  try {
    const key = 'medinear_custom_appointments';
    const existing = JSON.parse(localStorage.getItem(key) || '[]');
    const newEntry = {
      id: bookingId,
      doctor_id: data.doctor_id,
      doctor_name: data.doctor_name,
      specialty: data.specialty,
      clinic: 'Care Clinic Facility',
      patient_name: data.patient_name,
      date: data.date,
      time_slot: data.time_slot,
      mode: data.mode,
      status: 'Confirmed',
      badge_class: 'badge-status-confirmed',
      fee: data.fee,
      can_cancel: true
    };
    existing.unshift(newEntry);
    localStorage.setItem(key, JSON.stringify(existing));
  } catch (err) {
    console.error('Failed to save appointment locally:', err);
  }
}
