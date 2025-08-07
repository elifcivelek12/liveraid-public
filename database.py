# database.py (Cloud için güncellenmiş hali)
"""
Database configuration and utilities for PostgreSQL using Cloud SQL Connector
"""
import os
import bcrypt
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from typing import Dict, Any, List, Optional

# Cloud SQL Python Connector kütüphanesini import ediyoruz
from google.cloud.sql.connector import Connector, IPTypes

# Global database instance
db = None

class DatabaseManager:
    def __init__(self):
        # Cloud SQL Connector'u başlat
        self.connector = Connector()
        
        # Ortam değişkenlerinden bağlantı bilgilerini al
        # BU DEĞİŞKENLERİ DAHA SONRA CLOUD RUN'A EKLEYECEĞİZ
        self.db_user = os.environ.get("DB_USER")
        self.db_pass = os.environ.get("DB_PASS")
        self.db_name = os.environ.get("DB_NAME")
        # Bu, Cloud SQL örneğinizin özel kimliğidir.
        self.instance_connection_name = os.environ.get("INSTANCE_CONNECTION_NAME")

        # ÖNEMLİ: Uygulama başlatıldığında veritabanı veya tablo oluşturma mantığını kaldırdık.
        # Bu işlemlerin zaten yapıldığını varsayıyoruz.
        print("✅ DatabaseManager initialized for Cloud SQL.")

    # get_connection fonksiyonunu connector kullanacak şekilde güncelliyoruz
    @contextmanager
    def get_connection(self):
        """Get database connection with context manager using Cloud SQL Connector"""
        conn = None
        try:
            # Connector.connect metodu güvenli bağlantıyı otomatik olarak yönetir
            conn = self.connector.connect(
                self.instance_connection_name,
                "pg8000", # psycopg2 ile uyumlu bir sürücü
                user=self.db_user,
                password=self.db_pass,
                db=self.db_name,
                ip_type=IPTypes.PUBLIC, # Genel IP üzerinden bağlanmasını söyle
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"❌ Database connection error: {e}")
            raise e
        finally:
            if conn:
                conn.close()
            # Connector'u uygulama kapanırken temizlemek gerekir. 
            # Cloud Run'da bu adımı atlayabiliriz, ancak iyi bir pratiktir.
            # self.connector.close() 

    # ----- GERİ KALAN TÜM FONKSİYONLAR (create_user, verify_user vb.) DEĞİŞMEDEN AYNI KALIYOR -----
    # init_tables, create_database_if_not_exists ve _add_missing_columns fonksiyonları SİLİNDİ.
    
    def create_user(self, email: str, password: str, first_name: str, last_name: str,
                   medical_field: str, organization: str, diploma_number: str, 
                   years_experience: int = 0, phone: str = "", doctor_title: str = "Dr.") -> Optional[int]:
        """Create a new user"""
        try:
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            name_surname = f"{first_name} {last_name}"
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (name_surname, email, password_hash, medical_field, organization, diploma_number, first_name, last_name, years_experience, phone, doctor_title)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (name_surname, email, password_hash, medical_field, organization, diploma_number, first_name, last_name, years_experience, phone, doctor_title))
                user_id = cursor.fetchone()['id']
                conn.commit()
                return user_id
        except psycopg2.IntegrityError:
            return None
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            return None
    
    def verify_user_credentials(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        return self.verify_user(email, password)
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, first_name, last_name, email, medical_field, organization, diploma_number, doctor_title FROM users WHERE email = %s AND is_active = TRUE", (email,))
                user = cursor.fetchone()
                return dict(user) if user else None
        except Exception as e:
            print(f"❌ Error getting user by email: {e}")
            return None
    
    def verify_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, first_name, last_name, email, password_hash, medical_field, organization, diploma_number, doctor_title FROM users WHERE email = %s AND is_active = TRUE", (email,))
                user = cursor.fetchone()
                if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                    user_data = dict(user)
                    del user_data['password_hash']
                    return user_data
                return None
        except Exception as e:
            print(f"❌ Error verifying user: {e}")
            return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, first_name, last_name, email, medical_field, organization, diploma_number, doctor_title FROM users WHERE id = %s AND is_active = TRUE", (user_id,))
                user = cursor.fetchone()
                return dict(user) if user else None
        except Exception as e:
            print(f"❌ Error getting user: {e}")
            return None

    def email_exists(self, email: str) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM users WHERE email = %s", (email,))
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"❌ Error checking email: {e}")
            return False
            
    def get_doctor_titles(self) -> List[str]:
        return ["Dr.", "Prof. Dr.", "Doç. Dr.", "Öğr. Gör. Dr.", "Uzm. Dr.", "Op. Dr.", "Dt.", "Vet.", "Ebe", "Hemşire"]

# Global database instance
db = DatabaseManager()