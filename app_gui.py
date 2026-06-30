"""
=============================================================
  FILE: app_gui.py
  LOCATION: ImageProcessorPro/app_gui.py
  PURPOSE: Main Desktop GUI Application
  RUN WITH: python app_gui.py
=============================================================
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont, ImageTk
import cv2
import numpy as np
import os
import threading
import io

try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    TESSERACT_OK = True
except ImportError:
    TESSERACT_OK = False

try:
    from rembg import remove as rembg_remove
    REMBG_OK = True
except ImportError:
    REMBG_OK = False

#theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ACCENT  = "#00B4D8"
SUCCESS = "#06D6A0"
WARNING = "#FFD166"
DANGER  = "#EF476F"
BG_DARK = "#0D1117"
BG_CARD = "#161B22"
BG_SIDE = "#1A1F2E"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("⚡ Image Processor Pro")
        self.geometry("1300x820")
        self.minsize(1000, 650)
        self.configure(fg_color=BG_DARK)

        self.original_image  = None
        self.processed_image = None
        self.image_path      = None

        self._build_ui()

    #layout
    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._sidebar()
        self._main_area()
        self._statusbar()

    def _sidebar(self):
        sb = ctk.CTkScrollableFrame(self, width=255, fg_color=BG_SIDE, corner_radius=0)
        sb.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(sb, text="⚡ Image Processor Pro",
                     font=ctk.CTkFont("Segoe UI", 15, "bold"),
                     text_color=ACCENT).pack(pady=(18,2), padx=12)
        ctk.CTkLabel(sb, text="Professional Edition v1.0",
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color="#8B949E").pack(pady=(0,16))

        def sec(txt):
            ctk.CTkLabel(sb, text=txt, font=ctk.CTkFont("Segoe UI", 10, "bold"),
                         text_color="#8B949E", anchor="w").pack(fill="x", padx=14, pady=(16,3))

        def btn(label, icon, cmd):
            ctk.CTkButton(sb, text=f"  {icon}  {label}",
                          fg_color="transparent", hover_color="#21262D",
                          anchor="w", font=ctk.CTkFont("Segoe UI", 13),
                          text_color="white", height=36, border_width=0,
                          command=cmd, corner_radius=8
                          ).pack(fill="x", padx=8, pady=2)

        sec("📁  FILE")
        btn("Open Image",      "📂", self.open_image)
        btn("Save Image",      "💾", self.save_image)
        btn("Batch Process",   "📦", self.open_batch)
        btn("Reset to Original","♻️", self.reset_image)

        sec("✂️  BASIC OPERATIONS")
        btn("Resize",          "📐", self.dlg_resize)
        btn("Crop",            "✂️",  self.dlg_crop)
        btn("Rotate",          "🔃", self.dlg_rotate)
        btn("Flip",            "↔️",  self.dlg_flip)
        btn("Compress & Save", "🗜️",  self.dlg_compress)
        btn("Convert Format",  "🔄", self.dlg_convert)

        sec("🎨  FILTERS")
        btn("Grayscale",       "⬛", self.f_grayscale)
        btn("Blur",            "🌫️",  self.f_blur)
        btn("Sharpen",         "🔪", self.f_sharpen)
        btn("Edge Detect",     "📏", self.f_edge)
        btn("Sepia Tone",      "🎞️",  self.f_sepia)
        btn("Emboss",          "🏔️",  self.f_emboss)

        sec("🤖  AI FEATURES")
        btn("Remove Background","🪄", self.ai_rembg)
        btn("Face Detection",  "👤", self.ai_faces)
        btn("OCR – Extract Text","📝",self.ai_ocr)
        btn("Add Watermark",   "💧", self.dlg_watermark)
        btn("AI Auto-Enhance", "✨", self.ai_enhance)

    def _main_area(self):
        m = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=0)
        m.grid(row=0, column=1, sticky="nsew")
        m.grid_columnconfigure(0, weight=1)
        m.grid_rowconfigure(1, weight=1)

        # Top bar
        top = ctk.CTkFrame(m, height=52, fg_color=BG_CARD, corner_radius=0)
        top.grid(row=0, column=0, sticky="ew")
        top.grid_propagate(False)
        ctk.CTkLabel(top, text="Image Canvas",
                     font=ctk.CTkFont("Segoe UI", 14, "bold")).pack(side="left", padx=18, pady=14)
        self.info_lbl = ctk.CTkLabel(top, text="No image loaded",
                                      font=ctk.CTkFont("Segoe UI", 11),
                                      text_color="#8B949E")
        self.info_lbl.pack(side="left", padx=8)

        # Canvas
        cf = ctk.CTkFrame(m, fg_color=BG_CARD, corner_radius=10)
        cf.grid(row=1, column=0, sticky="nsew", padx=14, pady=14)
        cf.grid_columnconfigure(0, weight=1)
        cf.grid_rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(cf, bg="#0D1117", highlightthickness=0)
        self.canvas.grid(sticky="nsew", padx=2, pady=2)
        self.canvas.create_text(400, 280,
            text="📂  Click  'Open Image'  in the sidebar to begin",
            fill="#30363D", font=("Segoe UI", 16), tags="hint")

        # Sliders panel
        sp = ctk.CTkFrame(m, height=120, fg_color=BG_CARD, corner_radius=10)
        sp.grid(row=2, column=0, sticky="ew", padx=14, pady=(0,14))
        sp.grid_propagate(False)
        self._sliders(sp)

    def _sliders(self, parent):
        ctk.CTkLabel(parent, text="Quick Adjustments",
                     font=ctk.CTkFont("Segoe UI", 11, "bold"),
                     text_color="#8B949E").place(x=14, y=10)

        def make(label, color, x, attr):
            ctk.CTkLabel(parent, text=label, text_color="white",
                         font=ctk.CTkFont("Segoe UI", 11)).place(x=x, y=38)
            s = ctk.CTkSlider(parent, from_=0.1, to=3.0, number_of_steps=29,
                              width=155, progress_color=color)
            s.set(1.0)
            s.place(x=x+90, y=41)
            setattr(self, attr, s)

        make("Brightness", ACCENT,   14,  "sl_bright")
        make("Contrast",   WARNING,  290, "sl_contrast")
        make("Saturation", SUCCESS,  565, "sl_saturation")

        ctk.CTkButton(parent, text="Apply", width=100, fg_color=ACCENT,
                      command=self._apply_sliders).place(x=840, y=33)
        ctk.CTkButton(parent, text="Reset", width=80, fg_color="#21262D",
                      command=self._reset_sliders).place(x=950, y=33)

    def _statusbar(self):
        sb = ctk.CTkFrame(self, height=28, fg_color="#21262D", corner_radius=0)
        sb.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.status = ctk.CTkLabel(sb, text="✅  Ready",
                                    font=ctk.CTkFont("Segoe UI", 11),
                                    text_color="#8B949E")
        self.status.pack(side="left", padx=14)
        self.pbar = ctk.CTkProgressBar(sb, width=140, height=6)
        self.pbar.pack(side="right", padx=14, pady=10)
        self.pbar.set(0)

    #Helpers
    def setstatus(self, msg, color="#8B949E"):
        self.status.configure(text=msg, text_color=color)

    def setprog(self, v):
        self.pbar.set(v); self.update()

    def show(self, img):
        self.canvas.delete("all")
        self.canvas.update_idletasks()  # force canvas to compute real size first
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 10 or ch < 10:   # canvas not ready yet -> use safe fallback size
            cw, ch = 900, 550
        tmp = img.copy()
        tmp.thumbnail((cw - 20, ch - 20), Image.LANCZOS)
        self._tkimg = ImageTk.PhotoImage(tmp)
        self.canvas.create_image(cw // 2, ch // 2, image=self._tkimg, anchor="center")
        w, h = img.size
        self.info_lbl.configure(
            text=f"  {w} × {h} px  |  {img.mode}  |  {os.path.basename(self.image_path or 'unsaved')}")

    def need(self):
        if self.original_image is None:
            messagebox.showwarning("No Image", "Open an image first."); return False
        return True

    def work(self):
        return self.processed_image or self.original_image

    def _commit(self, img, msg):
        self.processed_image = img; self.show(img); self.setstatus(msg, SUCCESS)

    #File ops
    def open_image(self):
        p = filedialog.askopenfilename(
            filetypes=[("Images","*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp"),("All","*.*")])
        if not p: return
        self.image_path = p
        self.original_image = Image.open(p).convert("RGBA")
        self.processed_image = None
        self.after(50, lambda: self.show(self.original_image))
        self.setstatus(f"✅  Loaded: {os.path.basename(p)}", SUCCESS)

    def save_image(self):
        if not self.need(): return
        p = filedialog.asksaveasfilename(defaultextension=".png",
            filetypes=[("PNG","*.png"),("JPEG","*.jpg"),("BMP","*.bmp"),("WEBP","*.webp")])
        if p:
            img = self.work()
            (img.convert("RGB") if p.lower().endswith((".jpg",".jpeg")) else img).save(p)
            self.setstatus(f"💾  Saved: {os.path.basename(p)}", SUCCESS)

    def reset_image(self):
        if not self.need(): return
        self.processed_image = None; self.show(self.original_image)
        self._reset_sliders(); self.setstatus("♻️  Reset to original", WARNING)

    def open_batch(self):
        files = filedialog.askopenfilenames(
            filetypes=[("Images","*.png *.jpg *.jpeg *.bmp *.tiff")])
        if files: BatchWin(self, list(files))

    # ── Dialogs ───────────────────────────────────────────────────────────────
    def dlg_resize(self):
        if self.need(): ResizeDlg(self)

    def dlg_crop(self):
        if self.need(): CropDlg(self)

    def dlg_rotate(self):
        if self.need(): RotateDlg(self)

    def dlg_flip(self):
        if self.need(): FlipDlg(self)

    def dlg_compress(self):
        if self.need(): CompressDlg(self)

    def dlg_convert(self):
        if self.need(): ConvertDlg(self)

    def dlg_watermark(self):
        if self.need(): WatermarkDlg(self)

    #Filters 
    def f_grayscale(self):
        if not self.need(): return
        self._commit(self.work().convert("L").convert("RGBA"), "⬛  Grayscale applied")

    def f_blur(self):
        if not self.need(): return
        self._commit(self.work().filter(ImageFilter.GaussianBlur(3)), "🌫️  Blur applied")

    def f_sharpen(self):
        if not self.need(): return
        self._commit(self.work().filter(ImageFilter.SHARPEN), "🔪  Sharpen applied")

    def f_edge(self):
        if not self.need(): return
        img = self.work().convert("RGB").filter(ImageFilter.FIND_EDGES).convert("RGBA")
        self._commit(img, "📏  Edge detection applied")

    def f_sepia(self):
        if not self.need(): return
        a = np.array(self.work().convert("RGB"), dtype=np.float64)
        r = np.clip(a[:,:,0]*.393 + a[:,:,1]*.769 + a[:,:,2]*.189, 0, 255)
        g = np.clip(a[:,:,0]*.349 + a[:,:,1]*.686 + a[:,:,2]*.168, 0, 255)
        b = np.clip(a[:,:,0]*.272 + a[:,:,1]*.534 + a[:,:,2]*.131, 0, 255)
        img = Image.fromarray(np.stack([r,g,b],2).astype(np.uint8)).convert("RGBA")
        self._commit(img, "🎞️  Sepia applied")

    def f_emboss(self):
        if not self.need(): return
        self._commit(self.work().filter(ImageFilter.EMBOSS), "🏔️  Emboss applied")

    # ── Sliders ───────────────────────────────────────────────────────────────
    def _apply_sliders(self):
        if not self.need(): return
        img = self.original_image.convert("RGB")
        img = ImageEnhance.Brightness(img).enhance(self.sl_bright.get())
        img = ImageEnhance.Contrast(img).enhance(self.sl_contrast.get())
        img = ImageEnhance.Color(img).enhance(self.sl_saturation.get())
        self._commit(img.convert("RGBA"), "☀️  Adjustments applied")

    def _reset_sliders(self):
        self.sl_bright.set(1.0)
        self.sl_contrast.set(1.0)
        self.sl_saturation.set(1.0)

    # ── AI ────────────────────────────────────────────────────────────────────
    def ai_rembg(self):
        if not self.need(): return
        if not REMBG_OK:
            messagebox.showerror("Missing", "Install rembg:\npip install rembg"); return
        self.setstatus("🪄  Removing background…", WARNING); self.setprog(.3)
        def run():
            try:
                buf = io.BytesIO()
                self.original_image.save(buf, "PNG")
                out = rembg_remove(buf.getvalue())
                img = Image.open(io.BytesIO(out)).convert("RGBA")
                self.after(0, lambda: self._commit(img, "✅  Background removed!"))
                self.after(0, lambda: self.setprog(1))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=run, daemon=True).start()

    def ai_faces(self):
        if not self.need(): return
        cv = cv2.cvtColor(np.array(self.work().convert("RGB")), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv, cv2.COLOR_BGR2GRAY)
        cas = cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
        faces = cas.detectMultiScale(gray, 1.1, 4, minSize=(30,30))
        for x,y,w,h in faces:
            cv2.rectangle(cv,(x,y),(x+w,y+h),(0,255,120),3)
            cv2.putText(cv,"Face",(x,y-10),cv2.FONT_HERSHEY_SIMPLEX,.8,(0,255,120),2)
        img = Image.fromarray(cv2.cvtColor(cv, cv2.COLOR_BGR2RGB)).convert("RGBA")
        self._commit(img, f"👤  {len(faces)} face(s) detected")

    def ai_ocr(self):
        if not self.need(): return
        if not TESSERACT_OK:
            messagebox.showerror("Missing","Install pytesseract + Tesseract OCR"); return
        try:
            text = pytesseract.image_to_string(self.work().convert("RGB"))
            OCRWin(self, text)
            self.setstatus("📝  Text extracted", SUCCESS)
        except Exception as e:
            messagebox.showerror("OCR Error", str(e))

    def ai_enhance(self):
        if not self.need(): return
        img = self.work().convert("RGB")
        img = ImageEnhance.Sharpness(img).enhance(1.5)
        img = ImageEnhance.Contrast(img).enhance(1.2)
        img = ImageEnhance.Color(img).enhance(1.15)
        img = ImageEnhance.Brightness(img).enhance(1.05)
        self._commit(img.convert("RGBA"), "✨  AI Enhancement done!")


# ==============================================================================
#  Dialog classes
# ==============================================================================
class BaseDlg(ctk.CTkToplevel):
    def __init__(self, app, title, w=400, h=280):
        super().__init__(app)
        self.app = app
        self.title(title)
        self.geometry(f"{w}x{h}")
        self.resizable(False, False)
        self.grab_set()
        self.configure(fg_color=BG_CARD)
        ctk.CTkLabel(self, text=title,
                     font=ctk.CTkFont("Segoe UI",14,"bold"),
                     text_color=ACCENT).pack(pady=(18,8))

# ── Resize ────────────────────────────────────────────────────────────────────
class ResizeDlg(BaseDlg):
    def __init__(self, app):
        super().__init__(app, "📐  Resize Image", 400, 260)
        w, h = app.work().size
        ctk.CTkLabel(self, text=f"Current size: {w} × {h} px",
                     text_color="#8B949E").pack()
        f = ctk.CTkFrame(self, fg_color="transparent"); f.pack(pady=12)
        ctk.CTkLabel(f, text="Width:").grid(row=0,column=0,padx=8)
        self.ew = ctk.CTkEntry(f, width=90); self.ew.insert(0,str(w)); self.ew.grid(row=0,column=1,padx=4)
        ctk.CTkLabel(f, text="Height:").grid(row=0,column=2,padx=8)
        self.eh = ctk.CTkEntry(f, width=90); self.eh.insert(0,str(h)); self.eh.grid(row=0,column=3,padx=4)
        ctk.CTkButton(self, text="Apply Resize", fg_color=ACCENT, command=self._go).pack(pady=10)

    def _go(self):
        try:
            img = self.app.work().resize((int(self.ew.get()), int(self.eh.get())), Image.LANCZOS)
            self.app._commit(img, f"📐  Resized to {img.size}"); self.destroy()
        except: messagebox.showerror("Error","Enter valid numbers")

# ── Crop ──────────────────────────────────────────────────────────────────────
class CropDlg(BaseDlg):
    def __init__(self, app):
        super().__init__(app, "✂️  Crop Image", 420, 300)
        w, h = app.work().size
        ctk.CTkLabel(self, text=f"Image: {w} × {h} px", text_color="#8B949E").pack()
        f = ctk.CTkFrame(self, fg_color="transparent"); f.pack(pady=10)
        labels = ["Left (x1)","Top (y1)","Right (x2)","Bottom (y2)"]
        vals   = [0, 0, w, h]
        self.entries = []
        for i,(l,v) in enumerate(zip(labels,vals)):
            ctk.CTkLabel(f, text=l+":", width=90, anchor="e").grid(row=i//2,column=(i%2)*2,padx=6,pady=5)
            e = ctk.CTkEntry(f, width=90); e.insert(0,str(v)); e.grid(row=i//2,column=(i%2)*2+1,padx=4)
            self.entries.append(e)
        ctk.CTkButton(self, text="Apply Crop", fg_color=ACCENT, command=self._go).pack(pady=10)

    def _go(self):
        try:
            box = tuple(int(e.get()) for e in self.entries)
            img = self.app.work().crop(box)
            self.app._commit(img, f"✂️  Cropped to {img.size}"); self.destroy()
        except Exception as e: messagebox.showerror("Error", str(e))

# ── Rotate ────────────────────────────────────────────────────────────────────
class RotateDlg(BaseDlg):
    def __init__(self, app):
        super().__init__(app, "🔃  Rotate Image", 380, 240)
        self.sl = ctk.CTkSlider(self, from_=0, to=360, number_of_steps=360,
                                progress_color=ACCENT)
        self.sl.set(90); self.sl.pack(fill="x", padx=30, pady=8)
        self.lbl = ctk.CTkLabel(self, text="90°"); self.lbl.pack()
        self.sl.configure(command=lambda v: self.lbl.configure(text=f"{int(v)}°"))
        self.exp = ctk.CTkCheckBox(self, text="Expand canvas"); self.exp.pack(pady=6); self.exp.select()
        ctk.CTkButton(self, text="Apply Rotate", fg_color=ACCENT, command=self._go).pack(pady=8)

    def _go(self):
        img = self.app.work().rotate(-self.sl.get(), expand=bool(self.exp.get()))
        self.app._commit(img, f"🔃  Rotated {int(self.sl.get())}°"); self.destroy()

# ── Flip ──────────────────────────────────────────────────────────────────────
class FlipDlg(BaseDlg):
    def __init__(self, app):
        super().__init__(app, "↔️  Flip Image", 340, 190)
        ctk.CTkButton(self, text="↔️  Flip Horizontal", fg_color=ACCENT,
                      command=lambda: self._go(Image.FLIP_LEFT_RIGHT, "↔️")).pack(fill="x",padx=30,pady=8)
        ctk.CTkButton(self, text="↕️  Flip Vertical",   fg_color="#7B61FF",
                      command=lambda: self._go(Image.FLIP_TOP_BOTTOM, "↕️")).pack(fill="x",padx=30,pady=6)

    def _go(self, mode, icon):
        img = self.app.work().transpose(mode)
        self.app._commit(img, f"{icon}  Flip applied"); self.destroy()

# ── Compress ──────────────────────────────────────────────────────────────────
class CompressDlg(BaseDlg):
    def __init__(self, app):
        super().__init__(app, "🗜️  Compress Image", 380, 230)
        ctk.CTkLabel(self, text="JPEG Quality (lower = smaller file)",
                     text_color="#8B949E").pack()
        self.sl = ctk.CTkSlider(self, from_=10, to=95, number_of_steps=17,
                                progress_color=WARNING)
        self.sl.set(70); self.sl.pack(fill="x", padx=30, pady=8)
        self.lbl = ctk.CTkLabel(self, text="Quality: 70"); self.lbl.pack()
        self.sl.configure(command=lambda v: self.lbl.configure(text=f"Quality: {int(v)}"))
        ctk.CTkButton(self, text="Compress & Save", fg_color=WARNING,
                      text_color="black", command=self._go).pack(pady=12)

    def _go(self):
        p = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG","*.jpg")])
        if p:
            self.app.work().convert("RGB").save(p,"JPEG",quality=int(self.sl.get()),optimize=True)
            sz = os.path.getsize(p)//1024
            self.app.setstatus(f"🗜️  Saved {sz} KB", SUCCESS); self.destroy()

# ── Convert ───────────────────────────────────────────────────────────────────
class ConvertDlg(BaseDlg):
    def __init__(self, app):
        super().__init__(app, "🔄  Convert Format", 360, 220)
        ctk.CTkLabel(self, text="Choose output format:", text_color="#8B949E").pack()
        self.opt = ctk.CTkOptionMenu(self, values=["PNG","JPEG","BMP","WEBP","TIFF"])
        self.opt.pack(pady=10)
        ctk.CTkButton(self, text="Convert & Save", fg_color="#F77F00",
                      command=self._go).pack(pady=10)

    def _go(self):
        ext = self.opt.get().lower()
        p = filedialog.asksaveasfilename(defaultextension=f".{ext}",
                                         filetypes=[(self.opt.get(),f"*.{ext}")])
        if p:
            img = self.app.work()
            (img.convert("RGB") if ext in ("jpg","jpeg","bmp") else img).save(p)
            self.app.setstatus(f"🔄  Converted to {ext.upper()}", SUCCESS); self.destroy()

# ── Watermark ─────────────────────────────────────────────────────────────────
class WatermarkDlg(BaseDlg):
    def __init__(self, app):
        super().__init__(app, "💧  Add Watermark", 420, 290)
        ctk.CTkLabel(self, text="Watermark Text:", text_color="#8B949E").pack()
        self.txt = ctk.CTkEntry(self, width=300, placeholder_text="© Your Name 2024")
        self.txt.pack(pady=6)
        ctk.CTkLabel(self, text="Opacity:", text_color="#8B949E").pack()
        self.op = ctk.CTkSlider(self, from_=50, to=255, number_of_steps=41,
                                progress_color="#2980B9")
        self.op.set(128); self.op.pack(fill="x", padx=30, pady=6)
        self.pos = ctk.CTkOptionMenu(self, values=["Bottom Right","Center","Bottom Left","Top Right"])
        self.pos.pack(pady=6)
        ctk.CTkButton(self, text="Add Watermark", fg_color="#2980B9",
                      command=self._go).pack(pady=8)

    def _go(self):
        txt = self.txt.get() or "© Watermark"
        img = self.app.work().convert("RGBA")
        ov  = Image.new("RGBA", img.size, (0,0,0,0))
        dr  = ImageDraw.Draw(ov)
        try:    font = ImageFont.truetype("arial.ttf", max(img.width//20,20))
        except: font = ImageFont.load_default()
        bb = dr.textbbox((0,0), txt, font=font)
        tw, th = bb[2]-bb[0], bb[3]-bb[1]
        w, h   = img.size
        pmap = {"Bottom Right":(w-tw-20,h-th-20),"Center":(w//2-tw//2,h//2-th//2),
                "Bottom Left":(20,h-th-20),"Top Right":(w-tw-20,20)}
        x, y = pmap[self.pos.get()]
        dr.text((x,y), txt, fill=(255,255,255,int(self.op.get())), font=font)
        result = Image.alpha_composite(img, ov)
        self.app._commit(result, "💧  Watermark added"); self.destroy()

# ── OCR result window ─────────────────────────────────────────────────────────
class OCRWin(BaseDlg):
    def __init__(self, app, text):
        super().__init__(app, "📝  Extracted Text", 580, 440)
        box = ctk.CTkTextbox(self, width=540, height=300,
                              font=ctk.CTkFont("Courier New", 12))
        box.pack(pady=8, padx=16)
        box.insert("1.0", text or "(No text detected)")
        ctk.CTkButton(self, text="📋  Copy to Clipboard", fg_color=SUCCESS,
                      text_color="black",
                      command=lambda: (self.clipboard_clear(), self.clipboard_append(text),
                                       app.setstatus("📋  Copied!", SUCCESS))
                      ).pack(pady=8)

# ── Batch processing window ───────────────────────────────────────────────────
class BatchWin(BaseDlg):
    def __init__(self, app, files):
        super().__init__(app, "📦  Batch Processing", 580, 480)
        self.files = files
        ctk.CTkLabel(self, text=f"{len(files)} images selected",
                     text_color="#8B949E").pack()
        ctk.CTkLabel(self, text="Operation to apply to all images:",
                     text_color="white").pack(pady=4)
        self.op = ctk.CTkOptionMenu(self, values=[
            "Grayscale","Blur","Sharpen","Sepia","Rotate 90°","Resize 800×600"])
        self.op.pack(pady=4)
        self.pb = ctk.CTkProgressBar(self, width=400); self.pb.set(0); self.pb.pack(pady=8)
        self.log = ctk.CTkTextbox(self, width=520, height=200)
        self.log.pack(padx=14, pady=4)
        ctk.CTkButton(self, text="▶  Start Batch", fg_color=SUCCESS,
                      text_color="black", command=self._run).pack(pady=8)

    def _run(self):
        out = os.path.join(os.path.dirname(self.files[0]), "batch_output")
        os.makedirs(out, exist_ok=True)
        op = self.op.get()
        def go():
            for i, fp in enumerate(self.files):
                try:
                    img = Image.open(fp).convert("RGBA")
                    if   op == "Grayscale":     img = img.convert("L").convert("RGBA")
                    elif op == "Blur":          img = img.filter(ImageFilter.GaussianBlur(3))
                    elif op == "Sharpen":       img = img.filter(ImageFilter.SHARPEN)
                    elif op == "Rotate 90°":    img = img.rotate(-90, expand=True)
                    elif op == "Resize 800×600":img = img.resize((800,600),Image.LANCZOS)
                    elif op == "Sepia":
                        a = np.array(img.convert("RGB"), dtype=np.float64)
                        r = np.clip(a[:,:,0]*.393+a[:,:,1]*.769+a[:,:,2]*.189,0,255)
                        g = np.clip(a[:,:,0]*.349+a[:,:,1]*.686+a[:,:,2]*.168,0,255)
                        b = np.clip(a[:,:,0]*.272+a[:,:,1]*.534+a[:,:,2]*.131,0,255)
                        img = Image.fromarray(np.stack([r,g,b],2).astype(np.uint8)).convert("RGBA")
                    img.save(os.path.join(out, "batch_"+os.path.basename(fp)))
                    self.log.insert("end", f"✅  {os.path.basename(fp)}\n")
                    self.pb.set((i+1)/len(self.files)); self.update()
                except Exception as e:
                    self.log.insert("end", f"❌  {os.path.basename(fp)}: {e}\n")
            self.log.insert("end", f"\n🎉  Done! Files saved to:\n{out}\n")
        threading.Thread(target=go, daemon=True).start()


# ==============================================================================
if __name__ == "__main__":
    App().mainloop()
<<<<<<< HEAD
    
=======
>>>>>>> 6d9475d79d1f9c4466ee34c39edc2aec20548e84
