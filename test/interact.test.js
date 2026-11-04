const assert = require('assert');
const { createInteract, createStats } = require('../src/interact.js');

// pokes: 4 quick pokes are pokes, the 5th makes it dizzy, then it resets
let it = createInteract();
for (let i = 0; i < 4; i++) assert.strictEqual(it.click(i * 300), 'poke');
assert.strictEqual(it.click(1300), 'dizzy');
assert.strictEqual(it.click(1400), 'poke');
// slow pokes never make it dizzy
it = createInteract();
for (let i = 0; i < 10; i++) assert.strictEqual(it.click(i * 1000), 'poke');

// petting: rubbing back and forth → happy; a straight pass doesn't count
it = createInteract();
let got = null, t = 0;
for (let i = 0; i < 40 && !got; i++) { got = it.hover(i % 10 < 5 ? (i % 5) * 4 : 20 - (i % 5) * 4, t); t += 30; }
assert.strictEqual(got, 'happy');
it = createInteract(); got = null;
for (let x = 0; x < 200; x += 3) got = got || it.hover(x, x * 10);
assert.strictEqual(got, null);

// stats: milestones, daily snack limit, day rollover keeps affection
const d1 = new Date(2026, 10, 4, 10, 0), d2 = new Date(2026, 10, 5, 10, 0);
let st = createStats(null);
let ms = null;
for (let i = 0; i < 500; i++) ms = st.key(d1, i * 200) || ms;
assert.deepStrictEqual(ms, { milestone: 500 });
assert.strictEqual(st.today(d1).keys, 500);
assert.ok(st.snack(d1) && st.snack(d1) && st.snack(d1));
assert.strictEqual(st.snack(d1), false);
st.pet(d1);
assert.strictEqual(st.today(d1).love, 7);
const restored = createStats(JSON.parse(JSON.stringify(st.save())));
assert.strictEqual(restored.today(d1).keys, 500);
assert.strictEqual(restored.today(d2).keys, 0);
assert.strictEqual(restored.today(d2).love, 7);
assert.ok(restored.snack(d2));

// break reminder after 50 min of steady typing, once, re-armed by a 5 min rest
st = createStats(null);
let stretch = 0;
for (let now = 0; now <= 52 * 60000; now += 2000) if ((st.key(d1, now) || {}).stretch) stretch++;
assert.strictEqual(stretch, 1);
for (let now = 58 * 60000; now <= 110 * 60000; now += 2000) if ((st.key(d1, now) || {}).stretch) stretch++;
assert.strictEqual(stretch, 2);

console.log('interact tests passed');
