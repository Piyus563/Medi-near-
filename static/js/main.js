/**
 * MediNear AI — Smart Healthcare & Doctor Finder
 * Global Client Script (main.js)
 */

/**
 * Global CSRF Token Extractor for AJAX fetch requests
 */
window.getCsrfToken = function() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
};

document.addEventListener('DOMContentLoaded', () => {
  initNavbarScroll();
  initGeolocationButtons();
  initFavoriteButtons();
});

/**
 * Navbar subtle shadow on scroll
 */
function initNavbarScroll() {
  const navbar = document.getElementById('mainNavbar');
  if (!navbar) return;

  window.addEventListener('scroll', () => {
    if (window.scrollY > 20) {
      navbar.classList.add('shadow-sm');
    } else {
      navbar.classList.remove('shadow-sm');
    }
  });
}

/**
 * Toast Notification Dispatcher
 * @param {string} message - Notification text
 * @param {'success'|'info'|'warning'|'error'} type - Style category
 * @param {number} duration - Milliseconds before auto-dismiss
 */
function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const iconMap = {
    success: 'bi-check-circle-fill text-success',
    info: 'bi-info-circle-fill text-primary',
    warning: 'bi-exclamation-triangle-fill text-warning',
    error: 'bi-x-circle-fill text-danger'
  };

  const toast = document.createElement('div');
  toast.className = `medinear-toast toast-${type}`;
  toast.setAttribute('role', 'alert');
  toast.innerHTML = `
    <i class="bi ${iconMap[type] || iconMap.info} fs-5 flex-shrink-0"></i>
    <div class="flex-grow-1" style="font-size: 0.9rem; font-weight: 500;">${message}</div>
    <button type="button" class="btn-close ms-2" style="font-size: 0.75rem;" aria-label="Close"></button>
  `;

  const closeBtn = toast.querySelector('.btn-close');
  closeBtn.addEventListener('click', () => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(40px)';
    setTimeout(() => toast.remove(), 250);
  });

  container.appendChild(toast);

  if (duration > 0) {
    setTimeout(() => {
      if (toast.parentElement) {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(40px)';
        setTimeout(() => toast.remove(), 250);
      }
    }, duration);
  }
}

/**
 * Geolocation button detection & fill-in
 */
function initGeolocationButtons() {
  const locateBtns = document.querySelectorAll('.btn-locate-me');
  locateBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const targetInputId = btn.getAttribute('data-target-input') || 'searchLocationInput';
      const targetInput = document.getElementById(targetInputId);

      if (!navigator.geolocation) {
        showToast('Geolocation is not supported by your browser', 'warning');
        return;
      }

      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Detecting...';
      btn.disabled = true;

      navigator.geolocation.getCurrentPosition(
        (position) => {
          btn.innerHTML = '<i class="bi bi-geo-alt-fill text-success"></i> Located';
          btn.disabled = false;
          if (targetInput) {
            targetInput.value = 'Current Location (Near You)';
            targetInput.classList.add('border-primary');
          }
          showToast('Location detected successfully! Showing nearby healthcare providers.', 'success');
        },
        (error) => {
          btn.innerHTML = '<i class="bi bi-crosshair"></i> Use My Location';
          btn.disabled = false;
          let msg = 'Could not access location. Please enter your city manually.';
          if (error.code === error.PERMISSION_DENIED) {
            msg = 'Location permission denied. Please enter your city manually.';
          }
          showToast(msg, 'warning');
        },
        { timeout: 8000 }
      );
    });
  });
}

/**
 * Saved / Favorite Doctors in localStorage
 */
const FAVORITES_KEY = 'medinear_favorite_doctors';

function getFavoriteDoctors() {
  try {
    const raw = localStorage.getItem(FAVORITES_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
}

function toggleFavoriteDoctor(doctorId, doctorName) {
  let favs = getFavoriteDoctors();
  const idNum = parseInt(doctorId, 10);
  const existsIndex = favs.indexOf(idNum);

  if (existsIndex > -1) {
    favs.splice(existsIndex, 1);
    localStorage.setItem(FAVORITES_KEY, JSON.stringify(favs));
    showToast(`Removed ${doctorName || 'doctor'} from saved list.`, 'info');
    return false;
  } else {
    favs.push(idNum);
    localStorage.setItem(FAVORITES_KEY, JSON.stringify(favs));
    showToast(`Saved ${doctorName || 'doctor'} to your saved providers!`, 'success');
    return true;
  }
}

function initFavoriteButtons() {
  const favs = getFavoriteDoctors();
  document.querySelectorAll('.btn-favorite-heart').forEach(btn => {
    const docId = parseInt(btn.getAttribute('data-doctor-id'), 10);
    const docName = btn.getAttribute('data-doctor-name') || 'Doctor';
    if (favs.includes(docId)) {
      btn.classList.add('active');
      btn.innerHTML = '<i class="bi bi-heart-fill"></i>';
    }

    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const isSaved = toggleFavoriteDoctor(docId, docName);
      if (isSaved) {
        btn.classList.add('active');
        btn.innerHTML = '<i class="bi bi-heart-fill"></i>';
      } else {
        btn.classList.remove('active');
        btn.innerHTML = '<i class="bi bi-heart"></i>';
      }
    });
  });
}
