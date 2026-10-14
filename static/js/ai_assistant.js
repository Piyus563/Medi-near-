/**
 * MediNear AI — Smart Healthcare & Doctor Finder
 * AI Assistant Chat Script (ai_assistant.js)
 */

document.addEventListener('DOMContentLoaded', () => {
  initAiAssistant();
});

function initAiAssistant() {
  const form = document.getElementById('aiChatInputForm');
  const input = document.getElementById('aiUserInput');
  const chatFlow = document.getElementById('chatMessagesFlow');
  const typingIndicator = document.getElementById('aiTypingIndicator');
  const clearBtn = document.getElementById('btnClearChat');
  const langToggleGroup = document.getElementById('langToggleGroup');
  const promptsTray = document.getElementById('suggestedPromptsTray');

  let currentLang = 'en'; // 'en' or 'hi'

  // Language toggle handling
  if (langToggleGroup) {
    langToggleGroup.querySelectorAll('.lang-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        langToggleGroup.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentLang = btn.getAttribute('data-lang') || 'en';
        updatePromptsLanguage(currentLang);
      });
    });
  }

  function updatePromptsLanguage(lang) {
    if (!promptsTray || !input) return;

    if (lang === 'hi') {
      input.placeholder = "अपने लक्षण या स्वास्थ्य संबंधी सवाल यहाँ लिखें (उदा. 'बुखार और खांसी', 'त्वचा पर लाल दाने')...";
      promptsTray.innerHTML = `
        <span class="text-muted fw-semibold me-1" style="font-size: 0.78rem;">सुझाव:</span>
        <button type="button" class="prompt-chip" data-prompt="त्वचा के डॉक्टर या डर्मेटोलॉजिस्ट खोजें">
          <i class="bi bi-hand-dots"></i> डर्मेटोलॉजिस्ट खोजें
        </button>
        <button type="button" class="prompt-chip" data-prompt="दांत के दर्द के लिए डेंटिस्ट खोजें">
          <i class="bi bi-bandaid"></i> दांतों के डॉक्टर (डेंटिस्ट)
        </button>
        <button type="button" class="prompt-chip" data-prompt="मेरे शहर में 24/7 आपातकालीन अस्पताल">
          <i class="bi bi-hospital"></i> आपातकालीन अस्पताल
        </button>
        <button type="button" class="prompt-chip" data-prompt="सीने में तेज दर्द और सांस लेने में कठिनाई">
          <i class="bi bi-exclamation-triangle-fill text-danger"></i> आपातकालीन छाती दर्द
        </button>
        <button type="button" class="prompt-chip" data-prompt="दो दिन से बुखार और सिरदर्द">
          <i class="bi bi-thermometer-half"></i> सामान्य चिकित्सक (बुखार)
        </button>
      `;
    } else {
      input.placeholder = "Type your symptoms or question (e.g. 'persistent dry cough', 'skin rash')...";
      promptsTray.innerHTML = `
        <span class="text-muted fw-semibold me-1" style="font-size: 0.78rem;">Suggested:</span>
        <button type="button" class="prompt-chip" data-prompt="Help me find a dermatologist for skin allergy">
          <i class="bi bi-hand-dots"></i> Find a Dermatologist
        </button>
        <button type="button" class="prompt-chip" data-prompt="I have toothache and gum pain, find a dentist">
          <i class="bi bi-bandaid"></i> Find a Nearby Dentist
        </button>
        <button type="button" class="prompt-chip" data-prompt="Find 24/7 emergency hospitals in my city">
          <i class="bi bi-hospital"></i> Find Emergency Hospitals
        </button>
        <button type="button" class="prompt-chip" data-prompt="I have sudden acute chest pain and shortness of breath">
          <i class="bi bi-exclamation-triangle-fill text-danger"></i> Emergency Chest Pain
        </button>
        <button type="button" class="prompt-chip" data-prompt="Fever and body aches for two days">
          <i class="bi bi-thermometer-half"></i> General Physician (Fever)
        </button>
      `;
    }

    attachPromptChipListeners();
  }

  function attachPromptChipListeners() {
    if (!promptsTray) return;
    promptsTray.querySelectorAll('.prompt-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const promptText = chip.getAttribute('data-prompt');
        if (input && promptText) {
          input.value = promptText;
          form.dispatchEvent(new Event('submit'));
        }
      });
    });
  }

  attachPromptChipListeners();

  // Clear Chat
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      chatFlow.innerHTML = `
        <div class="chat-bubble-wrap chat-bubble-ai">
          <div class="chat-avatar-icon ai"><i class="bi bi-stars"></i></div>
          <div class="chat-bubble-content">
            <p class="mb-2 fw-semibold text-dark">Conversation cleared.</p>
            <p class="mb-0 text-secondary">How can I assist your healthcare navigation today? Describe your symptoms or condition.</p>
          </div>
        </div>
      `;
      showToast('Chat history reset.', 'info', 2000);
    });
  }

  // Form submission
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const userText = (input.value || '').trim();
      if (!userText) return;

      // Append user bubble
      appendUserBubble(userText);
      input.value = '';

      // Show typing indicator
      if (typingIndicator) typingIndicator.classList.remove('d-none');
      scrollChatToBottom();

      try {
        // Send request to Flask backend
        const response = await fetch('/api/ai-chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.getCsrfToken ? window.getCsrfToken() : ''
          },
          body: JSON.stringify({ message: userText, language: currentLang })
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Brief delay for natural conversational feel
        setTimeout(() => {
          if (typingIndicator) typingIndicator.classList.add('d-none');
          appendAssistantBubble(data);
          scrollChatToBottom();
        }, 400);

      } catch (err) {
        console.warn('Backend /api/ai-chat unavailable, running offline triage engine:', err);
        setTimeout(() => {
          if (typingIndicator) typingIndicator.classList.add('d-none');
          const fallbackData = getOfflineTriageResponse(userText, currentLang);
          appendAssistantBubble(fallbackData);
          scrollChatToBottom();
        }, 400);
      }
    });
  }

  function appendUserBubble(text) {
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble-wrap chat-bubble-user';
    bubble.innerHTML = `
      <div class="chat-avatar-icon user"><i class="bi bi-person-fill"></i></div>
      <div class="chat-bubble-content">
        <p class="mb-0">${escapeHtml(text)}</p>
      </div>
    `;
    chatFlow.appendChild(bubble);
  }

  function appendAssistantBubble(data) {
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble-wrap chat-bubble-ai';

    let extraHtml = '';

    // Emergency red-flag alert
    if (data.is_emergency) {
      extraHtml += `
        <div class="red-flag-warning">
          <div class="d-flex align-items-center gap-2 mb-1 fw-bold">
            <i class="bi bi-exclamation-triangle-fill fs-5"></i>
            <span>URGENT MEDICAL ADVISORY</span>
          </div>
          <div style="font-size: 0.88rem;">${data.emergency_note || 'These symptoms may require immediate acute medical evaluation. Please do not wait for an online appointment.'}</div>
          <div class="mt-2 d-flex gap-2 flex-wrap">
            <a href="tel:108" class="btn btn-danger btn-sm"><i class="bi bi-telephone-fill"></i> Call Ambulance 108</a>
            <a href="/hospitals" class="btn btn-outline-danger btn-sm"><i class="bi bi-hospital"></i> Locate Emergency Hospitals</a>
          </div>
        </div>
      `;
    }

    // Recommended specialty card
    if (data.recommended_specialty) {
      extraHtml += `
        <div class="ai-recommendation-card">
          <div>
            <div class="text-uppercase text-muted fw-bold" style="font-size: 0.72rem;">Suggested Medical Specialty</div>
            <div class="fw-bold text-dark fs-6">${data.recommended_specialty}</div>
            <div class="text-muted" style="font-size: 0.78rem;">${data.specialty_reason || 'Matches your described health concern'}</div>
          </div>
          <a href="/doctors?specialty=${encodeURIComponent(data.recommended_specialty)}" class="btn btn-primary-teal btn-sm">
            <i class="bi bi-search"></i> View Doctors
          </a>
        </div>
      `;
    }

    // Backend unavailable note if fallback
    if (data.is_fallback) {
      extraHtml += `
        <div class="alert alert-light border py-1 px-2 mt-2 mb-0 text-muted" style="font-size: 0.75rem;">
          <i class="bi bi-cloud-slash"></i> Offline Rule-Based Triage Mode (Flask API endpoint was unreachable)
        </div>
      `;
    }

    bubble.innerHTML = `
      <div class="chat-avatar-icon ai"><i class="bi bi-stars"></i></div>
      <div class="chat-bubble-content">
        <p class="mb-2 text-dark">${data.reply_text}</p>
        ${extraHtml}
      </div>
    `;

    chatFlow.appendChild(bubble);
  }

  function scrollChatToBottom() {
    chatFlow.scrollTop = chatFlow.scrollHeight;
  }

  function escapeHtml(string) {
    const div = document.createElement('div');
    div.innerText = string;
    return div.innerHTML;
  }

  /**
   * Safe offline triage fallback matching clinical rules
   */
  function getOfflineTriageResponse(text, lang) {
    const lower = text.toLowerCase();

    // Check emergency red flags
    if (lower.includes('chest pain') || lower.includes('heart attack') || lower.includes('shortness of breath') || lower.includes('छाती') || lower.includes('सांस')) {
      return {
        reply_text: lang === 'hi'
          ? "चेतावनी: सीने में तेज दर्द या सांस लेने में गंभीर तकलीफ संभावित आपातकालीन चिकित्सा स्थिति का संकेत हो सकती है।"
          : "Urgent: Acute chest pain, heaviness, or sudden shortness of breath can indicate a critical cardiovascular or pulmonary emergency.",
        recommended_specialty: "Cardiologist",
        specialty_reason: "Cardiovascular emergency evaluation required",
        is_emergency: true,
        emergency_note: "Please contact emergency response (108 / 112) or reach your nearest 24/7 hospital immediately.",
        is_fallback: true
      };
    }

    // Skin / Dermatologist
    if (lower.includes('skin') || lower.includes('acne') || lower.includes('rash') || lower.includes('hair') || lower.includes('त्वचा') || lower.includes('खुजली')) {
      return {
        reply_text: lang === 'hi'
          ? "त्वचा से जुड़े लक्षण (जैसे रैश, मुँहासे, एलर्जी) के लिए डर्मेटोलॉजिस्ट (त्वचा विशेषज्ञ) से परामर्श करना उचित है।"
          : "Based on your symptoms involving skin, rash, itching or hair concerns, consulting a Dermatologist is recommended.",
        recommended_specialty: "Dermatologist",
        specialty_reason: "Dermatology & Skin Disorders",
        is_emergency: false,
        is_fallback: true
      };
    }

    // Dental / Dentist
    if (lower.includes('tooth') || lower.includes('teeth') || lower.includes('gum') || lower.includes('dental') || lower.includes('दांत')) {
      return {
        reply_text: lang === 'hi'
          ? "दांतों या मसूड़ों के दर्द के लिए डेंटिस्ट (दंत चिकित्सक) की जाँच आवश्यक है।"
          : "For tooth pain, dental sensitivity, cavity or gum discomfort, a visit to a licensed Dentist is recommended.",
        recommended_specialty: "Dentist",
        specialty_reason: "Oral health & Dental Care",
        is_emergency: false,
        is_fallback: true
      };
    }

    // Eye / Vision
    if (lower.includes('eye') || lower.includes('vision') || lower.includes('blur') || lower.includes('आँख') || lower.includes('दृष्टि')) {
      return {
        reply_text: lang === 'hi'
          ? "आँखों में खिंचाव, धुंधलापन या जलन के लिए नेत्र विशेषज्ञ (Eye Specialist / Ophthalmologist) से परामर्श करें।"
          : "For digital eye fatigue, blurred vision, or corneal irritation, consulting an Eye Specialist (Ophthalmologist) is recommended.",
        recommended_specialty: "Eye Specialist",
        specialty_reason: "Vision diagnostics & Ophthalmology",
        is_emergency: false,
        is_fallback: true
      };
    }

    // Child / Pediatrician
    if (lower.includes('child') || lower.includes('baby') || lower.includes('infant') || lower.includes('बच्च') || lower.includes('शिशु')) {
      return {
        reply_text: lang === 'hi'
          ? "शिशु और बच्चों के स्वास्थ्य, टीकाकरण और पोषण के लिए बाल रोग विशेषज्ञ (Pediatrician) सबसे उपयुक्त डॉक्टर हैं।"
          : "For pediatric concerns, newborn feeding, fever, or childhood vaccinations, consulting a Pediatrician is recommended.",
        recommended_specialty: "Pediatrician",
        specialty_reason: "Child healthcare & Pediatrics",
        is_emergency: false,
        is_fallback: true
      };
    }

    // Default: General Physician
    return {
      reply_text: lang === 'hi'
        ? "सामान्य लक्षणों (जैसे हल्का बुखार, कमजोरी, पेट दर्द) के लिए प्राथमिक परीक्षण हेतु जनरल फिजिशियन से शुरुआत करना सर्वोत्तम रहता है।"
        : "For general symptoms like fever, fatigue, or primary checkups, we recommend starting with a General Physician for comprehensive evaluation.",
      recommended_specialty: "General Physician",
      specialty_reason: "Primary Care & Internal Medicine",
      is_emergency: false,
      is_fallback: true
    };
  }
}
