[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv) [![Static Badge](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13%20|%203.14-%233775A9?style=plastic&logo=python&logoColor=%23FFE569)](https://www.python.org/) [![Static Badge](https://img.shields.io/badge/SQLAlchemy-2.0.83-%23a11b18?logo=SQLAlchemy&logoColor=white)](https://www.sqlalchemy.org/) ![Static Badge](https://img.shields.io/badge/PostgreSQL-14.19-%23336690?style=plastic&logo=PostgreSQL&logoColor=white) ![Static Badge](https://img.shields.io/badge/PyJWT-2.10.1-%232980b9?style=plastic&logo=JWT&logoColor=%232980b9) ![Static Badge](https://img.shields.io/badge/Rich-3.8.0-%236ab0de?style=plastic&logo=Rich&logoColor=white) ![Static Badge](https://img.shields.io/badge/sentry--sdk-2.35.1-%23be5db9?style=plastic&logo=Sentry&logoColor=white)


![](./media/epic_events.png)

# Epic Events CRM

A comprehensive Customer Relationship Management (CRM) system built with Python, featuring user authentication, role-based permissions, and a rich command-line interface.

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

Using `virtualenv`:
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
   ```

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

## Usage  

If you try this:
```bash
python epic_events.py --help
```
This is what you should see:
![](media/help_menu.svg)

At this point, for more convenience, it is recommended to:

```bash
alias epic-events="python epic_events.py"
```

This way, it is possible to 

```bash
epic-events help
```

## Commands

#### `init-db`

This is the first command that should be launched after installation. It initializes the database and sets up the necessary data required by the app to start running (it initializes the role IDs, allowing you to create users and start providing them with roles).

#### `init-manager`

This command can only be run with root privileges (`sudo` on Unix systems). It allows you to create a user with the management role, typically a user with the permission to create other user profiles.

**Usage:** 
```bash
sudo epic-events init-manager -u [USERNAME] -n [FULL_NAME] -e [EMAIL]
```
`sudo` will ask you for your root password, then epic-events will ask for the password of the manager user that is being created.

#### `create-user`

This command requires you to be connected to the CRM and to be a manager user. In order to make it work, it should receive as an argument an access token proving the role of the requesting user.

**Usage:** 
```bash
epic-events create-user -t [ACCESS_TOKEN] -u [USERNAME] -n [FULL_NAME] -e [EMAIL] -r [ROLE_ID]
```

#### `login`

Authenticate a user and obtain an access token.

**Usage:**
You can provide your username as an argument or be prompted for it.
```bash
epic-events login -u [USERNAME]
```

#### `create-client`

Create a new client. This command requires a commercial user token, otherwise it will display an error message.
The access token is mandatory.

The other arguments are optional. If they are not provided, the user will be prompted to enter them.

**Usage:**
```bash
epic-events create-client -t [ACCESS_TOKEN] -n [FULL_NAME] -e [EMAIL] -p [PHONE] -c [COMPANY_ID] -d [FIRST_CONTACT_DATE]
```

#### `list-clients`

List all clients or, optionally, only the clients assigned to the current commercial user. 
This command is available for all users in readonly, requiring at least to be logged in.
access token required but no role check is performed.
However, if the user is a commercial user, the command can be filtered to only list the clients assigned to the current commercial user.

**Usage:**
```bash
epic-events list-clients -t [ACCESS_TOKEN] -f [FILTERED]
```