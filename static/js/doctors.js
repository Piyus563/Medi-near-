/**
 * MediNear AI — Smart Healthcare & Doctor Finder
 * Doctors Listing & Client Filtering Script (doctors.js)
 */

document.addEventListener('DOMContentLoaded', () => {
  initDoctorFiltersAndSort();
});

function initDoctorFiltersAndSort() {
  const grid = document.getElementById('doctorsCardGrid');
  if (!grid) return;

  const items = Array.from(grid.querySelectorAll('.doctor-listing-item'));
  const sortSelector = document.getElementById('sortSelector');
  const searchInput = document.getElementById('searchKeyword');
  const specialtyFilter = document.getElementById('specialtyFilter');
  const cityInput = document.getElementById('cityFilter');
  const emptyState = document.getElementById('noDoctorsEmptyState');
  const resultsCount = document.getElementById('resultsCount');
  const loadingSpinner = document.getElementById('doctorsLoadingSpinner');

  function applyFiltersAndSort() {
    const query = (searchInput?.value || '').trim().toLowerCase();
    const specialty = (specialtyFilter?.value || '').trim();
    const city = (cityInput?.value || '').trim().toLowerCase();
    const sortVal = sortSelector?.value || 'distance_asc';

    let visibleCount = 0;

    items.forEach(item => {
      const name = item.getAttribute('data-name') || '';
      const docSpecialty = item.getAttribute('data-specialty') || '';
      const docCity = item.getAttribute('data-city') || '';

      const matchQuery = !query || name.includes(query) || docSpecialty.toLowerCase().includes(query);
      const matchSpecialty = !specialty || docSpecialty === specialty;
      const matchCity = !city || city.includes('current location') || city.includes('near you') || docCity.includes(city);

      if (matchQuery && matchSpecialty && matchCity) {
        item.classList.remove('d-none');
        visibleCount++;
      } else {
        item.classList.add('d-none');
      }
    });

    // Update count display
    if (resultsCount) {
      resultsCount.textContent = visibleCount;
    }

    // Toggle empty state
    if (emptyState) {
      if (visibleCount === 0) {
        emptyState.classList.remove('d-none');
      } else {
        emptyState.classList.add('d-none');
      }
    }

    // Sort visible items
    items.sort((a, b) => {
      const distA = parseFloat(a.getAttribute('data-distance')) || 0;
      const distB = parseFloat(b.getAttribute('data-distance')) || 0;
      const ratingA = parseFloat(a.getAttribute('data-rating')) || 0;
      const ratingB = parseFloat(b.getAttribute('data-rating')) || 0;
      const expA = parseInt(a.getAttribute('data-experience')) || 0;
      const expB = parseInt(b.getAttribute('data-experience')) || 0;
      const feeA = parseInt(a.getAttribute('data-fee')) || 99999;
      const feeB = parseInt(b.getAttribute('data-fee')) || 99999;

      switch (sortVal) {
        case 'distance_asc':
          return distA - distB;
        case 'rating_desc':
          return ratingB - ratingA;
        case 'experience_desc':
          return expB - expA;
        case 'fee_asc':
          return feeA - feeB;
        case 'fee_desc':
          return feeB - feeA;
        default:
          return 0;
      }
    });

    // Re-append sorted elements to the DOM
    items.forEach(item => grid.appendChild(item));
  }

  // Live filter event listeners
  if (sortSelector) {
    sortSelector.addEventListener('change', () => {
      if (loadingSpinner) {
        loadingSpinner.classList.remove('d-none');
        grid.style.opacity = '0.5';
        setTimeout(() => {
          applyFiltersAndSort();
          loadingSpinner.classList.add('d-none');
          grid.style.opacity = '1';
        }, 150);
      } else {
        applyFiltersAndSort();
      }
    });
  }

  if (searchInput) {
    searchInput.addEventListener('input', applyFiltersAndSort);
  }

  if (specialtyFilter) {
    specialtyFilter.addEventListener('change', applyFiltersAndSort);
  }

  if (cityInput) {
    cityInput.addEventListener('input', applyFiltersAndSort);
  }
}
