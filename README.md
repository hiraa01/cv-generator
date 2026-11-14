# CV Üretici / CV Generator

**[Türkçe](#türkçe) · [English](#english)**

---

## Türkçe

Kişisel bilgilerini ve deneyimlerini bir arayüze girerek Word (.docx) ve PDF formatında CV üretir. Türkçe ve İngilizce CV'leri aynı anda yönetebilirsin. Microsoft Word ve LibreOffice ile çalışır.

### Özellikler
- Masaüstü penceresi: formları doldur, bölümleri ekle, sırala, düzenle.
- Tek sütunlu, tablosuz, ATS'ye uygun A4 düzeni.
- E-posta, LinkedIn, GitHub ve sertifika linkleri tıklanabilir.
- Türkçe ve İngilizce için ayrı veri dosyaları.

### Hızlı başlangıç (uygulama)
1. Uygulamayı indir (veya kaynak koddan çalıştır, aşağıya bak).
2. `CVUretici.exe` dosyasını çalıştır.
3. Bilgilerini doldur. Her bölüme madde ya da başlık ekleyebilirsin.
4. **Kaydet**: `cv_tr.json` ve `cv_en.json` dosyalarına yazar.
5. **Word / PDF oluştur**: seçtiğin klasöre `Ad_Soyad_CV_TR.docx` ve `Ad_Soyad_CV_EN.docx` dosyalarını (ve PDF'leri) üretir.

PDF için LibreOffice (ücretsiz) ya da Windows'ta Microsoft Word gerekir.

### Kaynak koddan çalıştırma
```
pip install -r requirements.txt
python app.py
```
Python 3.9 veya üstü gerekir. Windows'ta kurulumda "Add Python to PATH" seçeneğini işaretle.

### İlana göre uyarlama
Başvurduğun ilanı yapıştır, uygulama ilandaki teknik terimleri CV'nle karşılaştırsın:
1. Pencerenin altındaki **İlana göre uyarla** düğmesine tıkla ve ilan metnini yapıştır.
2. **Analiz et** ile eşleşen ve eksik terimleri gör.
3. **Eşleşenleri öne çıkar** ile eşleşen beceriler başa alınır ve ilgili deneyim/proje maddeleri üste gelir.

Araç hiçbir beceriyi kendiliğinden eklemez. Eksik terimleri yalnızca gerçekten biliyorsan kendin ekle.

### Komut satırı kullanımı
Arayüz istemezsen JSON dosyalarından doğrudan üretebilirsin:
```
copy example_tr.json cv_tr.json
copy example_en.json cv_en.json
python build_cv.py cv_tr.json cv_en.json --pdf --out output
```

### Dosya yapısı
- `app.py`: masaüstü arayüzü
- `build_cv.py`: Word ve PDF üretimi
- `cv_model.py`: veri yardımcıları ve ilan eşleştirme
- `test_model.py`, `test_tailor.py`: testler
- `example_tr.json`, `example_en.json`: örnek veriler (uydurma)
- `cv_*.json`: kendi CV verilerin. Git tarafından yok sayılır, repoya girmez.

### Exe dosyası oluşturma (isteğe bağlı)
```
pip install pyinstaller
pyinstaller --onefile --windowed --name CVUretici app.py
```
Çıkan dosya `dist\CVUretici.exe` olur.

### Sorun giderme
- `ModuleNotFoundError: No module named 'docx'`: `pip install -r requirements.txt` çalıştır.
- PDF oluşmuyor: LibreOffice kurulu mu ve `soffice` komutu PATH'te mi kontrol et.
- Arayüz açılmıyor: Tkinter'ın Python ile geldiğinden emin ol (python.org kurulumu içerir).

### Lisans
MIT. Ayrıntılar için `LICENSE` dosyasına bak.

---

## English

Create a CV in Word (.docx) and PDF by filling in a desktop form. Turkish and English versions are managed together. Works with Microsoft Word and LibreOffice.

### Features
- Desktop window: fill in fields, add sections, reorder and edit items.
- Single-column, table-free, ATS-friendly A4 layout.
- Email, LinkedIn, GitHub and certificate links are clickable.
- Separate data files for Turkish and English.

### Quick start (app)
1. Download the app (or run from source, see below).
2. Run `CVUretici.exe`.
3. Fill in your details. Add items to any section.
4. **Save** writes `cv_tr.json` and `cv_en.json`.
5. **Word / PDF** creates `Name_Surname_CV_TR.docx` and `Name_Surname_CV_EN.docx` (and PDFs) in the folder you choose.

PDF needs LibreOffice (free) or Microsoft Word on Windows.

### Run from source
```
pip install -r requirements.txt
python app.py
```
Python 3.9 or later is required. On Windows, tick "Add Python to PATH" during setup.

### Tailoring to a job ad
Paste a job ad and compare it with your CV:
1. Click **İlana göre uyarla** (Tailor to job ad) at the bottom and paste the ad text.
2. **Analiz et** (Analyze) shows matched and missing terms.
3. **Eşleşenleri öne çıkar** (Highlight matches) moves matching skills to the front and brings related entries up.

The tool never adds skills by itself. Add missing terms only if you really have them.

### Command-line use
Without the app, generate directly from JSON:
```
copy example_tr.json cv_tr.json
copy example_en.json cv_en.json
python build_cv.py cv_tr.json cv_en.json --pdf --out output
```

### Project files
- `app.py`: desktop interface
- `build_cv.py`: Word and PDF generation
- `cv_model.py`: data helpers and job-ad matching
- `test_model.py`, `test_tailor.py`: tests
- `example_tr.json`, `example_en.json`: sample data (fictional)
- `cv_*.json`: your own CV data. Ignored by git, never committed.

### Build an .exe (optional)
```
pip install pyinstaller
pyinstaller --onefile --windowed --name CVUretici app.py
```
The result is `dist\CVUretici.exe`.

### Troubleshooting
- `ModuleNotFoundError: No module named 'docx'`: run `pip install -r requirements.txt`.
- No PDF: check that LibreOffice is installed and `soffice` is on your PATH.
- Window does not open: make sure Tkinter is available (the python.org installer includes it).

### License
MIT. See `LICENSE`.
