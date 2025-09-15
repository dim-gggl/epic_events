## Prerequisites

Before running the application, ensure you have the following prerequisites installed and configured:

### PostgreSQL Database

1. **Install PostgreSQL** (version 14 or higher)  

   - **macOS**: `brew install postgresql`
   - **Ubuntu/Debian**: `sudo apt-get install postgresql postgresql-contrib`
   - **Windows**: Download from [postgresql.org](https://www.postgresql.org/download/windows/)

2. **Start PostgreSQL service**  

   - **macOS**: `brew services start postgresql@14`
   - **Linux**: `sudo systemctl start postgresql`
   - **Windows**: Start the PostgreSQL service from Services or use pgAdmin

3. **Create a database and user**
```sql
-- Connect to PostgreSQL as superuser
sudo psql -d postgres

-- Create the owner role of the database
CREATE ROLE epic_events_owner NOLOGIN;

-- Create Database
CREATE DATABASE epic_events_db 
OWNER epic_events_owner;

-- Connection to the new database
\c epic_events_db

-- Revoke rights to create in public mode
REVOKE CREATE 
ON SCHEMA public 
FROM PUBLIC;

GRANT USAGE 
ON SCHEMA public 
TO PUBLIC;

-- Create a schema for the app
CREATE SCHEMA epic_events 
AUTHORIZATION epic_events_owner;

ALTER ROLE epic_events_owner 
SET search_path 
TO epic_events, public;

-- Grant privileges
GRANT ALL PRIVILEGES 
ON DATABASE epic_events_db 
TO epic_user_owner;

-- Exit
\q
```
```bash
psql -h 127.0.0.1 -p 5432 -U epic_user_owner -d epic_events_db
```

```sql
-- Create the user
CREATE ROLE epic_events_app
LOGIN 
PASSWORD '<the-common-password>'
NOSUPERUSER NOCREATEDB 
NOCREATEROLE NOREPLICATION;

-- Give access and rights on the schema
GRANT USAGE 
ON SCHEMA epic_events 
TO epic_events_app;

GRANT SELECT, 
INSERT, UPDATE, 
DELETE ON ALL TABLES 
IN SCHEMA epic_events 
TO epic_events_app;

ALTER DEFAULT PRIVILEGES
FOR ROLE epic_events_owner 
IN SCHEMA epic_events
GRANT SELECT, 
INSERT, UPDATE, 
DELETE ON TABLES 
TO epic_events_app;

-- Limit the db access to the app users
REVOKE CONNECT 
ON DATABASE epic_events_db 
FROM PUBLIC;

GRANT CONNECT 
ON DATABASE epic_events_db
TO epic_events_app, 
epic_events_owner;
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

## Installation

### 1. Clonez le dépôt et placez-vous à la racine du projet  

```bash
git clone https://github.com/dim-gggl/epic_events && cd epic_events
```

### 2. Créez et activez un environnement Python, puis installez le projet et ses dépendances:

- Si vous utilisez `uv` (**recommandé**) :
```bash
uv sync

# or uv venv && source .venv/bin/activate && uv pip install -e .
```

- Sinon :
```bash
python3 -m venv .venv 
source .venv/bin/activate  # On Linux/macOS
.venv\Scripts\activate     # On Windows
```



### Python Environment
- Python 3.10, 3.11, 3.12, 3.13, or 3.14
- Virtual environment (recommended)

## Everything is ready to continue to the [Quick Start guide](./README.md#demarrage-rapide)