/**
 * Admin Analytics Dashboard Controller
 * Chart.js Visualizations, Data Filtering, Pagination & Modal Inspector
 */

document.addEventListener('DOMContentLoaded', function () {
  const stats = window.SURVEY_STATS || {};
  if (!stats || stats.total_n === 0) return;

  // Chart Palette (Teal & Navy theme)
  const colors = {
    tealPrimary: '#0d9488',
    tealDark: '#0f766e',
    tealLight: '#99f6e4',
    tealBg: 'rgba(13, 148, 136, 0.75)',
    navyDark: '#0f172a',
    navyMedium: '#1e293b',
    roseAlert: '#ef4444',
    amberWarning: '#f59e0b',
    blueInfo: '#3b82f6',
    purpleAccent: '#8b5cf6',
    grayMuted: '#94a3b8'
  };

  const chartDefaultOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: { boxWidth: 12, padding: 14, font: { family: 'inherit', size: 12 } }
      },
      tooltip: {
        backgroundColor: '#0f172a',
        padding: 10,
        cornerRadius: 6
      }
    }
  };

  // 1. Reported Diabetes Diagnosis Chart (Doughnut)
  const diagCtx = document.getElementById('diabetesDiagnosisChart');
  if (diagCtx) {
    const diagData = stats.diabetes_distribution || {};
    const labels = Object.keys(diagData);
    const values = Object.values(diagData);

    new Chart(diagCtx, {
      type: 'doughnut',
      data: {
        labels: labels.length ? labels : ['No Data'],
        datasets: [{
          data: values.length ? values : [1],
          backgroundColor: [
            colors.roseAlert,
            '#e11d48',
            colors.amberWarning,
            colors.tealPrimary,
            colors.grayMuted
          ],
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        ...chartDefaultOptions,
        plugins: {
          ...chartDefaultOptions.plugins,
          tooltip: {
            callbacks: {
              label: function (ctx) {
                const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                const val = ctx.raw || 0;
                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                return ` ${ctx.label}: ${val} respondents (${pct}%)`;
              }
            }
          }
        }
      }
    });
  }

  // 2. Chronic Diseases Comorbidity Frequency (Horizontal Bar)
  const chronicCtx = document.getElementById('chronicDiseasesChart');
  if (chronicCtx) {
    const chronicData = stats.chronic_diseases_frequency || {};
    const labels = Object.keys(chronicData);
    const values = Object.values(chronicData);

    new Chart(chronicCtx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Reported Cases',
          data: values,
          backgroundColor: colors.tealPrimary,
          borderRadius: 6
        }]
      },
      options: {
        ...chartDefaultOptions,
        indexAxis: 'y',
        scales: {
          x: {
            beginAtZero: true,
            ticks: { precision: 0 }
          }
        }
      }
    });
  }

  // 3. Age Demographics (Bar)
  const ageCtx = document.getElementById('ageDistributionChart');
  if (ageCtx) {
    const ageData = stats.age_distribution || {};
    const ageOrder = ["Below 18 years", "18 – 30 years", "31 – 45 years", "46 – 60 years", "Above 60 years"];
    const labels = ageOrder.filter(a => ageData[a] !== undefined).concat(Object.keys(ageData).filter(k => !ageOrder.includes(k)));
    const values = labels.map(k => ageData[k] || 0);

    new Chart(ageCtx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Respondents',
          data: values,
          backgroundColor: colors.blueInfo,
          borderRadius: 6
        }]
      },
      options: {
        ...chartDefaultOptions,
        scales: {
          y: { beginAtZero: true, ticks: { precision: 0 } }
        }
      }
    });
  }

  // 4. Location Type Distribution (Doughnut)
  const locCtx = document.getElementById('locationTypeChart');
  if (locCtx) {
    const locData = stats.location_distribution || {};
    new Chart(locCtx, {
      type: 'doughnut',
      data: {
        labels: Object.keys(locData),
        datasets: [{
          data: Object.values(locData),
          backgroundColor: [colors.tealDark, colors.amberWarning, colors.purpleAccent],
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: chartDefaultOptions
    });
  }

  // 5. Exercise Frequency (Bar)
  const exCtx = document.getElementById('exerciseFrequencyChart');
  if (exCtx) {
    const exData = stats.exercise_distribution || {};
    const exOrder = ["Daily (≥ 30 minutes)", "4–6 times per week", "2–3 times per week", "Once a week", "Rarely", "Never"];
    const labels = exOrder.filter(e => exData[e] !== undefined);
    const values = labels.map(e => exData[e] || 0);

    new Chart(exCtx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Respondents',
          data: values,
          backgroundColor: colors.tealPrimary,
          borderRadius: 6
        }]
      },
      options: {
        ...chartDefaultOptions,
        scales: {
          y: { beginAtZero: true, ticks: { precision: 0 } }
        }
      }
    });
  }

  // 6. Age vs Reported Diabetes Cross-Tabulation (Bar)
  const crossAgeCtx = document.getElementById('crossAgeDiabetesChart');
  if (crossAgeCtx) {
    const crossData = stats.cross_age_diabetes || {};
    const ageOrder = ["Below 18 years", "18 – 30 years", "31 – 45 years", "46 – 60 years", "Above 60 years"];
    const labels = ageOrder.filter(a => crossData[a] !== undefined);
    const pctValues = labels.map(a => crossData[a].percentage);

    new Chart(crossAgeCtx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Reported Diabetes (%)',
          data: pctValues,
          backgroundColor: colors.roseAlert,
          borderRadius: 6
        }]
      },
      options: {
        ...chartDefaultOptions,
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: {
              callback: val => val + '%'
            }
          }
        },
        plugins: {
          ...chartDefaultOptions.plugins,
          tooltip: {
            callbacks: {
              label: function (ctx) {
                const item = crossData[ctx.label];
                return ` ${ctx.raw}% diagnosed (${item.diagnosed} out of ${item.total} in this age group)`;
              }
            }
          }
        }
      }
    });
  }

  // 7. Routine Blood Sugar Testing Frequency (Bar)
  const sugarCtx = document.getElementById('bloodSugarChart');
  if (sugarCtx) {
    const sugarData = stats.blood_sugar_test_frequency || {};
    new Chart(sugarCtx, {
      type: 'bar',
      data: {
        labels: Object.keys(sugarData),
        datasets: [{
          label: 'Respondents',
          data: Object.values(sugarData),
          backgroundColor: colors.purpleAccent,
          borderRadius: 6
        }]
      },
      options: {
        ...chartDefaultOptions,
        scales: {
          y: { beginAtZero: true, ticks: { precision: 0 } }
        }
      }
    });
  }

  // 8. Healthcare Accessibility / Distance (Bar)
  const accessCtx = document.getElementById('healthcareAccessChart');
  if (accessCtx) {
    const accessData = stats.healthcare_access_distribution || {};
    new Chart(accessCtx, {
      type: 'bar',
      data: {
        labels: Object.keys(accessData),
        datasets: [{
          label: 'Respondents',
          data: Object.values(accessData),
          backgroundColor: colors.tealDark,
          borderRadius: 6
        }]
      },
      options: {
        ...chartDefaultOptions,
        scales: {
          y: { beginAtZero: true, ticks: { precision: 0 } }
        }
      }
    });
  }

  // ==========================================
  // Anonymized Table Controller
  // ==========================================
  let currentPage = 1;
  const perPage = 10;
  const tableBody = document.getElementById('tableBody');
  const tableSearch = document.getElementById('tableSearch');
  const locationFilter = document.getElementById('locationFilter');
  const diabetesFilter = document.getElementById('diabetesFilter');
  const prevBtn = document.getElementById('prevPageBtn');
  const nextBtn = document.getElementById('nextPageBtn');
  const paginationInfo = document.getElementById('paginationInfo');
  const recordsCountText = document.getElementById('recordsCountText');

  function fetchResponses() {
    if (!tableBody) return;
    tableBody.innerHTML = '<tr><td colspan="10" style="text-align:center; padding: 24px; color: var(--text-muted);">Loading response data... ⏳</td></tr>';

    const search = tableSearch ? encodeURIComponent(tableSearch.value.trim()) : '';
    const loc = locationFilter ? encodeURIComponent(locationFilter.value) : '';
    const diab = diabetesFilter ? encodeURIComponent(diabetesFilter.value) : '';

    const url = `/api/responses?page=${currentPage}&per_page=${perPage}&search=${search}&location=${loc}&diabetes=${diab}`;

    fetch(url)
      .then(res => res.json())
      .then(data => {
        renderTable(data);
      })
      .catch(err => {
        console.error('Failed to load responses:', err);
        tableBody.innerHTML = '<tr><td colspan="10" style="text-align:center; padding: 24px; color: var(--danger-color);">Error loading records.</td></tr>';
      });
  }

  function renderTable(data) {
    tableBody.innerHTML = '';
    const records = data.records || [];

    if (records.length === 0) {
      tableBody.innerHTML = '<tr><td colspan="10" style="text-align:center; padding: 24px; color: var(--text-muted);">No matching responses found.</td></tr>';
      if (paginationInfo) paginationInfo.textContent = 'Page 1 of 1';
      if (recordsCountText) recordsCountText.textContent = 'Showing 0 records';
      if (prevBtn) prevBtn.disabled = true;
      if (nextBtn) nextBtn.disabled = true;
      return;
    }

    records.forEach(r => {
      const tr = document.createElement('tr');

      // Status badge
      let badgeClass = 'badge-diab-no';
      let badgeLabel = 'No';
      if (r.q9_diagnosed_diabetes && r.q9_diagnosed_diabetes.includes('Yes')) {
        badgeClass = 'badge-diab-yes';
        badgeLabel = 'Diagnosed';
      } else if (r.q9_diagnosed_diabetes === 'Not tested yet') {
        badgeClass = 'badge-diab-not-tested';
        badgeLabel = 'Not Tested';
      }

      // Synthetic badge
      const synthBadge = r.is_synthetic ?
        `<span class="kpi-tag tag-synthetic" style="font-size:0.7rem;">Synthetic</span>` :
        `<span class="kpi-tag" style="background:#ecfdf5; color:#166534; font-size:0.7rem;">Genuine</span>`;

      tr.innerHTML = `
        <td><strong style="font-family:monospace; color:var(--navy-dark);">${r.reference_id}</strong></td>
        <td>${r.location_type || '—'}</td>
        <td>${r.survey_location || '—'}</td>
        <td>${r.q2_age_group || '—'}</td>
        <td>${r.q3_gender || '—'}</td>
        <td>${r.q5_education || '—'}</td>
        <td><span class="status-badge ${badgeClass}">${badgeLabel}</span></td>
        <td>${r.q12_exercise_frequency || '—'}</td>
        <td>${synthBadge}</td>
        <td>
          <button type="button" class="btn btn-secondary view-detail-btn" data-ref="${r.reference_id}" style="padding: 4px 10px; font-size: 0.8rem;">
            Inspect
          </button>
        </td>
      `;
      tableBody.appendChild(tr);
    });

    if (paginationInfo) paginationInfo.textContent = `Page ${data.page} of ${data.total_pages}`;
    if (recordsCountText) recordsCountText.textContent = `Showing ${records.length} of ${data.total} records`;
    if (prevBtn) prevBtn.disabled = data.page <= 1;
    if (nextBtn) nextBtn.disabled = data.page >= data.total_pages;

    // Attach click handlers to Inspect buttons
    document.querySelectorAll('.view-detail-btn').forEach(btn => {
      btn.addEventListener('click', function () {
        openDetailModal(this.getAttribute('data-ref'));
      });
    });
  }

  // Filter change listeners
  if (tableSearch) {
    let debounceTimer;
    tableSearch.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        currentPage = 1;
        fetchResponses();
      }, 300);
    });
  }

  if (locationFilter) {
    locationFilter.addEventListener('change', () => {
      currentPage = 1;
      fetchResponses();
    });
  }

  if (diabetesFilter) {
    diabetesFilter.addEventListener('change', () => {
      currentPage = 1;
      fetchResponses();
    });
  }

  if (prevBtn) {
    prevBtn.addEventListener('click', () => {
      if (currentPage > 1) {
        currentPage--;
        fetchResponses();
      }
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      currentPage++;
      fetchResponses();
    });
  }

  // Initial table fetch
  fetchResponses();

  // ==========================================
  // Response Inspector Modal
  // ==========================================
  const detailModal = document.getElementById('detailModal');
  const detailBody = document.getElementById('detailModalBody');
  const detailRefId = document.getElementById('detailRefId');
  const detailTimestamp = document.getElementById('detailTimestamp');
  const closeDetailModal = document.getElementById('closeDetailModal');
  const closeDetailBtn = document.getElementById('closeDetailBtn');

  function openDetailModal(refId) {
    if (!detailModal || !detailBody) return;
    detailBody.innerHTML = '<div style="text-align:center; padding: 2rem;">Loading details... ⏳</div>';
    detailModal.classList.add('show');

    fetch(`/api/responses/${refId}`)
      .then(res => res.json())
      .then(r => {
        if (r.error) {
          detailBody.innerHTML = `<div style="color:var(--danger-color);">${r.error}</div>`;
          return;
        }

        if (detailRefId) detailRefId.textContent = `Response: ${r.reference_id}`;
        if (detailTimestamp) detailTimestamp.textContent = `Submitted: ${r.submitted_at} (${r.is_synthetic ? 'Synthetic Demo' : 'Genuine Field Entry'})`;

        const formatList = (arr) => Array.isArray(arr) && arr.length > 0 ? arr.join(', ') : 'None reported';

        detailBody.innerHTML = `
          <div style="margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--border-color);">
            <strong style="color: var(--teal-dark);">Metadata:</strong> ${r.location_type} | Area: ${r.survey_location || 'Not specified'} | Surveyor: ${r.surveyor_name || 'Volunteer'} | Respondent Identity: ${r.q1_full_name_masked}
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 1rem;">
            <div><strong>Q2. Age Group:</strong> ${r.q2_age_group}</div>
            <div><strong>Q3. Gender:</strong> ${r.q3_gender}</div>
            <div><strong>Q4. Occupation:</strong> ${r.q4_occupation || '—'}</div>
            <div><strong>Q5. Education:</strong> ${r.q5_education}</div>
            <div><strong>Q6. Heard Diabetes:</strong> ${r.q6_heard_diabetes}</div>
            <div><strong>Q8. First Source:</strong> ${r.q8_first_learned_source}</div>
            <div><strong>Q9. Diabetes Diagnosis:</strong> <span style="color:var(--teal-dark); font-weight:700;">${r.q9_diagnosed_diabetes}</span></div>
            <div><strong>Q12. Exercise:</strong> ${r.q12_exercise_frequency}</div>
            <div><strong>Q13. Daily Activity:</strong> ${r.q13_daily_activity_level || '—'}</div>
            <div><strong>Q14. Sugary Foods:</strong> ${r.q14_sugary_intake_frequency || '—'}</div>
            <div><strong>Q15. Smoking:</strong> ${r.q15_smoking_status || '—'}</div>
            <div><strong>Q16. Alcohol:</strong> ${r.q16_alcohol_consumption || '—'}</div>
            <div><strong>Q17. Sleep:</strong> ${r.q17_sleep_hours || '—'}</div>
            <div><strong>Q18. Diet Type:</strong> ${r.q18_diet_type || '—'}</div>
            <div><strong>Q21. Health Checkup:</strong> ${r.q21_routine_health_checkup || '—'}</div>
            <div><strong>Q22. Blood Sugar Test:</strong> ${r.q22_blood_sugar_test_frequency || '—'}</div>
            <div><strong>Q23. Distance to PHC:</strong> ${r.q23_healthcare_accessibility || '—'}</div>
            <div><strong>Q24. Medicines Access:</strong> ${r.q24_medicines_access || '—'}</div>
            <div><strong>Q25. Daily Routine Impact:</strong> ${r.q25_daily_life_impact || '—'}</div>
            <div><strong>Q26. Monthly Expenditure:</strong> ${r.q26_monthly_expenditure || '—'}</div>
          </div>
          <div style="margin-top: 10px; padding: 10px; background:#f8fafc; border-radius:6px;">
            <div><strong>Q7. Aware of other conditions:</strong> ${formatList(r.q7_aware_chronic_diseases)}</div>
            <div style="margin-top:4px;"><strong>Q10. Diagnosed chronic conditions:</strong> ${formatList(r.q10_diagnosed_chronic_diseases)}</div>
            <div style="margin-top:4px;"><strong>Q11. Family history:</strong> ${formatList(r.q11_family_history)}</div>
            <div style="margin-top:4px;"><strong>Q27. Challenges:</strong> ${formatList(r.q27_challenges)}</div>
            <div style="margin-top:8px;"><strong>Q30. Prevention ideas:</strong> ${r.q30_prevention_measures || 'None provided'}</div>
            <div style="margin-top:4px;"><strong>Q31. Healthcare suggestions:</strong> ${r.q31_healthcare_suggestions || 'None provided'}</div>
          </div>
        `;
      });
  }

  if (closeDetailModal) closeDetailModal.addEventListener('click', () => detailModal.classList.remove('show'));
  if (closeDetailBtn) closeDetailBtn.addEventListener('click', () => detailModal.classList.remove('show'));
});
