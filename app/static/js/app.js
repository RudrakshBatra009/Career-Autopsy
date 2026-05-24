// ============================================
// CAREER AUTOPSY — Frontend JS
// ============================================

const form = document.getElementById('analyze-form');
const statusEl = document.getElementById('status');
const resultsEl = document.getElementById('results');
const submitBtn = document.getElementById('submit-btn');
const loadingOverlay = document.getElementById('loading_overlay');
const loadingBar = document.getElementById('loading_bar');
const loadingPct = document.getElementById('loading_pct');
const loadingStage = document.getElementById('loading_stage');
const historyListEl = document.getElementById('history_list');
const refreshHistoryBtn = document.getElementById('refresh_history_btn');
const copyShareBtn = document.getElementById('copy_share_btn');
const newAnalysisBtn = document.getElementById('new_analysis_btn');

const el = {
  verdictEmoji: document.getElementById('verdict_emoji'),
  verdictText: document.getElementById('verdict_text'),
  summary: document.getElementById('summary_text'),
  
  // Readout elements
  readoutPeak: document.getElementById('readout_peak'),
  readoutReplacement: document.getElementById('readout_replacement'),
  readoutPivot: document.getElementById('readout_pivot'),
  
  // Rings
  stagnationRing: document.getElementById('stagnation_ring'),
  stagnationValue: document.getElementById('stagnation_value'),
  burnoutRing: document.getElementById('burnout_ring'),
  burnoutValue: document.getElementById('burnout_value'),
  
  // Metric values
  valStagnation: document.getElementById('val_stagnation'),
  valBurnout: document.getElementById('val_burnout'),
  valAutomation: document.getElementById('val_automation'),
  valCeiling: document.getElementById('val_ceiling'),
  valDecline: document.getElementById('val_decline'),
  
  // Lists
  strengths: document.getElementById('strengths_list'),
  redFlags: document.getElementById('red_flags_list'),
  recommendations: document.getElementById('recommendations_list'),
  comparable: document.getElementById('comparable_list'),
  survival: document.getElementById('survival_list'),
  
  report: document.getElementById('detailed_report'),
};

let loadingTimer = null;
let stageTimer = null;
let activeShareUrl = window.location.pathname || '/';

const CIRCUMFERENCE = 2 * Math.PI * 52; // ~326.73

function clearChildren(node) {
  while (node && node.firstChild) node.removeChild(node.firstChild);
}

function pushItem(node, text, className) {
  const li = document.createElement('li');
  li.textContent = text;
  if (className) li.className = className;
  node.appendChild(li);
}

function pct(value) {
  return `${Number(value || 0).toFixed(1)}%`;
}

function setRing(ringEl, percentage) {
  if (!ringEl) return;
  const offset = CIRCUMFERENCE - (percentage / 100) * CIRCUMFERENCE;
  ringEl.style.strokeDashoffset = offset;
}

function getValueClass(value, invertDanger) {
  // invertDanger: true = higher is worse (which is true for all our risks)
  if (invertDanger) {
    if (value >= 70) return 'val-danger';
    if (value >= 40) return 'val-warning';
    return 'val-good';
  } else {
    if (value >= 70) return 'val-good';
    if (value >= 40) return 'val-warning';
    return 'val-danger';
  }
}

function getBarClass(value, invertDanger) {
  if (invertDanger) {
    if (value >= 70) return 'bar-danger';
    if (value >= 40) return 'bar-warning';
    return '';
  }
  return '';
}

function getVerdictClass(verdict) {
  const v = verdict.toUpperCase().trim();
  if (v === 'THRIVING') return 'thriving';
  if (v === 'STABLE') return 'stable';
  if (v === 'HIGH PLATEAU') return 'plateau';
  return 'threat';
}

function startLoading(title) {
  const shortTitle = title.length > 40 ? title.substring(0, 40) + '...' : title;
  const stages = [
    `Analyzing career trajectory for "${shortTitle}"...`,
    'Measuring salary stagnation velocity...',
    'Estimating automation replacement index...',
    'Scanning promotion ceiling threshold...',
    'Evaluating role burnout exposure...',
    'Generating final autopsy report...',
  ];
  let progress = 3;
  let stageIndex = 0;

  loadingBar.style.width = '3%';
  loadingPct.textContent = '3%';
  loadingStage.textContent = stages[0];
  loadingOverlay.classList.remove('hidden');

  loadingTimer = setInterval(() => {
    progress = Math.min(92, progress + Math.random() * 5 + 1.5);
    loadingBar.style.width = `${progress.toFixed(0)}%`;
    loadingPct.textContent = `${progress.toFixed(0)}%`;
  }, 300);

  stageTimer = setInterval(() => {
    stageIndex = Math.min(stages.length - 1, stageIndex + 1);
    loadingStage.textContent = stages[stageIndex];
  }, 1500);
}

function stopLoading() {
  if (loadingTimer) { clearInterval(loadingTimer); loadingTimer = null; }
  if (stageTimer) { clearInterval(stageTimer); stageTimer = null; }
  loadingBar.style.width = '100%';
  loadingPct.textContent = '100%';
  loadingStage.textContent = 'Rendering autopsy dashboard...';
  setTimeout(() => loadingOverlay.classList.add('hidden'), 300);
}

function renderDashboard(data) {
  // Populate form fields with the loaded data
  if (data.job_title) document.getElementById('job_title').value = data.job_title;
  if (data.years_of_experience !== undefined) document.getElementById('years_of_experience').value = data.years_of_experience;
  if (data.country) document.getElementById('country').value = data.country;
  if (data.current_stack) document.getElementById('current_stack').value = data.current_stack;
  
  document.getElementById('current_salary').value = data.current_salary || '';
  document.getElementById('work_hours_per_week').value = data.work_hours_per_week !== null && data.work_hours_per_week !== undefined ? data.work_hours_per_week : '';
  document.getElementById('company_type').value = data.company_type || '';
  document.getElementById('career_goals').value = data.career_goals || '';

  const d = data.dashboard;
  const m = d.metrics;


  // Verdict
  if (el.verdictEmoji) el.verdictEmoji.textContent = d.verdict_emoji || '⚠️';
  const verdictClass = getVerdictClass(d.verdict);
  el.verdictText.textContent = d.verdict;
  el.verdictText.className = 'verdict-label ' + verdictClass;
  el.summary.textContent = d.summary || 'Autopsy complete.';

  // Readouts
  el.readoutPeak.textContent = d.career_peak_forecast || '--';
  el.readoutReplacement.textContent = d.replacement_pressure || '--';
  el.readoutPivot.textContent = d.pivot_recommendation || '--';

  if (data.share_url) activeShareUrl = data.share_url;

  // Rings
  const stagnationVal = Number(m.salary_stagnation_probability || 0);
  const burnoutVal = Number(m.burnout_risk || 0);
  el.stagnationValue.textContent = pct(stagnationVal);
  el.burnoutValue.textContent = pct(burnoutVal);
  setTimeout(() => {
    setRing(el.stagnationRing, stagnationVal);
    setRing(el.burnoutRing, burnoutVal);
  }, 100);

  // Metric bars
  const metricMap = [
    { el: el.valStagnation, key: 'salary_stagnation_probability', invert: true },
    { el: el.valBurnout, key: 'burnout_risk', invert: true },
    { el: el.valAutomation, key: 'automation_pressure', invert: true },
    { el: el.valCeiling, key: 'promotion_ceiling', invert: true },
    { el: el.valDecline, key: 'industry_decline_exposure', invert: true },
  ];

  metricMap.forEach(({ el: valEl, key, invert }) => {
    const value = Number(m[key] || 0);
    valEl.textContent = pct(value);
    valEl.className = 'metric-value ' + getValueClass(value, invert);

    const bar = document.querySelector(`[data-metric="${key}"]`);
    if (bar) {
      bar.className = 'metric-bar ' + getBarClass(value, invert);
      setTimeout(() => { bar.style.width = `${value}%`; }, 100);
    }
  });

  // Lists
  clearChildren(el.strengths);
  (d.strengths || []).forEach(s => pushItem(el.strengths, s, 'strength-item'));

  clearChildren(el.redFlags);
  (d.red_flags || []).forEach(s => pushItem(el.redFlags, s, 'flag-item'));

  clearChildren(el.recommendations);
  (d.recommendations || []).forEach(s => pushItem(el.recommendations, s, 'reco-item'));

  clearChildren(el.comparable);
  (d.comparable_paths || []).forEach(s => pushItem(el.comparable, s, 'comparable-item'));

  clearChildren(el.survival);
  (d.survival_tips || []).forEach(s => pushItem(el.survival, s, 'tip-item'));

  // Detailed Report
  el.report.textContent = d.detailed_report || 'Detailed report unavailable.';

  resultsEl.classList.remove('hidden');
  resultsEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function refreshHistory() {
  if (!historyListEl) return;
  try {
    const res = await fetch('/api/history');
    if (!res.ok) throw new Error('History unavailable');
    const rows = await res.json();

    clearChildren(historyListEl);
    if (!rows.length) {
      pushItem(historyListEl, 'No autopsies performed yet. Test your career resilience!');
      return;
    }

    rows.forEach(item => {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = item.url;
      const dt = new Date(item.created_at);
      const dateLabel = isNaN(dt.getTime()) ? item.created_at : dt.toLocaleString();
      
      const labelText = `${item.job_title} (${item.years_of_experience} YOE, ${item.country})`;
      a.textContent = labelText;
      li.appendChild(a);

      const badge = document.createElement('span');
      badge.className = 'history-verdict ' + getVerdictClass(item.verdict);
      badge.textContent = item.verdict;
      li.appendChild(badge);

      const date = document.createElement('span');
      date.style.cssText = 'font-size:0.75rem; color:var(--muted); margin-left:8px;';
      date.textContent = dateLabel;
      li.appendChild(date);

      historyListEl.appendChild(li);
    });
  } catch (err) {
    clearChildren(historyListEl);
    pushItem(historyListEl, 'History could not be loaded.');
  }
}

async function loadFromSlugIfPresent() {
  const slug = window.location.pathname.replace(/^\/+|\/+$/g, '');
  if (!slug || slug === 'api' || slug === 'docs' || slug === 'redoc' || slug === 'health') return;

  try {
    startLoading(slug);
    const res = await fetch(`/api/history/${encodeURIComponent(slug)}`);
    if (!res.ok) throw new Error('No saved autopsy found.');
    const data = await res.json();
    activeShareUrl = `/${slug}`;
    renderDashboard(data);
    statusEl.textContent = `Loaded saved career autopsy: ${data.job_title} (${data.country})`;
  } catch (err) {
    statusEl.textContent = '';
  } finally {
    stopLoading();
  }
}

// Form submit
form.addEventListener('submit', async (event) => {
  event.preventDefault();

  const job_title = document.getElementById('job_title').value.trim();
  const years_of_experience = parseInt(document.getElementById('years_of_experience').value) || 0;
  const country = document.getElementById('country').value.trim();
  const current_stack = document.getElementById('current_stack').value.trim();

  if (!job_title || job_title.length < 2) {
    statusEl.textContent = 'Please enter a valid job title.';
    return;
  }
  if (years_of_experience < 0) {
    statusEl.textContent = 'Please enter a valid years of experience.';
    return;
  }
  if (!country || country.length < 2) {
    statusEl.textContent = 'Please enter your country.';
    return;
  }
  if (!current_stack || current_stack.length < 2) {
    statusEl.textContent = 'Please enter your stack/skills.';
    return;
  }

  const formData = new FormData();
  formData.append('job_title', job_title);
  formData.append('years_of_experience', years_of_experience);
  formData.append('country', country);
  formData.append('current_stack', current_stack);

  const currentSalary = document.getElementById('current_salary').value.trim();
  if (currentSalary) formData.append('current_salary', currentSalary);

  const workHoursVal = document.getElementById('work_hours_per_week').value;
  if (workHoursVal) formData.append('work_hours_per_week', parseInt(workHoursVal));

  const companyTypeVal = document.getElementById('company_type').value;
  if (companyTypeVal) formData.append('company_type', companyTypeVal);

  const careerGoals = document.getElementById('career_goals').value.trim();
  if (careerGoals) formData.append('career_goals', careerGoals);

  const resumeFileEl = document.getElementById('resume_file');
  if (resumeFileEl && resumeFileEl.files.length > 0) {
    formData.append('resume_file', resumeFileEl.files[0]);
  }

  submitBtn.disabled = true;
  statusEl.textContent = 'Running diagnostic autopsy...';
  startLoading(job_title);

  try {
    const response = await fetch('/analyze', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const msg = await response.text();
      throw new Error(msg || 'Request failed');
    }

    const data = await response.json();
    renderDashboard(data);

    statusEl.textContent = data.history_saved
      ? `Autopsy complete. Saved to history.`
      : `Autopsy complete. ${data.history_error ? 'History save failed: ' + data.history_error : ''}`;

    const targetSlug = `${job_title} ${country} ${years_of_experience}`
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .trim()
      .replace(/[\s_-]+/g, '-')
      .substring(0, 80) || 'career';
    
    history.replaceState({}, '', `/${targetSlug}`);
    activeShareUrl = `/${targetSlug}`;
    await refreshHistory();
  } catch (err) {
    statusEl.textContent = `Autopsy diagnostic failed: ${err.message}`;
  } finally {
    stopLoading();
    submitBtn.disabled = false;
  }
});


// Buttons
if (refreshHistoryBtn) {
  refreshHistoryBtn.addEventListener('click', () => refreshHistory());
}

if (copyShareBtn) {
  copyShareBtn.addEventListener('click', async () => {
    const link = new URL(activeShareUrl || '/', window.location.origin).toString();
    try {
      await navigator.clipboard.writeText(link);
      statusEl.textContent = 'Share link copied to clipboard!';
    } catch {
      statusEl.textContent = `Share: ${link}`;
    }
  });
}

if (newAnalysisBtn) {
  newAnalysisBtn.addEventListener('click', () => {
    resultsEl.classList.add('hidden');
    document.querySelector('.search-shell').scrollIntoView({ behavior: 'smooth' });
    form.reset();
    statusEl.textContent = '';
    history.replaceState({}, '', '/');
  });
}

// Init
refreshHistory();
loadFromSlugIfPresent();
