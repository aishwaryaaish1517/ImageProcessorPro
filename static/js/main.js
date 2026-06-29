/* =============================================================
   FILE:     static/js/main.js
   LOCATION: ImageProcessorPro/static/js/main.js
   PURPOSE:  JavaScript logic for the Flask web interface
============================================================= */

let imgId = null, imgExt = null;

// ── Slider labels ──────────────────────────────────────────────────────────
document.getElementById('sl-blur').addEventListener('input', function () {
  document.getElementById('lbl-blur').textContent = this.value;
});
document.getElementById('sl-bright').addEventListener('input', function () {
  document.getElementById('lbl-bright').textContent = (this.value / 100).toFixed(1) + '×';
});

// ── File input ─────────────────────────────────────────────────────────────
document.getElementById('file-input').addEventListener('change', function (e) {
  if (e.target.files[0]) uploadFile(e.target.files[0]);
});

// ── Drag & drop ────────────────────────────────────────────────────────────
const dz = document.getElementById('drop-zone');
document.body.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag'); });
document.body.addEventListener('dragleave', () => dz.classList.remove('drag'));
document.body.addEventListener('drop', e => {
  e.preventDefault(); dz.classList.remove('drag');
  const f = e.dataTransfer.files[0];
  if (f && f.type.startsWith('image/')) uploadFile(f);
});

// ── Upload ─────────────────────────────────────────────────────────────────
function uploadFile(file) {
  setStatus('📂 Uploading…', '#FFD166'); progress(30);
  const fd = new FormData();
  fd.append('image', file);
  fetch('/upload', { method: 'POST', body: fd })
    .then(r => r.json())
    .then(d => {
      if (d.error) { setStatus('❌ ' + d.error, '#EF476F'); return; }
      imgId = d.id; imgExt = d.ext;
      showOriginal(d.preview);
      document.getElementById('file-info').textContent =
        `${file.name}  •  ${d.w} × ${d.h} px`;
      resetOutput();
      setStatus('✅ Loaded: ' + file.name, '#06D6A0');
      progress(100);
    })
    .catch(() => setStatus('❌ Upload failed', '#EF476F'));
}

// ── Apply operation ────────────────────────────────────────────────────────
function applyOp(op, params = {}) {
  if (!imgId) { setStatus('⚠️ Open an image first', '#FFD166'); return; }
  setStatus('⚙️ Processing…', '#00B4D8'); progress(40); spin(true);
  fetch('/process', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: imgId, ext: imgExt, operation: op, params })
  })
    .then(r => r.json())
    .then(d => {
      if (d.error) { setStatus('❌ ' + d.error, '#EF476F'); return; }
      showOutput(d.preview, d.out_id);
      setStatus('✅ ' + op + ' applied', '#06D6A0');
      progress(100); spin(false);
    })
    .catch(() => { setStatus('❌ Error', '#EF476F'); spin(false); });
}

// ── Named operations (called from sidebar buttons) ─────────────────────────
function doBlur()       { applyOp('blur',       { r: document.getElementById('sl-blur').value }); }
function doBrightness() { applyOp('brightness',  { v: document.getElementById('sl-bright').value / 100 }); }
function doContrast()   { applyOp('contrast',    { v: document.getElementById('sl-bright').value / 100 }); }
function doRotate()     { applyOp('rotate',      { angle: parseFloat(document.getElementById('inp-angle').value) || 90 }); }
function doResize() {
  const w = prompt('New width (pixels):');  if (!w) return;
  const h = prompt('New height (pixels):'); if (!h) return;
  applyOp('resize', { w: parseInt(w), h: parseInt(h) });
}
function doWatermark() {
  const txt = document.getElementById('inp-wm').value || '© Watermark';
  applyOp('watermark', { text: txt });
}
function doDownload() {
  const id = document.getElementById('out-id').textContent;
  if (!id) { setStatus('⚠️ No processed image yet', '#FFD166'); return; }
  window.location.href = '/download/' + id;
}

// ── DOM helpers ────────────────────────────────────────────────────────────
function showOriginal(src) {
  const img = document.getElementById('orig-img');
  const dz  = document.getElementById('drop-zone');
  img.src = src; img.style.display = 'block';
  dz.style.display = 'none';
}

function showOutput(src, outId) {
  const img = document.getElementById('out-img');
  const ph  = document.getElementById('out-ph');
  img.src = src; img.style.display = 'block';
  ph.style.display = 'none';
  document.getElementById('out-id').textContent = outId;
}

function resetOutput() {
  const img = document.getElementById('out-img');
  const ph  = document.getElementById('out-ph');
  img.style.display = 'none';
  ph.style.display = 'block';
  document.getElementById('out-id').textContent = '';
}

function setStatus(msg, color = '#8B949E') {
  const s = document.getElementById('status');
  s.textContent = msg; s.style.color = color;
}

function progress(pct) {
  document.getElementById('pbar').style.width = pct + '%';
}

function spin(show) {
  document.getElementById('spinner').style.display = show ? 'block' : 'none';
}