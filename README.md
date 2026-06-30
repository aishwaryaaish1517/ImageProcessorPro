# 🖼️ Image Processor Pro

A professional image processing application with Desktop GUI and Web Interface.

## ✨ Features
- Resize, Crop, Rotate, Flip images
- Apply Filters: Grayscale, Blur, Sharpen, Sepia, Edge, Emboss
- Convert image formats (PNG, JPG, WEBP, BMP, TIFF)
- Compress images
- Add Watermarks
- AI Background Removal
- Face Detection (OpenCV)
- OCR – Extract text from images (Tesseract)
- AI Auto-Enhancement
- Batch Processing (multiple images at once)
- Web Interface (Flask)



## 🚀 How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Run Desktop App
python app_gui.py

# Run Web App
python app_web.py
# Then open: http://localhost:5000
```


## 📁 Project Structure

```
ImageProcessorPro/
├── app_gui.py            ← Desktop GUI
├── app_web.py            ← Flask Web App
├── requirements.txt
├── README.md
├── .gitignore
├── templates/
│   └── index.html        ← Web UI page
├── static/
│   ├── css/
│   │   └── style.css     ← Web styles
│   └── js/
│       └── main.js       ← Web logic
├── uploads/              ← Auto-created
└── outputs/              ← Auto-created
```

---

## 🛠️ Tech Stack
- Python, Pillow, OpenCV, NumPy
- CustomTkinter (Desktop GUI)
- Flask (Web Interface)
- Tesseract OCR
- rembg (Background Removal)
## screenshot
![Screenshot](screenshot1.png)
![Screenshot](screenshot2.png)
![Screenshot](screenshot3.png)
![Screenshot](screenshot4.png)

