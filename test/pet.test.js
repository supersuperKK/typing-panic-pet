const assert = require('assert');
const { createPet } = require('../src/pet.js');

function run(pet, fromMs, toMs, kpsTyping, stepMs = 50) {
  let next = fromMs, last;
  for (let t = fromMs; t <= toMs; t += stepMs) {
    if (kpsTyping > 0) while (next <= t) { pet.key('key', next); next += 1000 / kpsTyping; }
    last = pet.tick(t);
  }
  return last;
}

// 1. Starts idle.
let p = createPet();
assert.strictEqual(p.tick(0).state, 'idle');

// 2. Gentle typing (2 kps) for a minute stays idle.
assert.strictEqual(run(p, 0, 60000, 2).state, 'idle');

// 3. A short burst (8 kps for 4s) makes it nervous but not dead.
p = createPet();
let s = run(p, 0, 4000, 8);
assert.strictEqual(s.state, 'nervous', JSON.stringify(s));

// 3b. Steady 4 kps: alert, not nervous.
p = createPet();
s = run(p, 0, 15000, 4);
assert.strictEqual(s.state, 'alert', JSON.stringify(s));

// 3c. Sustained 10 kps passes through panic before collapse.
p = createPet();
const seen = new Set(); { let n = 0; for (let t = 0; t <= 120000; t += 50) { while (n <= t) { p.key('key', n); n += 100; } seen.add(p.tick(t).state); } }
for (const st of ['alert', 'nervous', 'panic', 'collapse']) assert.ok(seen.has(st), 'missing ' + st);

// 4. Sustained hammering (10 kps) eventually collapses it.
p = createPet();
s = run(p, 0, 120000, 10);
assert.strictEqual(s.state, 'collapse', JSON.stringify(s));
const collapsedAt = 120000;

// 5. Still collapsed while you keep typing.
s = run(p, collapsedAt, collapsedAt + 5000, 10);
assert.strictEqual(s.state, 'collapse');

// 6. Recovers after you stop and stress drains.
s = run(p, collapsedAt + 5000, collapsedAt + 60000, 0);
assert.strictEqual(s.state, 'idle', JSON.stringify(s));

// 7. Reactions.
p = createPet();
p.key('enter', 0); assert.strictEqual(p.tick(10).reaction, 'jump');
assert.strictEqual(p.tick(2000).reaction, null);
p.key('save', 3000); assert.strictEqual(p.tick(3010).reaction, 'thumbs');
p.key('backspace', 5000); p.key('backspace', 5100); assert.notStrictEqual(p.tick(5110).reaction, 'facepalm');
p.key('backspace', 5200); assert.strictEqual(p.tick(5210).reaction, 'facepalm');

// 8. Falls asleep after 5 idle minutes, wakes on a key.
p = createPet();
p.key('key', 0);
s = run(p, 0, 5 * 60 * 1000 + 1000, 0, 1000);
assert.strictEqual(s.state, 'sleep');
p.key('key', 301500); assert.strictEqual(p.tick(301510).state, 'idle');

// Report how long to collapse at various speeds.
for (const k of [6, 8, 10, 12]) {
  const q = createPet(); let t = 0, n = 0;
  while (t < 600000) { while (n <= t) { q.key('key', n); n += 1000 / k; } if (q.tick(t).state === 'collapse') break; t += 50; }
  console.log(`${k} keys/s -> collapse after ${t < 600000 ? (t/1000).toFixed(1) + 's' : 'never (10 min)'}`);
}
console.log('all tests passed');

// v0.5: interactions
{
  const q = createPet();
  q.tick(0);
  assert.ok(q.react('poke', 0, 700));
  assert.strictEqual(q.tick(100).reaction, 'poke');
  assert.strictEqual(q.tick(800).reaction, null);
  run(q, 1000, 21000, 10);                // stressed out
  const before = q.snapshot().stress;
  q.soothe(25);
  assert.strictEqual(q.snapshot().stress, Math.max(0, before - 25));
  console.log('interaction hooks passed');
}
