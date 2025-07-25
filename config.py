import os

# Local development (SQLite)
SQLITE_URI = "sqlite:///library.db"

# MySQL for production (example)
MYSQL_URI = "mysql+pymysql://username:password@host:3306/database_name"

# PostgreSQL for production (example)
POSTGRES_URI = "postgresql://username:password@host:5432/database_name"

# Select database automatically (default: SQLite)
DATABASE_URI = os.getenv("DATABASE_URL", SQLITE_URI)
