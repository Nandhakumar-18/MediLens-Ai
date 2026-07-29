/* ── MediLensAI · voice.js ──────────────────────────────────────────────── */
/* English Web Speech API (SpeechSynthesis) Voice Readout.                   */
/* Completely offline — no external TTS service required.                    */

const Voice = (() => {
  const synth = window.speechSynthesis;

  function isSpeakingNow() {
    return !!(synth && (synth.speaking || synth.pending));
  }

  function getEnglishVoice() {
    if (!synth) return null;
    const voices = synth.getVoices();
    const preferred = ['Google UK English Female', 'Microsoft Zira', 'Samantha', 'Karen', 'Moira', 'Google US English'];
    for (const name of preferred) {
      const v = voices.find(v => v.name === name);
      if (v) return v;
    }
    return voices.find(v => /en/i.test(v.lang)) || voices[0] || null;
  }

  function stop() {
    if (synth) {
      synth.cancel();
    }
    const btn = document.getElementById('voice-btn');
    if (btn) {
      btn.textContent = '🔊 Read Aloud';
      btn.classList.remove('speaking');
    }
  }

  function speak(text, onEnd) {
    if (!synth) return;
    stop();

    setTimeout(() => {
      const utter    = new SpeechSynthesisUtterance(text);
      const voiceObj = getEnglishVoice();
      if (voiceObj) utter.voice = voiceObj;
      
      utter.lang   = 'en-US';
      utter.rate   = 0.95;
      utter.pitch  = 1.0;
      utter.volume = 1.0;

      utter.onend = () => {
        const btn = document.getElementById('voice-btn');
        if (btn) {
          btn.textContent = '🔊 Read Aloud';
          btn.classList.remove('speaking');
        }
        if (typeof onEnd === 'function') onEnd();
      };

      utter.onerror = () => { stop(); };

      const btn = document.getElementById('voice-btn');
      if (btn) {
        btn.textContent = '⏹ Stop Reading';
        btn.classList.add('speaking');
      }

      synth.speak(utter);
    }, 50);
  }

  return { speak, stop, isSupported: !!synth };
})();

window.stopVoice = Voice.stop;

function buildEnglishSummary(reportData) {
  const r = reportData.report;
  const p = reportData.parameters || [];

  let text = `Health report summary for ${r.patient_name || 'Patient'}. `;
  text += `Age ${r.patient_age || 'N/A'}, ${r.patient_gender || ''}. `;
  text += `Overall risk level: ${r.overall_risk_level || 'Normal'}. `;

  const detected = p.filter(param => param.value !== null);
  const abnormal = detected.filter(param => !['Normal', 'Not Detected'].includes(param.risk_level));

  if (detected.length === 0) {
    text += 'No medical parameters were detected in this report.';
  } else if (abnormal.length === 0) {
    text += `All ${detected.length} detected parameters are within the normal range.`;
  } else {
    text += `${abnormal.length} parameter${abnormal.length > 1 ? 's' : ''} require attention: `;
    abnormal.forEach(param => {
      text += `${param.display_name} is ${param.value} ${param.unit}, which is ${param.risk_level}. `;
    });
  }

  text += 'Please review the health recommendations shown on screen.';
  return text;
}

document.addEventListener('DOMContentLoaded', () => {
  const btn      = document.getElementById('voice-btn');
  const reportId = document.body.dataset.reportId;

  if (!btn || !reportId) return;

  if (!Voice.isSupported) {
    btn.textContent = '🔇 Voice not supported';
    btn.disabled = true;
    return;
  }

  let cachedSummary = '';

  // Pre-fetch report summary
  fetch(`/api/report-data/${reportId}`)
    .then(r => r.json())
    .then(data => { cachedSummary = buildEnglishSummary(data); })
    .catch(() => { cachedSummary = 'Health report summary is ready for playback.'; });

  btn.addEventListener('click', () => {
    if (window.speechSynthesis && (window.speechSynthesis.speaking || window.speechSynthesis.pending)) {
      Voice.stop();
      return;
    }

    const textToSpeak = cachedSummary || 'Health report summary is loading.';
    Voice.speak(textToSpeak);
  });
});
