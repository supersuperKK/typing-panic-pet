// Pure "brain" of the pet: no DOM, no Tauri. Testable with plain Node.
(function (root) {
  const DEFAULTS = {
    windowMs: 3000,       // KPS is measured over the last 3 seconds
    smooth: 0.15,         // EMA factor for KPS (lower = calmer face)
    calmKps: 1.5,         // below this, stress drains (v0.6: was 3, too forgiving)
    alertKps: 1.5,        // smoothed KPS above this = alert (watching you)
    alertStress: 12,
    nervousKps: 3.5,      // smoothed KPS above this = nervous
    nervousStress: 35,    // or stress above this = nervous
    gain: 0.6,            // stress per second per KPS above calmKps (~1 min of normal 4 kps typing to collapse)
    decay: 1.2,           // stress lost per second when calm
    panicStress: 65,      // stress above this = running around screaming
    collapseAt: 100,      // stress that knocks it out
    recoverBelow: 30,     // gets back up once stress drops below this
    collapseDecay: 5,     // v0.6.1: while knocked out it can't hear you, stress drains this fast
                          // (~14 s), even if you keep typing - before, typing kept it dead forever
    sleepAfterMs: 5 * 60 * 1000,
    reactionMs: 900,      // how long a backspace/enter/save reaction shows
  };

  function createPet(opts = {}) {
    const c = Object.assign({}, DEFAULTS, opts);
    const s = {
      presses: [], kps: 0, stress: 0, state: 'idle',
      lastKeyAt: null, lastTick: null, reaction: null, reactionUntil: 0,
      backspaceStreak: 0,
    };

    function key(kind, now) {
      s.presses.push(now);
      s.lastKeyAt = now;
      if (kind === 'backspace') {
        s.backspaceStreak++;
        if (s.backspaceStreak >= 3) setReaction('facepalm', now);
      } else {
        s.backspaceStreak = 0;
        if (kind === 'enter') setReaction('jump', now);
        if (kind === 'save') setReaction('thumbs', now);
      }
      if (s.state === 'sleep') s.state = 'idle';
    }

    function setReaction(r, now, ms = c.reactionMs) {
      if (s.state === 'collapse') return false; // too busy being dead
      s.reaction = r;
      s.reactionUntil = now + ms;
      if (s.state === 'sleep') s.state = 'idle';
      return true;
    }

    /** Calm it down (petting, snacks). */
    function soothe(amount) { s.stress = Math.max(0, s.stress - amount); }

    function tick(now) {
      const dt = s.lastTick == null ? 0 : Math.min((now - s.lastTick) / 1000, 1);
      s.lastTick = now;

      while (s.presses.length && s.presses[0] < now - c.windowMs) s.presses.shift();
      const raw = s.presses.length / (c.windowMs / 1000);
      s.kps += (raw - s.kps) * c.smooth;

      if (s.state === 'collapse') s.stress -= c.collapseDecay * dt;
      else if (raw > c.calmKps) s.stress += (raw - c.calmKps) * c.gain * dt;
      else s.stress -= c.decay * dt;
      s.stress = Math.max(0, Math.min(c.collapseAt, s.stress));

      const idleMs = s.lastKeyAt == null ? Infinity : now - s.lastKeyAt;

      if (s.state === 'collapse') {
        if (s.stress < c.recoverBelow) s.state = 'idle';
      } else if (s.stress >= c.collapseAt) {
        s.state = 'collapse';
        s.reaction = null;
      } else if (s.stress > c.panicStress) {
        s.state = 'panic';
      } else if (s.kps > c.nervousKps || s.stress > c.nervousStress) {
        s.state = 'nervous';
      } else if (s.kps > c.alertKps || s.stress > c.alertStress) {
        s.state = 'alert';
      } else if (idleMs >= c.sleepAfterMs && s.lastKeyAt != null) {
        s.state = 'sleep';
      } else {
        s.state = 'idle';
      }

      if (s.reaction && now >= s.reactionUntil) s.reaction = null;
      return snapshot();
    }

    function snapshot() {
      return {
        state: s.state,
        reaction: s.reaction,
        kps: Math.round(s.kps * 10) / 10,
        stress: Math.round(s.stress),
      };
    }

    return { key, tick, snapshot, react: setReaction, soothe, config: c };
  }

  const api = { createPet, DEFAULTS };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.PetBrain = api;
})(typeof window !== 'undefined' ? window : globalThis);
