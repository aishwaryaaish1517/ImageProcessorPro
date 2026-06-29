from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont
import numpy as np
import os, io, base64, uuid

app = Flask(__name__)
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

ALLOWED = {"png","jpg","jpeg","gif","bmp","webp","tiff"}

def allowed(fname):
    return "." in fname and fname.rsplit(".",1)[1].lower() in ALLOWED

def img_to_b64(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if "image" not in request.files:
        return jsonify({"error": "No file sent"}), 400
    f = request.files["image"]
    if not f.filename or not allowed(f.filename):
        return jsonify({"error": "Invalid file type"}), 400
    uid = str(uuid.uuid4())[:8]
    ext = f.filename.rsplit(".",1)[1].lower()
    path = os.path.join(UPLOAD_DIR, f"{uid}.{ext}")
    f.save(path)
    img = Image.open(path)
    return jsonify({"id":uid, "ext":ext, "w":img.width, "h":img.height, "preview":img_to_b64(img)})

@app.route("/process", methods=["POST"])
def process():
    d = request.json
    uid, ext, op = d.get("id"), d.get("ext","png"), d.get("operation","")
    p = d.get("params", {})
    path = os.path.join(UPLOAD_DIR, f"{uid}.{ext}")
    if not os.path.exists(path):
        return jsonify({"error":"Image not found"}), 404
    img = Image.open(path).convert("RGBA")

    if   op == "grayscale": img = img.convert("L").convert("RGBA")
    elif op == "blur":      img = img.filter(ImageFilter.GaussianBlur(int(p.get("r",3))))
    elif op == "sharpen":   img = img.filter(ImageFilter.SHARPEN)
    elif op == "edge":      img = img.convert("RGB").filter(ImageFilter.FIND_EDGES).convert("RGBA")
    elif op == "emboss":    img = img.filter(ImageFilter.EMBOSS)
    elif op == "flip_h":    img = img.transpose(Image.FLIP_LEFT_RIGHT)
    elif op == "flip_v":    img = img.transpose(Image.FLIP_TOP_BOTTOM)
    elif op == "rotate":
        img = img.rotate(-float(p.get("angle",90)), expand=True)
    elif op == "resize":
        img = img.resize((int(p.get("w",img.width)), int(p.get("h",img.height))), Image.LANCZOS)
    elif op == "brightness":
        img = ImageEnhance.Brightness(img.convert("RGB")).enhance(float(p.get("v",1.2))).convert("RGBA")
    elif op == "contrast":
        img = ImageEnhance.Contrast(img.convert("RGB")).enhance(float(p.get("v",1.2))).convert("RGBA")
    elif op == "sepia":
        a = np.array(img.convert("RGB"), dtype=np.float64)
        r = np.clip(a[:,:,0]*.393+a[:,:,1]*.769+a[:,:,2]*.189,0,255)
        g = np.clip(a[:,:,0]*.349+a[:,:,1]*.686+a[:,:,2]*.168,0,255)
        b = np.clip(a[:,:,0]*.272+a[:,:,1]*.534+a[:,:,2]*.131,0,255)
        img = Image.fromarray(np.stack([r,g,b],2).astype(np.uint8)).convert("RGBA")
    elif op == "enhance":
        rgb = img.convert("RGB")
        for fn, v in [(ImageEnhance.Sharpness,1.5),(ImageEnhance.Contrast,1.2),
                      (ImageEnhance.Color,1.15),(ImageEnhance.Brightness,1.05)]:
            rgb = fn(rgb).enhance(v)
        img = rgb.convert("RGBA")
    elif op == "watermark":
        txt  = p.get("text","© Watermark")
        ov   = Image.new("RGBA", img.size, (0,0,0,0))
        dr   = ImageDraw.Draw(ov)
        try:    font = ImageFont.truetype("arial.ttf", max(img.width//20,20))
        except: font = ImageFont.load_default()
        bb = dr.textbbox((0,0), txt, font=font)
        tw,th = bb[2]-bb[0], bb[3]-bb[1]
        dr.text((img.width-tw-20, img.height-th-20), txt, fill=(255,255,255,160), font=font)
        img = Image.alpha_composite(img, ov)

    out = os.path.join(OUTPUT_DIR, f"{uid}_{op}.png")
    img.save(out)
    return jsonify({"preview": img_to_b64(img), "out_id": f"{uid}_{op}"})

@app.route("/download/<oid>")
def download(oid):
    p = os.path.join(OUTPUT_DIR, f"{oid}.png")
    return send_file(p, as_attachment=True, download_name=f"{oid}.png") if os.path.exists(p) else ("Not found",404)

if __name__ == "__main__":
    print("\n🌐  Image Processor Pro — Web Interface")
    print("📌  Open your browser:  http://localhost:5000\n")
    app.run(debug=True, host="0.0.0.0", port=5000)