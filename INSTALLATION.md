## Installation
### 1. Clone the repository  

```bash
git clone https://github.com/dim-gggl/epic_events && cd epic_events
```

### 2. Set up and activate a virtual environment  
If using `uv`:
```bash
uv venv && source .venv/bin/activate
```

Using `venv`:
```bash
python3 -m venv .venv && source .venv/bin/activate      # on Linux/macOS
python3 -m venv .venv && .venv\Scripts\activate         # on Windows
```

### 3. Install the dependencies  

```bash
python -m pip install -U pip && python -m pip install -r requirements.txt
```

## Prerequisites

Before running the application, ensure you have the following prerequisites installed and configured:

### PostgreSQL Database

1. **Install PostgreSQL** (version 14 or higher)
   - **macOS**: `brew install postgresql@14`
   - **Ubuntu/Debian**: `sudo apt-get install postgresql postgresql-contrib`
   - **Windows**: Download from [postgresql.org](https://www.postgresql.org/download/windows/)

2. **Start PostgreSQL service**
   - **macOS**: `brew services start postgresql@14`
   - **Linux**: `sudo systemctl start postgresql`
   - **Windows**: Start the PostgreSQL service from Services or use pgAdmin

3. **Create a database and user**
   ```sql
   -- Connect to PostgreSQL as superuser
   sudo -u postgres psql
   
   -- Create database
   CREATE DATABASE epic_events_db;
   
   -- Create user (optional, you can use existing user)
   CREATE USER epic_user_app WITH PASSWORD 'your_password';
   
   -- Grant privileges
   GRANT ALL PRIVILEGES ON DATABASE epic_events_db TO epic_user_app;
   
   -- Exit
   \q
   ```

   ```bash
   psql -h 127.0.0.1 -p 5432 -U epic_user_app -d epic_events_db
   ```
   ```sql
   -- You need to create the schema for the database
   CREATE SCHEMA epic_events;

   -- Exit
   \q
   ```
   Now the database is ready to be used.

4. **Configure environment variables**
   Create a `.env` file in the project root with the following variables:
   ```env
   POSTGRES_USER=epic_user_app
   POSTGRES_PASSWORD=your_password
   POSTGRES_HOST=127.0.0.1
   POSTGRES_PORT=5432
   POSTGRES_DB=epic_events_db
   ```
   
   Alternatively, you can set the `DATABASE_URL` environment variable:
   ```env
   export DATABASE_URL=postgresql+psycopg2://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB
   echo "DATABASE_URL="$DATABASE_URL >> .env
   ```

### Python Environment
- Python 3.10, 3.11, 3.12, 3.13, or 3.14
- Virtual environment (recommended)