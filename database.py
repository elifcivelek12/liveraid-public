"""
Database configuration and utilities for PostgreSQL using Cloud SQL Connector
"""
import os
import bcrypt
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from typing import Dict, Any, List, Optional

from google.cloud.sql.connector import Connector, IPTypes


class DatabaseManager:
    def __init__(self):
        # Variables from the first code snippet
        self.db_user = os.environ.get('DB_USER')
        self.db_password = os.environ.get('DB_PASS')
        self.db_name = os.environ.get("DB_NAME")
        self.instance_connection_name = os.environ.get("CLOUD_SQL_CONNECTION_NAME")

        self.connector = Connector()

        
        # self.create_database_if_not_exists()
        self.init_tables()

        print("✅ DatabaseManager initialized for Cloud SQL.")

    # database.py dosyanızın içine eklenecek veya mevcut olanı değiştirecek

    @contextmanager
    def get_connection(self):
        """Get database connection with context manager using Cloud SQL Connector"""
        conn = None
        try:
            conn = self.connector.connect(
                self.instance_connection_name,
                "pg8000",
                user=self.db_user,
                password=self.db_password,
                db=self.db_name,
                ip_type=IPTypes.PRIVATE,
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
                
                
                
    def verify_database_connection(self):
        try:
       
            print(f"Attempting to verify connection to database '{self.db_name}'...")
        
            with self.get_connection() as conn:
                # Bağlantı başarılı olursa, basit bir sorgu çalıştırarak teyit et.
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            if result:
                print(f"✅ Successfully connected to database '{self.db_name}'. Connection is valid.")
                return True
            else:
                # Bu durumun gerçekleşmesi çok olası değil ama her ihtimale karşı.
                print(f"⚠️  Connected to '{self.db_name}', but test query failed.")
                return False

        except Exception as e:
            # get_connection içinde zaten bir hata loglaması var, ama burada daha spesifik bir mesaj verelim.
            print(f"❌ FAILED to connect to database '{self.db_name}'.")
            print("Please check the following:")
            print("1. The database name in your environment variables is correct.")
            print("2. The Cloud SQL instance is running.")
            print("3. The service account has the 'Cloud SQL Client' role in IAM.")
            print("4. The Cloud SQL Connection Name is correct.")
            print(f"Underlying error: {e}")
            return False
                
    
    def init_tables(self):
        """Initialize database tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Create users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        name_surname VARCHAR(255) NOT NULL,
                        first_name VARCHAR(255) NOT NULL,
                        last_name VARCHAR(255) NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        medical_field VARCHAR(255) NOT NULL,
                        organization VARCHAR(255) NOT NULL,
                        diploma_number VARCHAR(255) NOT NULL,
                        years_experience INTEGER DEFAULT 0,
                        phone VARCHAR(50) DEFAULT '',
                        doctor_title VARCHAR(100) DEFAULT 'Dr.',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                """)

                # Add missing columns if they don't exist
                self._add_missing_columns(cursor)

                # Create user_sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        session_data JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Create index on email for faster lookups
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")

                conn.commit()
                print("✅ Database tables initialized successfully")

        except Exception as e:
            print(f"❌ Error initializing tables: {e}")
            
    

    '''
    def _add_missing_columns(self, cursor):
        """Add missing columns to the users table for backward compatibility."""
        try:
            # List of columns to check and their definitions
            columns_to_add = {
                'first_name': "VARCHAR(255) DEFAULT ''",
                'last_name': "VARCHAR(255) DEFAULT ''",
                'years_experience': "INTEGER DEFAULT 0",
                'phone': "VARCHAR(50) DEFAULT ''",
                'doctor_title': "VARCHAR(100) DEFAULT 'Dr.'"
            }

            for col, definition in columns_to_add.items():
                cursor.execute("""
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='users' AND column_name=%s
                """, (col,))
                if not cursor.fetchone():
                    print(f"Adding column '{col}' to 'users' table...")
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
                    print(f"✅ Column '{col}' added.")

            # Logic to populate first_name and last_name from name_surname for old records
            cursor.execute("""
                UPDATE users
                SET first_name = SPLIT_PART(name_surname, ' ', 1),
                    last_name = CASE
                        WHEN ARRAY_LENGTH(STRING_TO_ARRAY(name_surname, ' '), 1) > 1
                        THEN SUBSTRING(name_surname FROM POSITION(' ' IN name_surname) + 1)
                        ELSE ''
                    END
                WHERE (first_name IS NULL OR first_name = '') AND name_surname IS NOT NULL AND name_surname != ''
            """)
            # Set NOT NULL constraint after populating
            cursor.execute("ALTER TABLE users ALTER COLUMN first_name SET NOT NULL")
            cursor.execute("ALTER TABLE users ALTER COLUMN last_name SET NOT NULL")

        except Exception as e:
            print(f"❌ Error adding missing columns: {e}")
            # Rollback is handled by the main context manager, but we raise to signal failure
            raise e
    '''


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
            # This error is raised when a unique constraint (like email) is violated
            return None
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            return None

    def verify_user_credentials(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify user credentials and return user data if valid."""
        return self.verify_user(email, password)

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user details by their email address."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, first_name, last_name, email, medical_field, organization, diploma_number, doctor_title
                    FROM users
                    WHERE email = %s AND is_active = TRUE
                """, (email,))
                user = cursor.fetchone()
                return dict(user) if user else None
        except Exception as e:
            print(f"❌ Error getting user by email: {e}")
            return None

    def verify_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify a user's email and password."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, first_name, last_name, email, password_hash, medical_field, organization, diploma_number, doctor_title
                    FROM users
                    WHERE email = %s AND is_active = TRUE
                """, (email,))
                user = cursor.fetchone()
                if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                    user_data = dict(user)
                    del user_data['password_hash']  # Do not send the hash to the client
                    return user_data
                return None
        except Exception as e:
            print(f"❌ Error verifying user: {e}")
            return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user details by their user ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, first_name, last_name, email, medical_field, organization, diploma_number, doctor_title
                    FROM users
                    WHERE id = %s AND is_active = TRUE
                """, (user_id,))
                user = cursor.fetchone()
                return dict(user) if user else None
        except Exception as e:
            print(f"❌ Error getting user by ID: {e}")
            return None

    def email_exists(self, email: str) -> bool:
        """Check if an email already exists in the database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM users WHERE email = %s", (email,))
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"❌ Error checking for email existence: {e}")
            return False

    def get_doctor_titles(self) -> List[str]:
        """Returns a static list of predefined doctor titles."""
        return [
            "Dr.", "Prof. Dr.", "Doç. Dr.", "Öğr. Gör. Dr.", "Uzm. Dr.",
            "Op. Dr.", "Dt.", "Vet.", "Ebe", "Hemşire"
        ]

# Global database instance
db = DatabaseManager()