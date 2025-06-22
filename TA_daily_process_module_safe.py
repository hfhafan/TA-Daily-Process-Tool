import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import filedialog
import re
import os
from datetime import datetime
import warnings
import time
import multiprocessing as mp
import psutil
import pymysql
from sqlalchemy import create_engine, text
import urllib.parse

# Import DEFAULT_OUTPUT_PATH untuk output
try:
    from app_config import DEFAULT_OUTPUT_PATH
except ImportError:
    import os
    DEFAULT_OUTPUT_PATH = os.path.expanduser("~/Documents/tainitprocesstools/output/")

# Database configuration - UPDATE DENGAN KREDENSIAL ANDA
DB_CONFIG = {
    'host': 'your-database-host.com',
    'port': 3306,
    'user': 'your-username',
    'password': 'your-password',
    'database': 'your-database',
    'table': 'tainit_cell_day'
}

# Database admin configuration for DELETE operations
DB_ADMIN_CONFIG = {
    'host': 'your-database-host.com',
    'port': 3306,
    'user': 'your-admin-username',
    'password': 'your-admin-password',
    'database': 'your-database',
    'table': 'tainit_cell_day'
}

def format_duration(seconds):
    """Convert seconds to readable format (minutes and seconds)"""
    if seconds < 60:
        return f"{seconds:.1f} detik"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes} menit {remaining_seconds:.1f} detik"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        remaining_seconds = seconds % 60
        return f"{hours} jam {minutes} menit {remaining_seconds:.1f} detik"

def create_db_connection():
    """Create database connection using SQLAlchemy"""
    try:
        # URL encode password to handle special characters
        password_encoded = urllib.parse.quote_plus(DB_CONFIG['password'])
        
        # Create connection string for MariaDB
        connection_string = (
            f"mysql+pymysql://{DB_CONFIG['user']}:{password_encoded}@"
            f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
            f"?charset=utf8mb4"
        )
        
        # Create engine
        engine = create_engine(
            connection_string,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        try:
            print(f"[INFO] Koneksi database berhasil ke {DB_CONFIG['host']}")
        except (OSError, IOError):
            pass
            
        return engine
        
    except Exception as e:
        try:
            print(f"[ERROR] Gagal koneksi database: {str(e)}")
        except (OSError, IOError):
            pass
        return None

def create_admin_db_connection():
    """Create admin database connection for DELETE operations using SQLAlchemy"""
    try:
        # URL encode password to handle special characters
        password_encoded = urllib.parse.quote_plus(DB_ADMIN_CONFIG['password'])
        
        # Create connection string for MariaDB
        connection_string = (
            f"mysql+pymysql://{DB_ADMIN_CONFIG['user']}:{password_encoded}@"
            f"{DB_ADMIN_CONFIG['host']}:{DB_ADMIN_CONFIG['port']}/{DB_ADMIN_CONFIG['database']}"
            f"?charset=utf8mb4"
        )
        
        # Create engine
        engine = create_engine(
            connection_string,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        try:
            print(f"[INFO] Koneksi admin database berhasil ke {DB_ADMIN_CONFIG['host']}")
        except (OSError, IOError):
            pass
            
        return engine
        
    except Exception as e:
        try:
            print(f"[ERROR] Gagal koneksi admin database: {str(e)}")
        except (OSError, IOError):
            pass
        return None

def upload_to_database(df, engine):
    """Upload dataframe to database using INSERT ON DUPLICATE KEY UPDATE"""
    try:
        if df.empty:
            try:
                print("[WARNING] Tidak ada data untuk diupload")
            except (OSError, IOError):
                pass
            return False
            
        # Prepare data for upload
        df_upload = df.copy()
        
        # Convert data types
        df_upload['DateId'] = pd.to_datetime(df_upload['DateId']).dt.strftime('%Y-%m-%d')
        
        # Replace \N with None for NULL values
        df_upload = df_upload.replace('\\N', None)
        
        # Convert numeric columns
        numeric_cols = ['Distr50', 'Distr80', 'Distr90', 'Distr95', 'Distr100', 'TotSample']
        for col in numeric_cols:
            df_upload[col] = pd.to_numeric(df_upload[col], errors='coerce')
        
        try:
            print(f"[INFO] Memulai upload {len(df_upload)} baris ke database...")
        except (OSError, IOError):
            pass
        
        # Build INSERT ON DUPLICATE KEY UPDATE query
        table_name = DB_CONFIG['table']
        columns = df_upload.columns.tolist()
        
        # Create placeholders for values
        placeholders = ', '.join(['%s'] * len(columns))
        
        # Create column list for INSERT
        column_list = ', '.join([f"`{col}`" for col in columns])
        
        # Create UPDATE part for ON DUPLICATE KEY
        update_part = ', '.join([f"`{col}` = VALUES(`{col}`)" for col in columns if col not in ['DateId', 'Cell']])
        
        # Final query
        query = f"""
        INSERT INTO `{table_name}` ({column_list})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {update_part}
        """
        
        # Convert DataFrame to list of tuples
        data_tuples = [tuple(row) for row in df_upload.values]
        
        # Execute batch insert
        with engine.begin() as conn:
            # Use raw connection for batch insert
            raw_conn = conn.connection
            cursor = raw_conn.cursor()
            
            try:
                cursor.executemany(query, data_tuples)
                affected_rows = cursor.rowcount
                
                try:
                    print(f"[SUCCESS] Upload berhasil! {affected_rows} baris diproses")
                except (OSError, IOError):
                    pass
                    
                return True
                
            except Exception as e:
                try:
                    print(f"[ERROR] Gagal upload ke database: {str(e)}")
                except (OSError, IOError):
                    pass
                return False
            finally:
                cursor.close()
                
    except Exception as e:
        try:
            print(f"[ERROR] Error dalam upload_to_database: {str(e)}")
        except (OSError, IOError):
            pass
        return False

def get_sector(cellname):
    """
    Extract sector from cell name
    """
    try:
        # Ambil karakter terakhir dari nama cell
        if cellname and len(cellname) > 0:
            last_char = cellname[-1]
            if last_char.isdigit():
                return int(last_char)
            else:
                return 0
        return 0
    except:
        return 0

def get_band(neid, siteid):
    """
    Determine band based on NEID and SITEID
    """
    try:
        # Logic untuk menentukan band berdasarkan NEID dan SITEID
        if neid and siteid:
            # Implementasi logic khusus untuk menentukan band
            # Contoh sederhana - bisa disesuaikan dengan kebutuhan
            if '1800' in str(neid).upper() or '18' in str(siteid).upper():
                return '1800'
            elif '900' in str(neid).upper() or '9' in str(siteid).upper():
                return '900'
            elif '2100' in str(neid).upper() or '21' in str(siteid).upper():
                return '2100'
            else:
                return '1800'  # Default
        return '1800'
    except:
        return '1800'

def get_site_id(erbs_name):
    """
    Extract Site ID from ERBS name
    """
    try:
        if not erbs_name:
            return 'UNKNOWN'
        
        # Logic untuk extract Site ID dari nama ERBS
        # Contoh: dari "JKTXXX_1" extract "JKTXXX"
        site_id = str(erbs_name).split('_')[0] if '_' in str(erbs_name) else str(erbs_name)
        
        # Clean up site ID
        site_id = re.sub(r'[^A-Za-z0-9]', '', site_id)
        
        return site_id[:20] if site_id else 'UNKNOWN'
    except:
        return 'UNKNOWN'

def get_site_name(erbs_name, site_id):
    """
    Generate site name from ERBS name and Site ID
    """
    try:
        if not erbs_name:
            return 'UNKNOWN'
        
        # Logic untuk generate site name
        # Bisa disesuaikan dengan naming convention yang digunakan
        site_name = str(erbs_name).replace('_', ' ').title()
        
        # Limit length
        return site_name[:50] if site_name else 'UNKNOWN'
    except:
        return 'UNKNOWN'

def get_ne_id(cellname):
    """
    Extract NE ID from cell name
    """
    try:
        if not cellname:
            return 'UNKNOWN'
        
        # Logic untuk extract NE ID dari nama cell
        # Contoh: dari "JKTXXX_1A" extract "JKTXXX"
        ne_id = str(cellname).split('_')[0] if '_' in str(cellname) else str(cellname)[:-1]
        
        # Clean up NE ID
        ne_id = re.sub(r'[^A-Za-z0-9]', '', ne_id)
        
        return ne_id[:20] if ne_id else 'UNKNOWN'
    except:
        return 'UNKNOWN'

def calculate_percentiles_safe(row):
    """
    Calculate percentiles from TA distribution data safely
    """
    try:
        # Kolom distribusi TA
        distr_cols = [f'pmTaInit2Distr_{i:02d}' for i in range(35)]
        
        # Ambil data distribusi
        distr_data = []
        total_samples = 0
        
        for i, col in enumerate(distr_cols):
            if col in row:
                value = row[col]
                if pd.notna(value) and value != '\\N':
                    try:
                        count = int(float(value))
                        if count > 0:
                            distr_data.extend([i] * count)
                            total_samples += count
                    except:
                        continue
        
        if not distr_data or total_samples == 0:
            return {
                'Distr50': '\\N',
                'Distr80': '\\N', 
                'Distr90': '\\N',
                'Distr95': '\\N',
                'Distr100': '\\N',
                'TotSample': 0
            }
        
        # Calculate percentiles
        distr_array = np.array(distr_data)
        
        p50 = np.percentile(distr_array, 50)
        p80 = np.percentile(distr_array, 80)
        p90 = np.percentile(distr_array, 90)
        p95 = np.percentile(distr_array, 95)
        p100 = np.percentile(distr_array, 100)
        
        return {
            'Distr50': round(p50, 2),
            'Distr80': round(p80, 2),
            'Distr90': round(p90, 2),
            'Distr95': round(p95, 2),
            'Distr100': round(p100, 2),
            'TotSample': total_samples
        }
        
    except Exception as e:
        return {
            'Distr50': '\\N',
            'Distr80': '\\N',
            'Distr90': '\\N', 
            'Distr95': '\\N',
            'Distr100': '\\N',
            'TotSample': 0
        }

def process_ericsson_data(df):
    """
    Process Ericsson CSV data and calculate TA percentiles
    """
    try:
        print("[INFO] Memulai pemrosesan data Ericsson...")
        
        # Validasi kolom yang diperlukan
        required_cols = ['DATE_ID', 'ERBS', 'EUtranCellFDD']
        distr_cols = [f'pmTaInit2Distr_{i:02d}' for i in range(35)]
        
        missing_cols = []
        for col in required_cols:
            if col not in df.columns:
                missing_cols.append(col)
        
        if missing_cols:
            print(f"[ERROR] Kolom yang hilang: {missing_cols}")
            return None
        
        # Check distribution columns
        available_distr_cols = [col for col in distr_cols if col in df.columns]
        if len(available_distr_cols) < 10:  # Minimal 10 kolom distribusi
            print(f"[WARNING] Hanya {len(available_distr_cols)} kolom distribusi ditemukan")
        
        processed_data = []
        
        for idx, row in df.iterrows():
            try:
                # Calculate percentiles
                percentiles = calculate_percentiles_safe(row)
                
                # Extract site information
                erbs_name = str(row['ERBS'])
                cell_name = str(row['EUtranCellFDD'])
                site_id = get_site_id(erbs_name)
                site_name = get_site_name(erbs_name, site_id)
                sector = get_sector(cell_name)
                ne_id = get_ne_id(cell_name)
                band = get_band(ne_id, site_id)
                
                # Create processed row
                processed_row = {
                    'DateId': row['DATE_ID'],
                    'Cell': cell_name,
                    'SiteId': site_id,
                    'SiteName': site_name,
                    'Sector': sector,
                    'Band': band,
                    'NeId': ne_id,
                    'Distr50': percentiles['Distr50'],
                    'Distr80': percentiles['Distr80'],
                    'Distr90': percentiles['Distr90'],
                    'Distr95': percentiles['Distr95'],
                    'Distr100': percentiles['Distr100'],
                    'TotSample': percentiles['TotSample']
                }
                
                processed_data.append(processed_row)
                
            except Exception as e:
                print(f"[WARNING] Error processing row {idx}: {str(e)}")
                continue
        
        if not processed_data:
            print("[ERROR] Tidak ada data yang berhasil diproses")
            return None
        
        # Create DataFrame
        result_df = pd.DataFrame(processed_data)
        
        print(f"[SUCCESS] Berhasil memproses {len(result_df)} baris data")
        return result_df
        
    except Exception as e:
        print(f"[ERROR] Error dalam process_ericsson_data: {str(e)}")
        return None

def process_ta_data(input_path, upload_to_db=True, cancel_event=None):
    """
    Main function to process TA data with database upload
    """
    try:
        start_time = time.time()
        print("="*50)
        print("MEMULAI PEMROSESAN DATA TA")
        print("="*50)
        
        # Create output directory
        os.makedirs(DEFAULT_OUTPUT_PATH, exist_ok=True)
        
        # Determine if input is file or directory
        if os.path.isfile(input_path):
            csv_files = [input_path]
            print(f"[INFO] Memproses single file: {os.path.basename(input_path)}")
        else:
            csv_files = [os.path.join(input_path, f) for f in os.listdir(input_path) 
                        if f.lower().endswith('.csv')]
            print(f"[INFO] Memproses {len(csv_files)} file CSV dari folder")
        
        if not csv_files:
            print("[ERROR] Tidak ada file CSV ditemukan")
            return False
        
        # Database connection
        engine = None
        if upload_to_db:
            engine = create_db_connection()
            if engine is None:
                print("[ERROR] Gagal koneksi database, proses dibatalkan")
                return False
        
        all_processed_data = []
        
        # Process each file
        for file_path in csv_files:
            try:
                if cancel_event and cancel_event.is_set():
                    print("[INFO] Proses dibatalkan oleh user")
                    return False
                
                print(f"[INFO] Memproses file: {os.path.basename(file_path)}")
                
                # Read CSV
                df = pd.read_csv(file_path)
                print(f"[INFO] Membaca {len(df)} baris dari {os.path.basename(file_path)}")
                
                # Process data
                processed_df = process_ericsson_data(df)
                if processed_df is not None and not processed_df.empty:
                    all_processed_data.append(processed_df)
                    print(f"[SUCCESS] Berhasil memproses {len(processed_df)} baris")
                else:
                    print(f"[WARNING] Tidak ada data yang berhasil diproses dari {os.path.basename(file_path)}")
                
            except Exception as e:
                print(f"[ERROR] Error processing {os.path.basename(file_path)}: {str(e)}")
                continue
        
        if not all_processed_data:
            print("[ERROR] Tidak ada data yang berhasil diproses dari semua file")
            return False
        
        # Combine all data
        final_df = pd.concat(all_processed_data, ignore_index=True)
        print(f"[INFO] Total data yang diproses: {len(final_df)} baris")
        
        # Save to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(DEFAULT_OUTPUT_PATH, f"TA_processed_{timestamp}.csv")
        final_df.to_csv(output_file, index=False)
        print(f"[SUCCESS] Data disimpan ke: {output_file}")
        
        # Upload to database if requested
        if upload_to_db and engine is not None:
            print("[INFO] Memulai upload ke database...")
            upload_success = upload_to_database(final_df, engine)
            if upload_success:
                print("[SUCCESS] Upload database berhasil")
            else:
                print("[ERROR] Upload database gagal")
                return False
        
        end_time = time.time()
        duration = end_time - start_time
        print("="*50)
        print("PEMROSESAN SELESAI")
        print(f"Total waktu: {format_duration(duration)}")
        print(f"Data diproses: {len(final_df)} baris")
        print(f"Output file: {output_file}")
        if upload_to_db:
            print("Database: Upload berhasil")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error dalam process_ta_data: {str(e)}")
        return False

def process_ta_data_test(input_path, cancel_event=None):
    """
    Test mode processing - save to CSV only, no database upload
    """
    try:
        start_time = time.time()
        print("="*50)
        print("MEMULAI PEMROSESAN DATA TA - TEST MODE")
        print("="*50)
        
        # Create output directory
        os.makedirs(DEFAULT_OUTPUT_PATH, exist_ok=True)
        
        # Determine if input is file or directory
        if os.path.isfile(input_path):
            csv_files = [input_path]
            print(f"[INFO] Memproses single file: {os.path.basename(input_path)}")
        else:
            csv_files = [os.path.join(input_path, f) for f in os.listdir(input_path) 
                        if f.lower().endswith('.csv')]
            print(f"[INFO] Memproses {len(csv_files)} file CSV dari folder")
        
        if not csv_files:
            print("[ERROR] Tidak ada file CSV ditemukan")
            return False
        
        all_processed_data = []
        
        # Process each file
        for file_path in csv_files:
            try:
                if cancel_event and cancel_event.is_set():
                    print("[INFO] Proses dibatalkan oleh user")
                    return False
                
                print(f"[INFO] Memproses file: {os.path.basename(file_path)}")
                
                # Read CSV
                df = pd.read_csv(file_path)
                print(f"[INFO] Membaca {len(df)} baris dari {os.path.basename(file_path)}")
                
                # Process data
                processed_df = process_ericsson_data(df)
                if processed_df is not None and not processed_df.empty:
                    all_processed_data.append(processed_df)
                    print(f"[SUCCESS] Berhasil memproses {len(processed_df)} baris")
                else:
                    print(f"[WARNING] Tidak ada data yang berhasil diproses dari {os.path.basename(file_path)}")
                
            except Exception as e:
                print(f"[ERROR] Error processing {os.path.basename(file_path)}: {str(e)}")
                continue
        
        if not all_processed_data:
            print("[ERROR] Tidak ada data yang berhasil diproses dari semua file")
            return False
        
        # Combine all data
        final_df = pd.concat(all_processed_data, ignore_index=True)
        print(f"[INFO] Total data yang diproses: {len(final_df)} baris")
        
        # Save to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(DEFAULT_OUTPUT_PATH, f"TA_processed_TEST_{timestamp}.csv")
        final_df.to_csv(output_file, index=False)
        print(f"[SUCCESS] Data disimpan ke: {output_file}")
        
        end_time = time.time()
        duration = end_time - start_time
        print("="*50)
        print("PEMROSESAN SELESAI - TEST MODE")
        print(f"Total waktu: {format_duration(duration)}")
        print(f"Data diproses: {len(final_df)} baris")
        print(f"Output file: {output_file}")
        print("Database: Tidak diupload (Test Mode)")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error dalam process_ta_data_test: {str(e)}")
        return False 