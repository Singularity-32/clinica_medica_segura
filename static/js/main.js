/* ═══════════════════════════════════════════════════════════════
   Sistema de Agendamento Clínico Seguro — main.js
   ═══════════════════════════════════════════════════════════════ */

'use strict';

// ── Aviso de sessão prestes a expirar (RNF03) ─────────────────────
(function sessionTimeoutWarning() {
  const TIMEOUT_MS = 900_000;   // 15 min (igual ao Django SESSION_COOKIE_AGE)
  const WARN_BEFORE = 60_000;   // avisa 1 min antes

  if (!document.querySelector('.navbar')) return; // só quando logado

  let warnTimer, expireTimer;

  function resetTimers() {
    clearTimeout(warnTimer);
    clearTimeout(expireTimer);

    warnTimer = setTimeout(() => {
      showToast('⚠️ Sua sessão expirará em 1 minuto por inatividade.', 'warning', 55_000);
    }, TIMEOUT_MS - WARN_BEFORE);

    expireTimer = setTimeout(() => {
      window.location.href = '/auth/login/?timeout=1';
    }, TIMEOUT_MS);
  }

  ['mousemove', 'keydown', 'click', 'scroll', 'touchstart'].forEach(evt =>
    document.addEventListener(evt, resetTimers, { passive: true })
  );
  resetTimers();
})();


// ── Toast / notificação flutuante ─────────────────────────────────
function showToast(msg, type = 'info', duration = 5000) {
  const toast = document.createElement('div');
  toast.className = `alert alert-${type}`;
  toast.style.cssText = 'position:fixed;top:70px;right:1rem;z-index:9999;max-width:360px;animation:fadeIn .3s';
  toast.innerHTML = `<span class="alert-icon">${type === 'warning' ? '⚠️' : 'ℹ️'}</span> ${msg}
    <button class="alert-close" onclick="this.parentElement.remove()">×</button>`;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), duration);
}


// ── Confirmação antes de ações destrutivas ─────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', e => {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });

  // Mostrar/ocultar senha
  document.querySelectorAll('.toggle-password').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = document.querySelector(btn.dataset.target);
      if (!input) return;
      input.type = input.type === 'password' ? 'text' : 'password';
      btn.textContent = input.type === 'password' ? '👁' : '🙈';
    });
  });

  // Auto-formatar token OTP (adiciona espaço a cada 3 dígitos)
  const tokenInput = document.querySelector('.token-input');
  if (tokenInput) {
    tokenInput.addEventListener('input', () => {
      tokenInput.value = tokenInput.value.replace(/\D/g, '').slice(0, 6);
    });
  }

  // Força HTTPS no client (complementa req 3.2)
  if (location.protocol === 'http:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
    location.replace('https:' + location.href.substring(5));
  }
});
