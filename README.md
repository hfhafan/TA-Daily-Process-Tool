# TA Daily Process Tool

Tool GUI untuk memproses data TA (Timing Advance) daily dari file CSV Ericsson dengan interface yang user-friendly.

## 🚀 Quick Start - Download Executable
**Download ready-to-use version**: [Download TA Daily Process Tool](http://bit.ly/3GanRLq)
- ✅ No Python installation required
- ✅ No dependencies setup needed  
- ✅ Ready to run executable (.exe)
- ✅ Includes Excel analysis tools

## 🚀 Features

- **GUI Interface**: Interface yang mudah digunakan dengan tkinter
- **File Processing**: Support untuk single file CSV atau multiple files dalam folder
- **Database Integration**: Upload otomatis ke database (MariaDB/MySQL)
- **Test Mode**: Mode testing tanpa upload database
- **Progress Monitoring**: Real-time log dan progress bar
- **Data Validation**: Validasi otomatis format data dan kolom required
- **Multi-threading**: Processing tidak memblokir GUI
- **Error Handling**: Comprehensive error handling dan logging

## 📋 Requirements

- Python 3.7+
- tkinter (biasanya sudah termasuk dalam Python)
- pandas
- numpy
- SQLAlchemy
- PyMySQL
- psutil

## 📦 Installation

### Quick Download (Executable)
🚀 **Download ready-to-use executable**: [Download TA Daily Process Tool](http://bit.ly/3GanRLq)
- Tidak perlu install Python atau dependencies
- Langsung jalankan file .exe
- Termasuk tools Excel untuk analisis TA

### Manual Installation (Source Code)

1. Clone repository ini:
```bash
git clone https://github.com/hfhafan/TA-Daily-Process-Tool.git
cd TA-Daily-Process-Tool
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. **Konfigurasi Database** (Diperlukan):
   - Edit file `TA_daily_process_module.py`
   - Update `DB_CONFIG` dan `DB_ADMIN_CONFIG` dengan kredensial database Anda
   - Pastikan tabel database sudah dibuat sesuai struktur yang diperlukan

4. **Setup Authentication** (Diperlukan):
   - File authentication modules tidak disertakan untuk keamanan
   - Anda perlu membuat module berikut:
     - `auth.py` - untuk validasi kredensial
     - `registry.py` - untuk menyimpan login info
     - `device_id.py` - untuk mendapatkan device ID
     - `spreadsheet.py` - untuk logging ke spreadsheet
   - Atau hapus bagian authentication di `ta_gui.py` jika tidak diperlukan

## 🏗️ Project Structure

```
TA-Daily-Process-Tool/
├── ta_gui.py                    # Main GUI application
├── TA_daily_process_module.py   # Core processing module
├── app_config.py               # Configuration settings
├── pack_to_exe_nuitka.bat      # Script untuk build executable
├── setup.iss                   # Inno Setup script
├── requirements.txt            # Python dependencies
├── excel/                      # Sample Excel tools
│   └── Tools TA Days Range HD v1.5 Juni25.xlsm
├── HFH.ico                     # Application icon
└── README.md                   # Documentation
```

## 🔧 Usage

### Option 1: Download Executable (Recommended)
1. Download dari: [TA Daily Process Tool Executable](http://bit.ly/3GanRLq)
2. Extract file yang didownload
3. Jalankan file `.exe` yang tersedia
4. Tidak perlu install Python atau dependencies

### Option 2: Run from Source Code

```bash
python ta_gui.py
```

### Input Data Format

File CSV harus memiliki kolom berikut:
- `DATE_ID`: Tanggal data (format: YYYY-MM-DD)
- `ERBS`: Nama eNodeB
- `EUtranCellFDD`: Nama cell
- `pmTaInit2Distr_00` sampai `pmTaInit2Distr_34`: Data distribusi TA

### Processing Options

1. **Single File**: Pilih satu file CSV
2. **Multiple Files**: Pilih folder berisi beberapa file CSV
3. **Database Upload**: Upload hasil ke database (centang checkbox)
4. **Test Mode**: Simpan hasil hanya ke CSV (uncheck database upload)

### Database Schema

Tabel `tainit_cell_day` dengan struktur:
```sql
CREATE TABLE tainit_cell_day (
    DateId DATE,
    Cell VARCHAR(255),
    SiteId VARCHAR(255),
    SiteName VARCHAR(255),
    Sector INT,
    Band VARCHAR(10),
    NeId VARCHAR(255),
    Distr50 DECIMAL(10,2),
    Distr80 DECIMAL(10,2),
    Distr90 DECIMAL(10,2),
    Distr95 DECIMAL(10,2),
    Distr100 DECIMAL(10,2),
    TotSample INT,
    PRIMARY KEY (DateId, Cell)
);
```

## 🛠️ Building Executable

Untuk membuat file executable (.exe):

1. Install Nuitka:
```bash
pip install nuitka
```

2. Run build script:
```bash
pack_to_exe_nuitka.bat
```

Atau gunakan Inno Setup dengan file `setup.iss` untuk membuat installer.

## ⚠️ Important Notes

1. **Database Configuration**: Update kredensial database di `TA_daily_process_module.py` sebelum digunakan
2. **Authentication Modules**: File authentication tidak disertakan untuk keamanan
3. **Dependencies**: Pastikan semua dependencies terinstall sebelum menjalankan
4. **File Permission**: Pastikan aplikasi memiliki permission untuk membaca/menulis file

## 🔒 Security

Repository ini tidak menyertakan:
- Kredensial database asli
- Module authentication dan login
- File konfigurasi sensitif

Hal ini dilakukan untuk menjaga keamanan sistem produksi.

## 📝 License

© 2025 - Hadi Fauzan Hanif

## 📧 Contact

**Author**: Hadi Fauzan Hanif  
**Email**: hadifauzanhanif@gmail.com  
**GitHub**: [hfhafan](https://github.com/hfhafan)

## 🐛 Known Issues

1. Authentication modules perlu dibuat sendiri
2. Database credentials perlu dikonfigurasi
3. Beberapa dependencies mungkin perlu versi spesifik

## 🔄 Changelog

### Version 1.0
- Initial release
- GUI interface dengan tkinter
- Support single/multiple file processing
- Database integration
- Real-time logging dan progress monitoring 