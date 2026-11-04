// When should the pet clock out? Pure functions, testable in Node.
(function (root) {
  const DEFAULTS = { leaveAt: '17:30', backAt: '09:00', workdays: [1, 2, 3, 4, 5] }; // Mon–Fri

  const minutes = (hhmm) => { const [h, m] = hhmm.split(':').map(Number); return h * 60 + m; };
  const dayKey = (d) => `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
  const nowMin = (d) => d.getHours() * 60 + d.getMinutes();

  /** Time to leave? (workday, past leaveAt, hasn't already left today) */
  function shouldLeave(d, leftOn, cfg = DEFAULTS) {
    return cfg.workdays.includes(d.getDay()) && nowMin(d) >= minutes(cfg.leaveAt) && leftOn !== dayKey(d);
  }
  /** Gone since an earlier day and it's past backAt? */
  function shouldReturn(d, leftOn, cfg = DEFAULTS) {
    return leftOn != null && leftOn !== dayKey(d) && nowMin(d) >= minutes(cfg.backAt);
  }

  const api = { DEFAULTS, shouldLeave, shouldReturn, dayKey };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.Offwork = api;
})(typeof window !== 'undefined' ? window : globalThis);
