(() => {
  const form = document.getElementById("riskForm");
  const headerRunBtn = document.getElementById("headerRunBtn");
  const errorNote = document.getElementById("errorNote");
  const verdict = document.getElementById("verdict");
  const emptyState = document.getElementById("emptyState");

  const incomeInput = document.getElementById("person_income");
  const amountInput = document.getElementById("loan_amnt");
  const percentInput = document.getElementById("loan_percent_income");

  const gaugeFill = document.getElementById("gaugeFill");
  const gaugeThreshold = document.getElementById("gaugeThreshold");
  const probNumber = document.getElementById("probNumber");

  const factThreshold = document.getElementById("factThreshold");
  const factResult = document.getElementById("factResult");

  const apiDot = document.getElementById("apiDot");
  const apiStatusText = document.getElementById("apiStatusText");

  const GAUGE_LENGTH = 251.327;

  // ---------- Auto-calculate loan-to-income ratio ----------
  function recalcPercent() {
    const income = parseFloat(incomeInput.value);
    const amount = parseFloat(amountInput.value);
    if (income > 0 && amount >= 0) {
      percentInput.value = (amount / income).toFixed(2);
    }
  }
  incomeInput.addEventListener("input", recalcPercent);
  amountInput.addEventListener("input", recalcPercent);
  recalcPercent();

  // ---------- Service status check ----------
  fetch("/health", { method: "GET" })
    .then((res) => {
      if (res.ok) {
        apiDot.classList.add("ok");
        apiStatusText.textContent = "Service Online";
      } else {
        throw new Error("bad status");
      }
    })
    .catch(() => {
      apiDot.classList.add("down");
      apiStatusText.textContent = "Service Offline";
    });

  // ---------- Helpers ----------
  function setLoading(isLoading) {
    headerRunBtn.disabled = isLoading;
    headerRunBtn.classList.toggle("loading", isLoading);
    if (isLoading) {
      headerRunBtn.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin-icon" style="animation: spin 1s linear infinite; width:16px; height:16px; margin-right:8px;">
          <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
          <path d="M12 2a10 10 0 0 1 10 10"></path>
        </svg>
        Predicting...
      `;
    } else {
      headerRunBtn.innerHTML = `
        <svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
        Run Predictor
      `;
    }
  }

  function showError(message) {
    errorNote.textContent = message;
    errorNote.hidden = false;
  }

  function clearError() {
    errorNote.hidden = true;
    errorNote.textContent = "";
  }

  function animateNumber(el, from, to, duration) {
    const start = performance.now();
    function tick(now) {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      const value = from + (to - from) * eased;
      el.textContent = value.toFixed(1);
      if (t < 1) requestAnimationFrame(tick);
      else el.textContent = to.toFixed(1);
    }
    requestAnimationFrame(tick);
  }

  function renderVerdict(data) {
    const probabilityPct = data.default_probability * 100;
    const thresholdPct = data.threshold * 100;
    const isHighRisk = data.default_prediction === 1;

    emptyState.hidden = true;
    verdict.hidden = false;
    
    // Gauge fill
    const offset = GAUGE_LENGTH * (1 - probabilityPct / 100);
    const strokeColor = isHighRisk ? "var(--risk-high)" : "var(--kaggle-blue)";
    gaugeFill.style.stroke = strokeColor;
    
    requestAnimationFrame(() => {
      gaugeFill.style.strokeDashoffset = offset;
    });

    const thresholdDeg = (thresholdPct / 100) * 180 - 90;
    gaugeThreshold.style.transform = `rotate(${thresholdDeg}deg)`;

    // Number readout
    animateNumber(probNumber, 0, probabilityPct, 1000);

    factThreshold.textContent = `${thresholdPct.toFixed(1)}%`;
    factResult.textContent = data.Result;
    
    factResult.className = "metric-value " + (isHighRisk ? "risk-high" : "risk-low");
  }

  // ---------- Submit ----------
  function handleSubmit(e) {
    if(e) e.preventDefault();
    clearError();
    setLoading(true);

    const payload = {
      person_age: parseInt(document.getElementById("person_age").value, 10),
      person_income: parseFloat(incomeInput.value),
      person_home_ownership: document.getElementById("person_home_ownership").value,
      person_emp_length: parseFloat(document.getElementById("person_emp_length").value),
      loan_intent: document.getElementById("loan_intent").value,
      loan_grade: document.getElementById("loan_grade").value,
      loan_amnt: parseFloat(amountInput.value),
      loan_int_rate: parseFloat(document.getElementById("loan_int_rate").value),
      loan_percent_income: parseFloat(percentInput.value),
      cb_person_default_on_file: document.getElementById("cb_person_default_on_file").value,
      cb_person_cred_hist_length: parseInt(document.getElementById("cb_person_cred_hist_length").value, 10),
    };

    fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(async (res) => {
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error((body && body.detail) ? JSON.stringify(body.detail) : `HTTP ${res.status}`);
      }
      return res.json();
    }).then(data => {
      renderVerdict(data);
    }).catch(err => {
      showError(`Request failed: ${err.message}`);
    }).finally(() => {
      setLoading(false);
    });
  }

  form.addEventListener("submit", handleSubmit);
  headerRunBtn.addEventListener("click", () => {
    if(form.reportValidity()) handleSubmit();
  });

})();
