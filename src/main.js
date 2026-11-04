const META = { size: 48, scale: 3 };
const FRAMES = { idle: 4, alert: 2, nervous: 4, panic: 4, collapse: 2, sleep: 2, jump: 3, thumbs: 2, facepalm: 2, offwork: 2, walk: 2,
  poke: 2, dizzy: 2, happy: 3, eat: 4, held: 2, stretch: 2, cheer: 2, deaf: 2 };
const ANIM = {
  idle: { fps: 3 }, alert: { fps: 4 }, nervous: { fps: 12 }, panic: { fps: 10 },
  collapse: { fps: 2 }, sleep: { fps: 1.5 }, jump: { fps: 8, once: true },
  thumbs: { fps: 4 }, facepalm: { fps: 3 }, offwork: { fps: 4 }, walk: { fps: 6 },
  poke: { fps: 6, once: true }, dizzy: { fps: 4 }, happy: { fps: 4 }, eat: { fps: 3 },
  held: { fps: 6 }, stretch: { fps: 1.5 }, cheer: { fps: 5 }, deaf: { fps: 1.5 },
};
// how long each interaction reaction stays on screen (ms)
const HOLD = { poke: 700, dizzy: 2400, happy: 1800, eat: 2600, stretch: 3500, cheer: 2200, held: 500 };
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
  poke: ['哎！', '干嘛戳我', '痒痒的', '嗯？叫我吗'],
  dizzy: ['别戳啦，头好晕～', '@_@ 转圈圈…', '我要生气了哦！'],
  happy: ['嘿嘿，好舒服', '再摸摸～', '心情变好了'],
  eat: ['嚼嚼嚼…好吃！', '谢谢投喂～', '饼干！最喜欢了'],
  full: ['今天吃不下啦', '肚子圆滚滚了'],
  held: ['哇！放我下来', '飞起来了～', '要去哪里呀'],
  land: ['呼，落地', '新家不错'],
  stretch: ['敲了快一小时了，起来动动吧～', '伸个懒腰，喝口水？'],
  deadpoke: ['别戳了…我已经没了', '……（没反应）'],
  deaf: ['我听不到键盘…点我一下去开权限'],
  deafpoke: ['在「辅助功能」里把我打开就好', '打开了还听不到？重启我一下'],
};
// Tray → 灵敏度
const SENS = {
  low:  { calmKps: 2.5, alertKps: 2.5, nervousKps: 5,   gain: 0.4 },
  mid:  { calmKps: 1.5, alertKps: 1.5, nervousKps: 3.5, gain: 0.6 },
  high: { calmKps: 1,   alertKps: 1,   nervousKps: 2.5, gain: 0.9 },
};

const pet = PetBrain.createPet();
const touch = Interact.createInteract();
const stats = Interact.createStats(JSON.parse(localStorage.getItem('pet.stats') || 'null'));
const saveStats = () => localStorage.setItem('pet.stats', JSON.stringify(stats.save()));
setInterval(saveStats, 10000);
window.addEventListener('beforeunload', saveStats);
const $pet = document.getElementById('pet');
const $sprite = document.getElementById('sprite');
const $bubble = document.getElementById('bubble');
// v0.6: the sprout on its head is the stress meter (0 perky … 3 withered)
const STAGE_AT = [25, 50, 75];
let stage = 0;
function sproutStage(stress) {
  // a little hysteresis so the leaves don't flicker at a boundary
  while (stage < 3 && stress >= STAGE_AT[stage] + 3) stage++;
  while (stage > 0 && stress < STAGE_AT[stage - 1] - 3) stage--;
  return stage;
}
let permOk = true;   // macOS: false until the keyboard (Accessibility) permission is granted
const invoke = (cmd, args) => (window.__TAURI__ ? window.__TAURI__.core.invoke(cmd, args) : Promise.resolve(null));

let anim = '', animFile = '', animStart = 0, lineKey = '';
let paused = false;
// off-work phases: null → 'offwork' (wave) → 'walk' → 'gone' ⇄ 'peek'
let phase = null, phaseAt = 0;
let leftOn = localStorage.getItem('pet.leftOn');
// a one-off line that wins over the state's usual line until `until`
let override = null;
let lastState = 'idle';
let hoverAt = null, hoverStill = 0;  // for the stats card
let dragging = false, lastMoveAt = 0;

const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];

function sayText(text, ms, now) {
  override = { text, until: now + ms };
  lineKey = '';
}
const fmt = (n) => n.toLocaleString('en-US');
function statsLine() {
  const t = stats.today(new Date());
  return `今天敲了 ${fmt(t.keys)} 下 · 崩溃 ${t.collapses} 次 · 亲密度 ♥${t.love}`;
}

function say(key) {
  if (override) {
    if (performance.now() < override.until) {
      if ($bubble.textContent !== override.text) $bubble.textContent = override.text;
      $bubble.classList.add('show');
      return;
    }
    override = null; lineKey = '';
  }
  if (key === lineKey) return;
  lineKey = key;
  const line = pick(LINES[key] || ['']);
  $bubble.textContent = line;
  $bubble.classList.toggle('show', !!line);
}

function setAnim(name, now, st = 0) {
  const file = (st && name !== 'collapse') ? `${name}-s${st}` : name;
  if (name !== anim) { anim = name; animStart = now; }
  if (file === animFile) return;
  animFile = file;
  $sprite.style.backgroundImage = `url(sprites/${file}.png)`;
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
  const hit = stats.key(new Date(), now);
  if (phase === 'gone' || phase === 'peek') { setPhase('peek', now); return; }
  if (phase) return;
  pet.key(kind, now);
  if (hit && hit.milestone && pet.react('cheer', now, HOLD.cheer)) sayText(`今天第 ${fmt(hit.milestone)} 下！`, HOLD.cheer, now);
  if (hit && hit.stretch && pet.react('stretch', now, HOLD.stretch)) lineKey = '';
}

// ---- mouse: poke, rub, feed, carry ----
function interact(kind, now) {
  if (phase) return;
  if (!permOk) { invoke('open_permission_settings'); return sayText(pick(LINES.deafpoke), 3000, now); }
  override = null; hoverAt = null;
  const d = new Date();
  const dead = pet.snapshot().state === 'collapse';
  if (kind === 'poke' || kind === 'dizzy') {
    stats.poke(d);
    if (dead) return sayText(pick(LINES.deadpoke), 1500, now);
    pet.react(kind, now, HOLD[kind]);
  } else if (kind === 'happy') {
    stats.pet(d);
    pet.soothe(15);
    if (!dead) pet.react('happy', now, HOLD.happy);
  } else if (kind === 'feed') {
    if (!stats.snack(d)) { pet.react('poke', now, HOLD.poke); return sayText(pick(LINES.full), 1800, now); }
    pet.soothe(25);
    if (dead) return sayText('嚼嚼…回了一点血', 2000, now);
    pet.react('eat', now, HOLD.eat);
  }
  lineKey = '';
  saveStats();
}

let downAt = null;
$sprite.addEventListener('mousedown', (e) => {
  if (e.button !== 0) return;
  downAt = { x: e.screenX, y: e.screenY };
});
window.addEventListener('mousemove', (e) => {
  const now = performance.now();
  if (downAt && (e.buttons & 1)) {
    if (Math.abs(e.screenX - downAt.x) + Math.abs(e.screenY - downAt.y) > 4) {
      downAt = null;
      if (window.__TAURI__) { dragging = true; lastMoveAt = now; window.__TAURI__.window.getCurrentWindow().startDragging(); }
    }
    return;
  }
  if (e.target === $sprite) {
    hoverAt = now; hoverStill = now;
    const r = touch.hover(e.screenX, now);
    if (r) interact(r, now);
  }
});
$sprite.addEventListener('mouseup', (e) => {
  if (e.button !== 0 || !downAt) return;
  downAt = null;
  interact(touch.click(performance.now()), performance.now());
});
$sprite.addEventListener('dblclick', () => interact('feed', performance.now()));
$sprite.addEventListener('mouseleave', () => { touch.leave(); hoverAt = null; });

function render(now) {
  const snap = pet.tick(now);
  if (snap.state === 'collapse' && lastState !== 'collapse') stats.collapse(new Date());
  lastState = snap.state;

  // being carried around
  if (dragging) {
    if (now - lastMoveAt < 450) pet.react('held', now, HOLD.held);
    else if (now - lastMoveAt > 450) { dragging = false; if (pet.react('poke', now, HOLD.poke)) sayText(pick(LINES.land), 1400, now); }
  }
  // hovering still over it for a moment shows today's stats
  if (hoverAt && !phase && now - hoverStill > 1500 && !override && !snap.reaction) { hoverAt = null; sayText(statsLine(), 3500, now); }

  // ---- off-work schedule ----
  const d = new Date();
  if (!phase && snap.state !== 'collapse' && Offwork.shouldLeave(d, leftOn)) leave(now);
  if ((phase === 'gone' || phase === 'peek') && Offwork.shouldReturn(d, leftOn)) comeBack(now);
  if (phase === 'offwork' && now - phaseAt > 2600) {
    setPhase('walk', now);
    const t = stats.today(d);
    sayText(t.keys ? `今天你敲了 ${fmt(t.keys)} 下，辛苦啦，明天见！` : '明天见！', 3200, now);
  }
  if (phase === 'walk' && now - phaseAt > 3200) setPhase('gone', now);
  if (phase === 'peek' && now - phaseAt > 3000) setPhase('gone', now);

  // ---- choose animation, line, classes ----
  let name, line, cls;
  if (phase === 'offwork') { name = 'offwork'; line = 'offwork'; cls = 'offwork'; }
  else if (phase === 'walk') { name = 'walk'; line = 'walk'; cls = 'walk'; }
  else if (phase === 'gone') { name = 'walk'; line = 'gone'; cls = 'gone'; }
  else if (phase === 'peek') { name = 'alert'; line = 'peek'; cls = 'peek flip'; }
  else if (!permOk && !snap.reaction) { name = 'deaf'; line = 'deaf'; cls = 'idle'; }
  else if (paused && !snap.reaction) { name = 'sleep'; line = 'paused'; cls = 'idle'; }
  else {
    name = snap.reaction || snap.state; line = name;
    const flip = snap.state === 'panic' && Math.floor((now - animStart) / 1100) % 2 === 1;
    cls = snap.state + (flip ? ' flip' : '') + (snap.reaction === 'held' ? ' held' : '');
  }
  if (lineKey === 'back' && name === 'jump') line = 'back';
  setAnim(name, now, sproutStage(snap.stress));
  say(line);
  $pet.className = cls;

  const a = ANIM[anim], n = FRAMES[anim];
  let f = Math.floor((now - animStart) / 1000 * a.fps);
  f = a.once ? Math.min(f, n - 1) : f % n;
  $sprite.style.backgroundPosition = `${-f * META.size * META.scale}px 0`;

  sendHitbox(phase === 'gone');
}

// v0.6: tell the native side where the pet's body is, so clicks anywhere else on the
// transparent window fall through to the desktop.
let lastBox = '';
function sendHitbox(hidden) {
  if (!window.__TAURI__) return;
  const r = $sprite.getBoundingClientRect();
  // the body + sprout fill roughly the middle 80% of the 48px frame
  const box = hidden ? { cx: 0, cy: 0, rx: 0, ry: 0 }
    : { cx: Math.round(r.left + r.width / 2), cy: Math.round(r.top + r.height * 0.56), rx: Math.round(r.width * 0.42), ry: Math.round(r.height * 0.4) };
  const key = `${box.cx},${box.cy},${box.rx},${box.ry}`;
  if (key === lastBox) return;
  lastBox = key;
  invoke('set_hitbox', box);
}

if (window.__TAURI__) {
  const { listen } = window.__TAURI__.event;
  listen('pet-key', (e) => onKey(e.payload.kind, performance.now()));
  listen('pet-paused', (e) => { paused = !!e.payload; });
  listen('pet-sensitivity', (e) => Object.assign(pet.config, SENS[e.payload] || SENS.mid));
  listen('pet-offwork', () => { const now = performance.now(); phase ? comeBack(now) : leave(now); });
  listen('pet-feed', () => interact('feed', performance.now()));
  listen('pet-stats', () => sayText(statsLine(), 4000, performance.now()));
  const checkPerm = () => invoke('keyboard_permission').then((ok) => { permOk = ok !== false; });
  checkPerm(); setInterval(checkPerm, 3000);
  window.__TAURI__.window.getCurrentWindow().onMoved(() => { if (dragging) lastMoveAt = performance.now(); });
} else {
  // Plain browser preview: keys typed in this page; F2 = clock out, F3 = feed, F4 = stats.
  window.addEventListener('keydown', (e) => {
    const now = performance.now();
    if (e.key === 'F2') { e.preventDefault(); phase ? comeBack(now) : leave(now); return; }
    if (e.key === 'F3') { e.preventDefault(); interact('feed', now); return; }
    if (e.key === 'F4') { e.preventDefault(); sayText(statsLine(), 4000, now); return; }
    const kind = e.key === 'Backspace' ? 'backspace'
      : e.key === 'Enter' ? 'enter'
      : (e.key === 's' && (e.ctrlKey || e.metaKey)) ? 'save' : 'key';
    if (kind === 'save') e.preventDefault();
    onKey(kind, now);
  });
}

for (const name of Object.keys(FRAMES)) {
  new Image().src = `sprites/${name}.png`;
  if (name !== 'collapse') for (let k = 1; k <= 3; k++) new Image().src = `sprites/${name}-s${k}.png`;
}

// v0.6: first launch says hello and what it does (and doesn't) look at
if (!localStorage.getItem('pet.welcomed')) {
  localStorage.setItem('pet.welcomed', '1');
  const t0 = performance.now();
  sayText('你好，我是团子！', 2600, t0);
  setTimeout(() => sayText('我只数你敲了几下，不看你打了什么', 4200, performance.now()), 2700);
}
function loop(now) { render(now); requestAnimationFrame(loop); }
requestAnimationFrame(loop);
