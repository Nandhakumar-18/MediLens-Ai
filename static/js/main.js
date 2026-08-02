/* ── MediLensAI · main.js ───────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {
  initUploadZone();
  initFlashMessages();
  pollUnreadAlerts();
  highlightActiveNav();
});

// ─── Upload drag-and-drop zone ────────────────────────────────────────────
function initUploadZone() {
  const zone      = document.getElementById('upload-zone');
  const fileInput = document.getElementById('file-input');
  const fileInfo  = document.getElementById('file-info');
  const form      = document.getElementById('upload-form');

  if (!zone) return;

  // Click to browse
  zone.addEventListener('click', () => fileInput.click());

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) showFileSelected(fileInput.files[0]);
  });

  // Drag events
  zone.addEventListener('dragover', (e) => {
    e.preventDefault();
    zone.classList.add('drag-over');
  });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    const dt = e.dataTransfer;
    if (dt.files.length > 0) {
      fileInput.files = dt.files;
      showFileSelected(dt.files[0]);
    }
  });

  // Form submit → show loading overlay
  if (form) {
    form.addEventListener('submit', (e) => {
      if (!fileInput.files.length) {
        e.preventDefault();
        showToast('Please select a medical report file first.', 'error');
        return;
      }
      showLoading('Analysing your medical report… please wait.');
    });
  }

  const filePreview  = document.getElementById('file-preview');
  const fileNameEl   = document.getElementById('file-name');
  const fileSizeEl   = document.getElementById('file-size');
  const btnChange    = document.getElementById('btn-change-file');

  if (btnChange) {
    btnChange.addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.click();
    });
  }

  function showFileSelected(file) {
    if (filePreview) {
      filePreview.style.display = 'flex';
      filePreview.style.alignItems = 'center';
      filePreview.style.justifyContent = 'space-between';
      filePreview.style.marginTop = '16px';
      filePreview.style.padding = '12px 16px';
      filePreview.style.borderRadius = 'var(--radius-md)';
      filePreview.style.background = 'rgba(16, 185, 129, 0.1)';
      filePreview.style.border = '1px solid var(--green)';
    }

    if (fileNameEl) fileNameEl.textContent = `📄 Selected Report: ${file.name}`;
    if (fileSizeEl) fileSizeEl.textContent = `(${formatBytes(file.size)})`;

    zone.style.borderColor = 'var(--green)';
    zone.style.background  = 'rgba(16,185,129,0.06)';
    zone.style.boxShadow   = '0 0 15px rgba(16,185,129,0.2)';

    // Update dropzone title for crystal-clear confirmation
    const titleEl = zone.querySelector('.upload-title');
    const subEl   = zone.querySelector('.upload-sub');
    if (titleEl) {
      titleEl.innerHTML = `<span style="color:var(--green); font-weight:700;">✓ Ready for Analysis: ${file.name}</span>`;
    }
    if (subEl) {
      subEl.textContent = `File size: ${formatBytes(file.size)} • Click 'Analyse Report' below to process.`;
    }
  }
}

// ─── Loading overlay ──────────────────────────────────────────────────────
function showLoading(msg) {
  const overlay = document.getElementById('loading-overlay');
  const text    = document.getElementById('loading-text');
  if (overlay) {
    if (text) text.textContent = msg || 'Processing…';
    overlay.classList.add('active');
  }
}
function hideLoading() {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) overlay.classList.remove('active');
}

// ─── Flash / toast messages ───────────────────────────────────────────────
function initFlashMessages() {
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => el.remove(), 5000);
    el.addEventListener('click', () => el.remove());
  });
}
function showToast(message, type = 'success') {
  const container = document.querySelector('.flash-messages')
                  || (() => {
                       const c = document.createElement('div');
                       c.className = 'flash-messages';
                       document.body.appendChild(c);
                       return c;
                     })();
  const el = document.createElement('div');
  el.className = `flash flash-${type}`;
  el.innerHTML = `<span>${type === 'error' ? '✕' : '✓'}</span> ${message}`;
  container.appendChild(el);
  setTimeout(() => el.remove(), 5000);
  el.addEventListener('click', () => el.remove());
}

// ─── Poll unread alert count (badge in nav) ───────────────────────────────
function pollUnreadAlerts() {
  const badge = document.querySelector('.alert-badge');
  if (!badge) return;

  const refresh = () => {
    fetch('/api/unread-alerts')
      .then(r => r.json())
      .then(data => {
        if (data.count > 0) {
          badge.textContent = data.count;
          badge.style.display = 'inline-block';
        } else {
          badge.style.display = 'none';
        }
      })
      .catch(() => {}); // offline-safe: silently ignore
  };

  refresh();
  setInterval(refresh, 30000); // every 30 s
}

// ─── Alert dismiss ────────────────────────────────────────────────────────
function dismissAlert(alertId, el) {
  fetch(`/api/dismiss-alert/${alertId}`, { method: 'POST' })
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        const card = el.closest('.alert-card');
        if (card) {
          card.style.transition = 'opacity 0.3s, transform 0.3s';
          card.style.opacity    = '0';
          card.style.transform  = 'translateX(30px)';
          setTimeout(() => card.remove(), 350);
        }
      }
    });
}

// ─── Highlight active nav link ────────────────────────────────────────────
function highlightActiveNav() {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(link => {
    const href = link.getAttribute('href') || '';
    if (href && (path === href || (href !== '/' && path.startsWith(href)))) {
      link.classList.add('active');
    }
  });
}

// ─── Utility: format bytes ────────────────────────────────────────────────
function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1048576).toFixed(1) + ' MB';
}

// ─── PWA Service Worker & "Add to Home Screen" Install Manager ───────────
let deferredInstallPrompt = null;

function initPWA() {
  // Register Service Worker
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js')
      .then(() => console.log('✓ Service Worker Registered'))
      .catch(() => {});
  }

  const sidebarBtn     = document.getElementById('pwa-install-btn');
  const banner         = document.getElementById('pwa-install-banner');
  const bannerInstBtn  = document.getElementById('pwa-banner-install-btn');
  const bannerCloseBtn = document.getElementById('pwa-banner-close-btn');

  // Catch native browser install prompt
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredInstallPrompt = e;

    // Show sidebar button & pop-up banner if not previously dismissed
    if (sidebarBtn) sidebarBtn.style.display = 'inline-flex';
    
    if (!localStorage.getItem('pwa_banner_dismissed')) {
      setTimeout(() => {
        if (banner) banner.style.display = 'block';
      }, 1500);
    }
  });

  const triggerInstall = () => {
    if (deferredInstallPrompt) {
      deferredInstallPrompt.prompt();
      deferredInstallPrompt.userChoice.then((choiceResult) => {
        if (choiceResult.outcome === 'accepted') {
          if (banner) banner.style.display = 'none';
          if (sidebarBtn) sidebarBtn.style.display = 'none';
        }
        deferredInstallPrompt = null;
      });
    } else {
      showToast('To add MediLensAI to your Home Screen: open browser menu ⋮ and select "Add to Home screen" or "Install App".', 'success');
    }
  };

  if (sidebarBtn)    sidebarBtn.addEventListener('click', triggerInstall);
  if (bannerInstBtn) bannerInstBtn.addEventListener('click', triggerInstall);

  if (bannerCloseBtn) {
    bannerCloseBtn.addEventListener('click', () => {
      if (banner) banner.style.display = 'none';
      localStorage.setItem('pwa_banner_dismissed', 'true');
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initPWA();
});
