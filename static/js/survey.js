/**
 * Survey Multi-Step Wizard & Interactive Validation Controller
 */

document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('surveyForm');
  if (!form) return;

  let currentStep = 1;
  const totalSteps = 10;

  const sectionNames = {
    1: 'Section 1: Basic Information',
    2: 'Section 2: Awareness of Diabetes',
    3: 'Section 3: Health Status',
    4: 'Section 4: Lifestyle & Habits',
    5: 'Section 5: Diet & Nutrition',
    6: 'Section 6: Medical Checkups',
    7: 'Section 7: Impact on Daily Life',
    8: 'Section 8: Community Awareness',
    9: 'Section 9: Suggestions',
    10: 'Section 10: Declaration & Consent'
  };

  // Section Mandatory Fields
  const sectionValidationRules = {
    1: ['q2_age_group', 'q3_gender', 'q5_education'],
    2: ['q6_heard_diabetes', 'q8_first_learned_source'],
    3: ['q9_diagnosed_diabetes'],
    4: ['q12_exercise_frequency'],
    5: [],
    6: [],
    7: [],
    8: [],
    9: [],
    10: ['consent_given']
  };

  // Step Indicators & Navigation
  const stepIndicators = document.querySelectorAll('.step-indicator');
  const sectionCards = document.querySelectorAll('.survey-section-card');
  const progressFill = document.getElementById('progressFill');
  const progressPercentage = document.getElementById('progressPercentage');
  const progressSectionName = document.getElementById('progressSectionName');

  function updateWizardUI(step) {
    currentStep = step;

    // Show active section card
    sectionCards.forEach(card => {
      if (parseInt(card.getAttribute('data-section'), 10) === step) {
        card.classList.add('active');
      } else {
        card.classList.remove('active');
      }
    });

    // Update Step Indicators
    stepIndicators.forEach(ind => {
      const indStep = parseInt(ind.getAttribute('data-step'), 10);
      ind.classList.remove('active');
      if (indStep === step) {
        ind.classList.add('active');
      } else if (indStep < step) {
        ind.classList.add('completed');
      }
    });

    // Update Progress Bar
    const pct = Math.round((step / totalSteps) * 100);
    if (progressFill) progressFill.style.width = pct + '%';
    if (progressPercentage) progressPercentage.textContent = pct + '% Completed';
    if (progressSectionName) progressSectionName.textContent = sectionNames[step] || `Step ${step}`;

    // Scroll to top of survey smoothly
    const container = document.getElementById('surveyProgressContainer');
    if (container) {
      const topOffset = container.getBoundingClientRect().top + window.pageYOffset - 80;
      window.scrollTo({ top: topOffset, behavior: 'smooth' });
    }
  }

  // Validate current section
  function validateSection(step) {
    const requiredFields = sectionValidationRules[step] || [];
    let isValid = true;
    let firstErrorElement = null;

    // Clear previous errors
    const currentCard = document.querySelector(`.survey-section-card[data-section="${step}"]`);
    if (currentCard) {
      currentCard.querySelectorAll('.question-block').forEach(b => {
        b.classList.remove('has-error');
        const errText = b.querySelector('.error-text-msg');
        if (errText) errText.remove();
      });
    }

    for (const fieldName of requiredFields) {
      let isAnswered = false;

      if (fieldName === 'consent_given') {
        const consentBox = document.getElementById('consent_given');
        isAnswered = consentBox && consentBox.checked;
      } else {
        const inputs = form.querySelectorAll(`input[name="${fieldName}"]`);
        for (const input of inputs) {
          if (input.checked && input.value.trim() !== '') {
            isAnswered = true;
            break;
          }
        }
      }

      if (!isAnswered) {
        isValid = false;
        const block = document.getElementById(`block_${fieldName}`) ||
                      (document.querySelector(`input[name="${fieldName}"]`) ? document.querySelector(`input[name="${fieldName}"]`).closest('.question-block') : null);
        if (block) {
          block.classList.add('has-error');
          if (!block.querySelector('.error-text-msg')) {
            const errSpan = document.createElement('div');
            errSpan.className = 'error-text-msg';
            errSpan.textContent = 'Please answer this mandatory question to proceed.';
            block.appendChild(errSpan);
          }
          if (!firstErrorElement) firstErrorElement = block;
        }
      }
    }

    if (!isValid && firstErrorElement) {
      firstErrorElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      showToast('Please complete all mandatory questions marked with *', 'error');
    }

    return isValid;
  }

  // Next Step Buttons
  document.querySelectorAll('.next-step-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const nextStep = parseInt(this.getAttribute('data-next'), 10);
      if (validateSection(currentStep)) {
        updateWizardUI(nextStep);
      }
    });
  });

  // Previous Step Buttons
  document.querySelectorAll('.prev-step-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const prevStep = parseInt(this.getAttribute('data-prev'), 10);
      updateWizardUI(prevStep);
    });
  });

  // Direct step indicator click
  stepIndicators.forEach(ind => {
    ind.addEventListener('click', function () {
      const targetStep = parseInt(this.getAttribute('data-step'), 10);
      if (targetStep < currentStep) {
        // Can always go backwards
        updateWizardUI(targetStep);
      } else if (targetStep > currentStep) {
        // Validate before jumping forward
        if (validateSection(currentStep)) {
          updateWizardUI(targetStep);
        }
      }
    });
  });

  // Radio and Checkbox visual highlight toggling
  form.addEventListener('change', function (e) {
    const target = e.target;
    if (target.type === 'radio') {
      const name = target.name;
      document.querySelectorAll(`input[name="${name}"]`).forEach(r => {
        const parentOpt = r.closest('.custom-option');
        if (parentOpt) {
          if (r.checked) {
            parentOpt.classList.add('selected');
          } else {
            parentOpt.classList.remove('selected');
          }
        }
      });
      // Remove error highlight on change
      const block = target.closest('.question-block');
      if (block) {
        block.classList.remove('has-error');
        const errText = block.querySelector('.error-text-msg');
        if (errText) errText.remove();
      }
    } else if (target.type === 'checkbox') {
      const parentOpt = target.closest('.custom-option');
      if (parentOpt) {
        if (target.checked) {
          parentOpt.classList.add('selected');
        } else {
          parentOpt.classList.remove('selected');
        }
      }

      // Handle mutually exclusive options (e.g. "None of the above", "No chronic disease diagnosed", "No family history")
      if (target.checked) {
        const val = target.value;
        const groupName = target.name;
        if (val.includes('None') || val.includes('No chronic disease') || val.includes('No family history') || val.includes('Not aware')) {
          // Uncheck others in this group
          document.querySelectorAll(`input[name="${groupName}"]`).forEach(cb => {
            if (cb !== target) {
              cb.checked = false;
              const p = cb.closest('.custom-option');
              if (p) p.classList.remove('selected');
            }
          });
        } else {
          // Uncheck the "None / No" options
          document.querySelectorAll(`input[name="${groupName}"]`).forEach(cb => {
            if (cb.value.includes('None') || cb.value.includes('No chronic disease') || cb.value.includes('No family history')) {
              cb.checked = false;
              const p = cb.closest('.custom-option');
              if (p) p.classList.remove('selected');
            }
          });
        }
      }
    }
  });

  // Review Modal Logic
  const reviewModal = document.getElementById('reviewModal');
  const reviewBody = document.getElementById('reviewModalBody');
  const reviewBtn = document.getElementById('reviewAnswersBtn');
  const closeReviewBtn = document.getElementById('closeReviewModal');
  const editSurveyBtn = document.getElementById('editSurveyBtn');
  const confirmAndSubmitBtn = document.getElementById('confirmAndSubmitBtn');

  if (reviewBtn) {
    reviewBtn.addEventListener('click', function () {
      buildReviewSummary();
      if (reviewModal) reviewModal.classList.add('show');
    });
  }

  if (closeReviewBtn) {
    closeReviewBtn.addEventListener('click', () => reviewModal.classList.remove('show'));
  }

  if (editSurveyBtn) {
    editSurveyBtn.addEventListener('click', () => reviewModal.classList.remove('show'));
  }

  if (confirmAndSubmitBtn) {
    confirmAndSubmitBtn.addEventListener('click', function () {
      reviewModal.classList.remove('show');
      form.requestSubmit();
    });
  }

  function buildReviewSummary() {
    if (!reviewBody) return;
    reviewBody.innerHTML = '';

    const questionsList = [
      { id: 'location_type', title: 'Location Type', type: 'radio' },
      { id: 'survey_location', title: 'Survey Location / Ward', type: 'text' },
      { id: 'q1_full_name', title: 'Q1. Name of Respondent', type: 'text' },
      { id: 'q2_age_group', title: 'Q2. Age', type: 'radio' },
      { id: 'q3_gender', title: 'Q3. Gender', type: 'radio' },
      { id: 'q4_occupation', title: 'Q4. Occupation', type: 'radio' },
      { id: 'q5_education', title: 'Q5. Highest Education Level', type: 'radio' },
      { id: 'q6_heard_diabetes', title: 'Q6. Heard about Diabetes', type: 'radio' },
      { id: 'q7_aware_chronic_diseases', title: 'Q7. Aware of other chronic diseases', type: 'checkbox' },
      { id: 'q8_first_learned_source', title: 'Q8. How first learned', type: 'radio' },
      { id: 'q9_diagnosed_diabetes', title: 'Q9. Diagnosed with Diabetes', type: 'radio' },
      { id: 'q10_diagnosed_chronic_diseases', title: 'Q10. Diagnosed chronic diseases', type: 'checkbox' },
      { id: 'q11_family_history', title: 'Q11. Family history', type: 'checkbox' },
      { id: 'q12_exercise_frequency', title: 'Q12. Exercise frequency', type: 'radio' },
      { id: 'q13_daily_activity_level', title: 'Q13. Daily activity level', type: 'radio' },
      { id: 'q14_sugary_intake_frequency', title: 'Q14. Sugary foods frequency', type: 'radio' },
      { id: 'q15_smoking_status', title: 'Q15. Smoking status', type: 'radio' },
      { id: 'q16_alcohol_consumption', title: 'Q16. Alcohol consumption', type: 'radio' },
      { id: 'q17_sleep_hours', title: 'Q17. Average sleep hours', type: 'radio' },
      { id: 'q18_diet_type', title: 'Q18. Diet type', type: 'radio' },
      { id: 'q19_fruits_veg_frequency', title: 'Q19. Fruits/vegetables frequency', type: 'radio' },
      { id: 'q20_fast_food_frequency', title: 'Q20. Fast food frequency', type: 'radio' },
      { id: 'q21_routine_health_checkup', title: 'Q21. Routine health check-up', type: 'radio' },
      { id: 'q22_blood_sugar_test_frequency', title: 'Q22. Blood sugar test frequency', type: 'radio' },
      { id: 'q23_healthcare_accessibility', title: 'Q23. Healthcare facility distance', type: 'radio' },
      { id: 'q24_medicines_access', title: 'Q24. Easy access to medicines', type: 'radio' },
      { id: 'q25_daily_life_impact', title: 'Q25. Daily life impact', type: 'radio' },
      { id: 'q26_monthly_expenditure', title: 'Q26. Monthly treatment expenditure', type: 'radio' },
      { id: 'q27_challenges', title: 'Q27. Challenges faced', type: 'checkbox' },
      { id: 'q28_community_awareness_programs', title: 'Q28. Awareness programs in area', type: 'radio' },
      { id: 'q29_community_knowledge_level', title: 'Q29. Community knowledge level', type: 'radio' },
      { id: 'q30_prevention_measures', title: 'Q30. Prevention measures suggested', type: 'text' },
      { id: 'q31_healthcare_suggestions', title: 'Q31. Healthcare service suggestions', type: 'text' },
      { id: 'q32_future_participation', title: 'Q32. Willing to participate in future', type: 'radio' }
    ];

    questionsList.forEach(item => {
      let val = '<em>Not answered</em>';
      if (item.type === 'radio') {
        const checked = form.querySelector(`input[name="${item.id}"]:checked`);
        if (checked) val = checked.value;
      } else if (item.type === 'checkbox') {
        const checkedList = Array.from(form.querySelectorAll(`input[name="${item.id}"]:checked`)).map(c => c.value);
        if (checkedList.length > 0) val = checkedList.join(', ');
      } else if (item.type === 'text') {
        const inp = form.querySelector(`[name="${item.id}"]`);
        if (inp && inp.value.trim() !== '') val = escapeHtml(inp.value.trim());
      }

      const row = document.createElement('div');
      row.className = 'review-item';
      row.innerHTML = `
        <div class="review-q-title">${item.title}</div>
        <div class="review-q-answer">${val}</div>
      `;
      reviewBody.appendChild(row);
    });
  }

  // Final Form Submit validation
  form.addEventListener('submit', function (e) {
    // Validate Section 10 consent
    if (!validateSection(10)) {
      e.preventDefault();
      updateWizardUI(10);
      return;
    }

    // Verify all prior mandatory sections
    for (let s = 1; s <= 9; s++) {
      if (!validateSection(s)) {
        e.preventDefault();
        updateWizardUI(s);
        return;
      }
    }

    // Disable submit button to prevent double-submit
    const submitBtn = document.getElementById('finalSubmitBtn');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = 'Submitting Responses... ⏳';
    }
  });

  function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <span>${message}</span>
      <button onclick="this.parentElement.remove()" style="background:none;border:none;cursor:pointer;font-weight:bold;margin-left:12px;">✕</button>
    `;
    container.appendChild(toast);
    setTimeout(() => {
      if (toast.parentElement) toast.remove();
    }, 4000);
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.innerText = text;
    return div.innerHTML;
  }
});
