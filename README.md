[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv) [![Static Badge](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13%20|%203.14-%233775A9?style=plastic&logo=python&logoColor=%23FFE569)](https://www.python.org/) ![Static Badge](https://img.shields.io/badge/SQLAlchemy-2.0.83-%23a11b18?logo=SQLAlchemy&logoColor=white)
![Static Badge](https://img.shields.io/badge/PostgreSQL-14.19-%23336690?style=plastic&logo=PostgreSQL&logoColor=white)
![Static Badge](https://img.shields.io/badge/PyJWT-2.10.1-%232980b9?style=plastic&logo=JWT&logoColor=%232980b9) ![Static Badge](https://img.shields.io/badge/Rich-3.8.0-%236ab0de?style=plastic&logo=Rich&logoColor=white) ![Static Badge](https://img.shields.io/badge/sentry--sdk-2.35.1-%23be5db9?style=plastic&logo=Sentry&logoColor=white)


|&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;|
|---|:-:|---|
|![](./media/epic_events.png)

C.R.M. For event planner company EPIC EVENTS.

## Installation
### 1. Cloning the repo  

```bash
git clone https://github.com/dim-gggl/epic_events && cd epic_events
```

### 2. Set and activate a virtual environment  
If using `uv`:
```bash
uv venv && source .venv/bin/activate
```

using `virtualenv`:
```bash
python3 -m venv .venv && source .venv/bin/activate # On Linux/macOS
python3 -m venv .venv && .venv\Scripts\activate # on Windows
```

### 3. Installing the dependancies  

```bash
python -m pip install -U pip && python -m pip install -r requirements.txt
```

## Usage  

if you try this:
```bash
python epic_events.py --help
```
This is what you should see :
![](media/help_menu.svg)

At this point, for more convenience, it's recommanded to :

```bash
alias epic-events="python epic_events.py"
```

This way it is possible to 

```bash
epic-events help
```

### The Commands

#### `init-db`

This is the first commande that should be launch after the installation. It initialises the database and sets up the necessary data required by the app to start running (it initiales the roles id permetting to create users and starting provifing them a role)

#### `init-manager`

This command can only be ran with root privileges (`sudo` on unix systems). It allows to create a user with the role of management, so, typically a user with the permission of creating other user profiles.

USAGE : 
```bash
sudo epic-events init-manager -u [USERNAME] -m [FULL_NAME] -e [EMAIL]
```
`sudo` will ask you for your root password, then epic-events should ask for the password of the manager user that is currently creating.

#### `create-user`

This command requires to be connected to the CRM and to be a manager user. In order to make it work, it should receive as an argument an access token proving the role of the request user.

USAGE : 
```bash
epic-events create-user -t [ACCESS_TOKEN] -u [USERNAME] -n [FULL_NAME] -e [EMAIL] -r [ROLE_ID]
```