const META = { size: 48, scale: 3 };
const FRAMES = { idle: 4, alert: 2, nervous: 4, panic: 4, collapse: 2, sleep: 2, jump: 3, thumbs: 2, facepalm: 2, offwork: 2, walk: 2 };
const ANIM = {
  idle: { fps: 3 }, alert: { fps: 4 }, nervous: { fps: 12 }, panic: { fps: 10 },
  collapse: { fps: 2 }, sleep: { fps: 1.5 }, jump: { fps: 8, once: true },
  thumbs: { fps: 4 }, facepalm: { fps: 3 }, offwork: { fps: 4 }, walk: { fps: 6 },
};
const LINES = {
  idle: ['', '', '今天也很平静'],
  alert: ['嗯？', '你要开始了吗', ''],
  nervous: ['慢、慢点…', '手速太快了！', '我有点慌'],
  panic: ['啊啊啊啊！', '救命！！', '键盘要着火了'],
  collapse: ['我不行了…', '停一下，求你了', '……'],
  sleep: ['zzZ'], paused: ['暂停中，我先睡会'],
  jump: ['嘿！'], thumbs: ['保存得好'], facepalm: ['又删了…'],
  offwork: ['17:30！下班啦～'], walk: ['明天见！'], gone: [''],
  peek: ['你怎么还在加班…', '还不走吗？', '我先走了哦'],
  back: ['早上好，上班啦'],
};
// Tray → 灵敏度
const SENS = {
  low:  { calmKps: 4, alertKps: 3.5, nervousKps: 6.5, gain: 0.12 },
  mid:  { calmKps: 3, alertKps: 2.5, nervousKps: 5,   gain: 0.2 },
  high: { calmKps: 2, alertKps: 1.8, nervousKps: 4,   gain: 0.35 },
};

const pet = PetBrain.createPet();
const $pet = document.getElementById('pet');
const $sprite = document.getElementById('sprite');
const $bubble = document.getElementById('bubble');
const $fill = document.getElementById('fill');

let anim = '', animStart = 0, lineKey = '';
let paused = false;
// off-work phases: null → 'offwork' (wave) → 'walk' → 'gone' ⇄ 'peek'
let phase = null, phaseAt = 0;
let leftOn = localStorage.getItem('pet.leftOn');

const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];

function say(key) {
  if (key === lineKey) return;
  lineKey = key;
  const line = pick(LINES[key] || ['']);
  $bubble.textContent = line;
  $bubble.classList.toggle('show', !!line);
}

function setAnim(name, now) {
  if (name === anim) return;
  anim = name; animStart = now;
  $sprite.style.backgroundImage = `url(sprites/${name}.png)`;
  $sprite.style.backgroundSize = `${FRAMES[name] * META.size * META.scale}px ${META.size * META.scale}px`;
}

function setPhase(p, now) { phase = p; phaseAt = now; }

function leave(now) {
  leftOn = Offwork.dayKey(new Date());
  localStorage.setItem('pet.leftOn', leftOn);
  setPhase('offwork', now);
}
function comeBack(now) {
  setPhase(null, now);
  pet.key('enter', now); // reuse the jump reaction as a little "I'm back" hop
  lineKey = ''; say('back');
}

function onKey(kind, now) {
  if (phase === 'gone' || phase === 'peek') { setPhase('peek', now); return; }
  if (!phase) pet.key(kind, now);
}

function render(now) {
  const snap = pet.tick(now);

  // ---- off-work schedule ----
  const d = new Date();
  if (!phase && snap.state !== 'collapse' && Offwork.shouldLeave(d, leftOn)) leave(now);
  if ((phase === 'gone' || phase === 'peek') && Offwork.shouldReturn(d, leftOn)) comeBack(now);
  if (phase === 'offwork' && now - phaseAt > 2600) setPhase('walk', now);
  if (phase === 'walk' && now - phaseAt > 3200) setPhase('gone', now);
  if (phase === 'peek' && now - phaseAt > 3000) setPhase('gone', now);

  // ---- choose animation, line, classes ----
  let name, line, cls;
  if (phase === 'offwork') { name = 'offwork'; line = 'offwork'; cls = 'offwork'; }
  else if (phase === 'walk') { name = 'walk'; line = 'walk'; cls = 'walk'; }
  else if (phase === 'gone') { name = 'walk'; line = 'gone'; cls = 'gone'; }
  else if (phase === 'peek') { name = 'alert'; line = 'peek'; cls = 'peek flip'; }
  else if (paused) { name = 'sleep'; line = 'paused'; cls = 'idle'; }
  else {
    name = snap.reaction || snap.state; line = name;
    const flip = snap.state === 'panic' && Math.floor((now - animStart) / 1100) % 2 === 1;
    cls = snap.state + (flip ? ' flip' : '');
  }
  if (lineKey === 'back' && name === 'jump') line = 'back';
  setAnim(name, now);
  say(line);
  $pet.className = cls;

  const a = ANIM[anim], n = FRAMES[anim];
  let f = Math.floor((now - animStart) / 1000 * a.fps);
  f = a.once ? Math.min(f, n - 1) : f % n;
  $sprite.style.backgroundPosition = `${-f * META.size * META.scale}px 0`;

  $fill.style.width = snap.stress + '%';
  $fill.style.background = snap.stress > 70 ? '#ef6a6a' : snap.stress > 40 ? '#ffb15c' : '#7fcf6a';
}

if (window.__TAURI__) {
  const { listen } = window.__TAURI__.event;
  listen('pet-key', (e) => onKey(e.payload.kind, performance.now()));
  listen('pet-paused', (e) => { paused = !!e.payload; });
  listen('pet-sensitivity', (e) => Object.assign(pet.config, SENS[e.payload] || SENS.mid));
  listen('pet-offwork', () => { const now = performance.now(); phase ? comeBack(now) : leave(now); });
} else {
  // Plain browser preview: keys typed in this page; press F2 to preview clocking out.
  window.addEventListener('keydown', (e) => {
    const now = performance.now();
    if (e.key === 'F2') { e.preventDefault(); phase ? comeBack(now) : leave(now); return; }
    const kind = e.key === 'Backspace' ? 'backspace'
      : e.key === 'Enter' ? 'enter'
      : (e.key === 's' && (e.ctrlKey || e.metaKey)) ? 'save' : 'key';
    if (kind === 'save') e.preventDefault();
    onKey(kind, now);
  });
}

for (const name of Object.keys(FRAMES)) new Image().src = `sprites/${name}.png`;
function loop(now) { render(now); requestAnimationFrame(loop); }
requestAnimationFrame(loop);
