/* ── MediLensAI · charts.js ─────────────────────────────────────────────── */
/* All charts use the locally-hosted Chart.js (no CDN).                      */

// ── Risk colour mapping ─────────────────────────────────────────────────────
const RISK_COLORS = {
  Normal:         { bg: 'rgba(16,185,129,0.7)',  border: '#10b981' },
  Low:            { bg: 'rgba(0,212,255,0.7)',   border: '#00d4ff' },
  'Critical Low': { bg: 'rgba(239,68,68,0.8)',   border: '#ef4444' },
  Moderate:       { bg: 'rgba(245,158,11,0.7)',  border: '#f59e0b' },
  High:           { bg: 'rgba(239,68,68,0.7)',   border: '#ef4444' },
  Critical:       { bg: 'rgba(220,38,38,0.8)',   border: '#dc2626' },
  'Not Detected': { bg: 'rgba(75,85,99,0.4)',    border: '#4b5563' },
};

function riskColor(level, key) {
  return (RISK_COLORS[level] || RISK_COLORS['Not Detected'])[key];
}

// ── Shared Chart.js defaults ────────────────────────────────────────────────
Chart.defaults.color        = '#8b9cc8';
Chart.defaults.borderColor  = 'rgba(255,255,255,0.06)';
Chart.defaults.font.family  = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";

// ── 1. Bar chart — all detected parameters ──────────────────────────────────
function renderParametersChart(parameters) {
  const ctx = document.getElementById('parameters-chart');
  if (!ctx) return;

  const detected = parameters.filter(p => p.value !== null);
  if (detected.length === 0) return;

  const normalised = detected.map(p => {
    if (!p.normal_max || p.normal_max <= 0) return 50;
    const ratio = (p.value / p.normal_max) * 100;
    // Low values get scaled 25-50% bar height so they display prominently!
    if (p.value < p.normal_min) {
      return Math.max(25, (p.value / (p.normal_min || 1)) * 50);
    }
    return Math.min(150, Math.max(15, ratio));
  });

  new Chart(ctx, {
    data: {
      labels: detected.map(p => p.display_name),
      datasets: [
        {
          type: 'bar',
          label: '% of Normal Range',
          data: normalised,
          backgroundColor: detected.map(p => riskColor(p.risk_level, 'bg')),
          borderColor:     detected.map(p => riskColor(p.risk_level, 'border')),
          borderWidth: 2,
          borderRadius: 8,
          borderSkipped: false,
        },
        {
          type: 'line',
          label: 'Normal threshold',
          data: new Array(detected.length).fill(100),
          borderColor: 'rgba(16,185,129,0.5)',
          borderDash:  [6, 4],
          borderWidth: 2,
          pointRadius: 0,
          fill: false,
        }
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label(ctx) {
              if (ctx.datasetIndex === 1) return ''; // Skip threshold line tooltips
              const p = detected[ctx.dataIndex];
              return ` ${p.value} ${p.unit}  ·  ${p.risk_level}`;
            },
          },
        },
      },
      scales: {
        x: {
          ticks: { maxRotation: 30, font: { size: 11 } },
          grid:  { display: false },
        },
        y: {
          min: 0, max: 150,
          title: { display: true, text: '% of Normal Range', font: { size: 11 } },
          ticks: {
            callback: v => v + '%',
          },
        },
      },
    },
  });
}

// ── 2. Doughnut — risk level distribution ──────────────────────────────────
function renderRiskDistributionChart(parameters) {
  const ctx = document.getElementById('risk-distribution-chart');
  if (!ctx) return;

  const counts = {};
  parameters.filter(p => p.value !== null).forEach(p => {
    counts[p.risk_level] = (counts[p.risk_level] || 0) + 1;
  });

  const labels = Object.keys(counts);
  if (labels.length === 0) return;

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data:            labels.map(l => counts[l]),
        backgroundColor: labels.map(l => riskColor(l, 'bg')),
        borderColor:     labels.map(l => riskColor(l, 'border')),
        borderWidth: 2,
        hoverOffset: 8,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '68%',
      plugins: {
        legend: {
          position: 'bottom',
          labels:   { padding: 16, usePointStyle: true, pointStyleWidth: 10 },
        },
        tooltip: {
          callbacks: {
            label(ctx) {
              return `  ${ctx.label}: ${ctx.parsed} parameter(s)`;
            },
          },
        },
      },
    },
  });
}

// ── 3. Radar chart — multi-parameter risk profile ───────────────────────────
function riskLevelToScore(level) {
  const map = { 'Normal': 1, 'Low': 1, 'Critical Low': 4, 'Moderate': 2, 'High': 3, 'Critical': 4 };
  return map[level] ?? 0;
}

function renderRadarChart(parameters) {
  const ctx = document.getElementById('radar-chart');
  if (!ctx) return;

  const detected = parameters.filter(p => p.value !== null);
  if (detected.length < 3) return; // radar needs ≥ 3 points

  // Derive numeric score from risk_level since there is no risk_score DB column
  const scores = detected.map(p => riskLevelToScore(p.risk_level));

  new Chart(ctx, {
    type: 'radar',
    data: {
      labels: detected.map(p => p.display_name),
      datasets: [{
        label: 'Risk Score',
        data: scores,
        backgroundColor: 'rgba(124,58,237,0.2)',
        borderColor:     '#7c3aed',
        pointBackgroundColor: detected.map(p => riskColor(p.risk_level, 'border')),
        pointRadius: 5,
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          min: 0, max: 4,
          ticks: { stepSize: 1, backdropColor: 'transparent', font: { size: 10 } },
          grid:  { color: 'rgba(255,255,255,0.06)' },
          angleLines: { color: 'rgba(255,255,255,0.06)' },
          pointLabels: { color: 'rgba(255,255,255,0.7)', font: { size: 11 } },
        },
      },
      plugins: {
        legend: { display: false },
      },
    },
  });
}

// ── 4. Mini gauge (arc) per metric card ────────────────────────────────────
function renderMiniGauge(canvasId, value, normalMin, normalMax, riskLevel) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  let pct;
  if (value < normalMin) {
    pct = normalMin > 0 ? (value / normalMin) * 0.4 : 0.2;
  } else if (value <= normalMax) {
    const range = normalMax - normalMin;
    pct = 0.4 + (range > 0 ? ((value - normalMin) / range) * 0.4 : 0.2);
  } else {
    pct = 0.8 + 0.2 * Math.min(1, (value - normalMax) / (normalMax || 1));
  }

  const filled = Math.min(Math.max(pct * 100, 5), 100);
  const empty  = 100 - filled;

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      datasets: [{
        data: [filled, empty],
        backgroundColor: [riskColor(riskLevel, 'bg'), 'rgba(255,255,255,0.05)'],
        borderColor:     [riskColor(riskLevel, 'border'), 'transparent'],
        borderWidth: [2, 0],
      }],
    },
    options: {
      responsive: false,
      cutout: '72%',
      circumference: 180,
      rotation: -90,
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
    },
  });
}

// ── 5. Trend line chart (multi-report history) ─────────────────────────────
function renderTrendChart(canvasId, trends, parameterName) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  const filtered = trends.filter(t => t.parameter_name === parameterName);
  if (filtered.length < 2) return;

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: filtered.map(t => t.upload_date.split(' ')[0]),
      datasets: [{
        label: filtered[0]?.display_name || parameterName,
        data:  filtered.map(t => t.value),
        borderColor:     '#00d4ff',
        backgroundColor: 'rgba(0,212,255,0.08)',
        pointBackgroundColor: filtered.map(t => riskColor(t.risk_level, 'border')),
        pointRadius: 5,
        fill: true,
        tension: 0.4,
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false } },
        y: { grid: { color: 'rgba(255,255,255,0.04)' } },
      },
    },
  });
}

// ── Bootstrap: run when dashboard page loads ───────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const reportId = document.body.dataset.reportId;
  if (!reportId) return;

  fetch(`/api/report-data/${reportId}`)
    .then(r => r.json())
    .then(data => {
      const params = data.parameters || [];
      renderParametersChart(params);
      renderRiskDistributionChart(params);
      renderRadarChart(params);

      params.forEach(p => {
        if (p.value !== null) {
          renderMiniGauge(
            `gauge-${p.id}`,
            p.value, p.normal_min, p.normal_max, p.risk_level
          );
        }
      });
    })
    .catch(err => console.error('[Charts] Failed to load report data:', err));

  // Trends — render dynamically for all parameters with ≥2 data points
  fetch('/api/health-trends')
    .then(r => r.json())
    .then(trends => {
      if (!trends || trends.length < 2) return;

      // Find all unique parameter names that have ≥2 data points
      const paramCounts = {};
      trends.forEach(t => {
        paramCounts[t.parameter_name] = (paramCounts[t.parameter_name] || 0) + 1;
      });
      const eligibleParams = Object.keys(paramCounts).filter(k => paramCounts[k] >= 2);

      if (eligibleParams.length === 0) return;

      const section = document.getElementById('trends-section');
      if (section) section.style.display = 'block';

      const trendsGrid = document.getElementById('trends-grid');
      if (!trendsGrid) return;

      trendsGrid.innerHTML = ''; // clear existing placeholders

      eligibleParams.forEach(paramName => {
        const displayName = (trends.find(t => t.parameter_name === paramName) || {}).display_name || paramName;
        const canvasId = `trend-${paramName.replace(/_/g, '-')}`;

        const wrapper = document.createElement('div');
        wrapper.className = 'trend-item';
        wrapper.innerHTML = `
          <p class="trend-label">${displayName}</p>
          <div style="height:120px; position:relative;">
            <canvas id="${canvasId}"></canvas>
          </div>`;
        trendsGrid.appendChild(wrapper);

        renderTrendChart(canvasId, trends, paramName);
      });
    })
    .catch(() => {});
});
