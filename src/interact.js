// Mouse interactions + daily stats. Pure logic, no DOM: testable in Node.
(function (root) {
  const DEFAULTS = {
    dizzyClicks: 5, dizzyWindowMs: 2500,    // 5 pokes in 2.5s = dizzy
    strokeTurns: 4, strokeWindowMs: 1500,   // mouse rubbing back and forth 4 times = petting
    strokeMinPx: 6,
    snacksPerDay: 3,
    milestones: [500, 1000, 3000, 5000, 10000, 20000],
    breakAfterMs: 50 * 60 * 1000,           // 50 min of typing without a 5 min rest → stretch reminder
    restMs: 5 * 60 * 1000,
  };

  function createInteract(opts = {}) {
    const c = Object.assign({}, DEFAULTS, opts);
    let clicks = [];
    let turns = [], lastX = null, dir = 0, travel = 0;

    /** A click on the pet → 'poke' or 'dizzy'. */
    function click(now) {
      clicks = clicks.filter((t) => t > now - c.dizzyWindowMs);
      clicks.push(now);
      if (clicks.length >= c.dizzyClicks) { clicks = []; return 'dizzy'; }
      return 'poke';
    }

    /** Hovering mouse x position → 'happy' when the user rubs it back and forth. */
    function hover(x, now) {
      if (lastX == null) { lastX = x; return null; }
      const dx = x - lastX; lastX = x;
      if (!dx) return null;
      const d = Math.sign(dx);
      travel += Math.abs(dx);
      if (d !== dir) {
        if (dir !== 0 && travel >= c.strokeMinPx) turns.push(now);
        dir = d; travel = 0;
      }
      turns = turns.filter((t) => t > now - c.strokeWindowMs);
      if (turns.length >= c.strokeTurns) { turns = []; return 'happy'; }
      return null;
    }
    function leave() { lastX = null; dir = 0; travel = 0; turns = []; }

    return { click, hover, leave, config: c };
  }

  const dayKey = (d) => `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
  const blank = (day) => ({ day, keys: 0, collapses: 0, pokes: 0, pets: 0, snacks: 0, hit: [] });

  /** Daily counters. `saved` is whatever was persisted last time (or null). */
  function createStats(saved, opts = {}) {
    const c = Object.assign({}, DEFAULTS, opts);
    let s = saved && saved.day ? Object.assign(blank(saved.day), saved) : blank(null);
    let love = (saved && saved.love) || 0;          // affection never resets
    let activeSince = null, lastKey = null, remindedAt = null;

    function roll(d) { const k = dayKey(d); if (s.day !== k) s = blank(k); }

    /** Count a key; returns {milestone} or {stretch} when something worth celebrating happened. */
    function key(d, now) {
      roll(d);
      s.keys++;
      if (lastKey == null || now - lastKey >= c.restMs) { activeSince = now; remindedAt = null; }
      lastKey = now;
      const m = c.milestones.find((x) => x === s.keys);
      if (m) { s.hit.push(m); return { milestone: m }; }
      if (remindedAt == null && now - activeSince >= c.breakAfterMs) { remindedAt = now; return { stretch: true }; }
      return null;
    }
    function collapse(d) { roll(d); s.collapses++; }
    function poke(d) { roll(d); s.pokes++; }
    function pet(d) { roll(d); s.pets++; love++; }
    /** Feed a snack; false when it's already had its fill today. */
    function snack(d) { roll(d); if (s.snacks >= c.snacksPerDay) return false; s.snacks++; love += 2; return true; }
    function today(d) { roll(d); return Object.assign({ love }, s); }
    function save() { return Object.assign({ love }, s); }

    return { key, collapse, poke, pet, snack, today, save };
  }

  const api = { DEFAULTS, createInteract, createStats, dayKey };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.Interact = api;
})(typeof window !== 'undefined' ? window : globalThis);
