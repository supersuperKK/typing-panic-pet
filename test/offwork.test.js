const assert = require('assert');
const { shouldLeave, shouldReturn, dayKey } = require('../src/offwork.js');
const wed = (h, m) => new Date(2026, 10, 4, h, m);   // Wed 2026-11-04
const sat = (h, m) => new Date(2026, 10, 7, h, m);
assert.strictEqual(shouldLeave(wed(17, 29), null), false);
assert.strictEqual(shouldLeave(wed(17, 30), null), true);
assert.strictEqual(shouldLeave(wed(20, 0), dayKey(wed(17, 30))), false, 'only once a day');
assert.strictEqual(shouldLeave(sat(18, 0), null), false, 'weekend');
assert.strictEqual(shouldReturn(new Date(2026, 10, 5, 8, 59), dayKey(wed(17, 30))), false);
assert.strictEqual(shouldReturn(new Date(2026, 10, 5, 9, 0), dayKey(wed(17, 30))), true);
assert.strictEqual(shouldReturn(wed(23, 0), dayKey(wed(17, 30))), false);
console.log('offwork tests passed');
