<a id="installation"></a>
# 🇫🇷 Installation du CRM Epic Events

Ce guide détaille les étapes pour installer et configurer l'application CRM Epic Events en local.

## 1. Prérequis

Avant de commencer, assurez-vous d'avoir les éléments suivants installés sur votre machine :

- **Python** (version 3.9 ou supérieure)
- **uv**: Un gestionnaire de paquets et d'environnements virtuels Python rapide. Si vous ne l'avez pas, installez-le avec pip :
  ```bash
  pip install uv
  ```
- **PostgreSQL**: Un serveur de base de données PostgreSQL fonctionnel.

## 2. Clonage du Dépôt

Clonez le projet depuis son dépôt Git :

```bash
git clone https://github.com/dim-gggl/epic_events.git
cd epic_events
```

## 3. Configuration de l'Environnement Python

Nous utilisons `uv` pour créer un environnement virtuel isolé et installer les dépendances.

1.  **Créer l'environnement virtuel** :
```bash
uv venv
```
Cette commande crée un dossier `.venv` dans le projet.

2.  **Activer l'environnement** :
    
- Sur macOS/Linux :
```bash
source .venv/bin/activate
```  

- Sur Windows :  

```bash
.venv\Scripts\activate
```

3.  **Installer les dépendances** :
Utilisez `uv` pour installer les dépendances listées dans `pyproject.toml` :
```bash
uv pip install -e .
```
L'option `-e` installe le projet en mode "éditable", ce qui est recommandé pour le développement.

## 4. Configuration de la Base de Données

1.  **Créez un utilisateur et une base de données** dans PostgreSQL. 

Par exemple, en utilisant `psql` :


```bash
psql -d postgres
```

```sql
-- Commencer par créer l'utilisateur de la base, sans privilège ni
-- permission particulière.
CREATE ROLE epic_events_app 
LOGIN PASSWORD 'votre_mot_de_passe_securise' -- https://dim-gggl.github.io/ClinKey/
NOSUPERUSER NOCREATEDB 
NOCREATEROLE NOREPLICATION;

-- Ensuite, créer la base de données, 
-- et l'assigner à l'utilisateur.
CREATE DATABASE epic_events_db 
OWNER epic_events_app;

-- Quitter psql
\q -- quit psql
```  

Connectez-vous à la base de données avec l'utilisateur créé :  

```bash
psql -d epic_events_db -U epic_events_app
```

```sql
-- Restreignez la lecture et l'écriture sur
-- le schéma public à l'utilisateur epic_events_app
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO PUBLIC;

-- Créez un nouveau schéma nommé epic_events
-- et l'assignez à l'utilisateur epic_events_app
CREATE SCHEMA epic_events 
AUTHORIZATION epic_events_app;

-- Définissez le chemin de recherche pour l'utilisateur 
-- epic_events_app à epic_events, public
ALTER ROLE epic_events_app 
SET search_path TO epic_events, public;

-- Grant all privileges on the epic_events_db 
-- database to the epic_events_app user
GRANT ALL PRIVILEGES 
ON DATABASE epic_events_db 
TO epic_events_app;
```

2.  **Configurez les variables d'environnement** :  

- Copiez le fichier d'exemple :  

```bash
cp .env.example .env
```
- Ouvrez le fichier `.env` et modifiez les valeurs pour correspondre à votre configuration PostgreSQL. Assurez-vous également de définir une `SECRET_KEY` forte pour la sécurité des jetons JWT.

```ini
# .env
POSTGRES_USER="epic_events_app"
POSTGRES_PASSWORD="votre_mot_de_passe_securise"
POSTGRES_HOST="127.0.0.1"
POSTGRES_PORT=5432
POSTGRES_DB="epic_events_db"

DATABASE_URL="postgresql+psycopg://"$POSTGRES_USER":"$POSTGRES_PASSWORD"@"$POSTGRES_HOST":"$POSTGRES_PORT"/"$POSTGRES_DB

# Clé secrète pour les jetons JWT (utilisez une chaîne aléatoire et complexe)
SECRET_KEY="remplacer_par_une_cle_secrete_forte"

# Optionnel : DSN pour l'intégration Sentry
SENTRY_DSN=""
```
> **Astuce** Vous pouvez générer la `SECRET_KEY` sur [ClinKey](https://dim-gggl.github.io/ClinKey/)
> ou la version en ligne de commande :
```bash
pip install clinkey-cli
export SECRET_KEY=$(clinkey -l 128 -t strong -n 1)
echo 'SECRET_KEY=$SECRET_KEY' >> .env
```

## 5. Initialisation de l'Application

1. **Créer les tables de la base de données** :
Cette commande initialise le schéma de la base de données et insère les rôles et permissions par défaut.
```bash
uv run epic_events.py db-create
# or
# python epic_events.py db-create
```

2. **Créer le premier utilisateur (Manager)** :
Pour administrer l'application, vous devez créer un utilisateur avec le rôle "Management". Cette opération nécessite des privilèges élevés car elle crée le premier administrateur.

- Sur macOS/Linux :
```bash
sudo python epic_events.py manager-create
```

- Sur Windows, lancez votre terminal en tant qu'administrateur avant d'exécuter :
```bash
sudo python epic_events.py manager-create
# ou uv run epic_events.py manager-create
```
Suivez les instructions pour définir le nom d'utilisateur, 
le nom complet et l'email. Le mot de passe vous sera demandé de manière sécurisée.

## 6. Lancement de l'Application

Vous êtes prêt ! Pour commencer à utiliser l'application, connectez-vous avec l'utilisateur que vous venez de créer.

```bash
epev login
```

Pour voir toutes les commandes disponibles, utilisez l'aide intégrée :

```bash
epev help
```
  
--- 
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
&nbsp;
&nbsp;
&nbsp;
&nbsp;
&nbsp;
&nbsp;
&nbsp;
&nbsp;
&nbsp;
  
  &nbsp;
    
  &nbsp;  
  &nbsp;  
  &nbsp;  
  &nbsp;  
  &nbsp;  
  &nbsp;  

<a id="setup"></a>
# 🇬🇧 Installing the Epic Events CRM

This guide details the steps to install and configure the Epic Events CRM application locally.

1. Prerequisites
Before you begin, make sure you have the following installed on your machine:Python (version 3.9 or higher)uv: A fast Python package and virtual environment manager.  

If you don't have it, install it with pip:  
```bash
pip install uv -e .
```

`PostgreSQL`: A running PostgreSQL database server.

2. Cloning the Repository
Clone the project from its Git repository:
```bash
git clone [https://github.com/dim-gggl/epic_events.git](https://github.com/dim-gggl/epic_events.git)
```  

A running PostgreSQL database server.

2. Cloning the Repository
Clone the project from its Git repository:

```bash
git clone [https://github.com/dim-gggl/epic_events.git](https://github.com/dim-gggl/epic_events.git)
cd epic_events
```

3. Python Environment Setup  

We use uv to create an isolated virtual environment and install dependencies.Create the virtual environment:
```bash
This com```
This command creates a .venv folder in the project.Activate the environment:

- On macOS/Linux:
```bash
source .venv/bin/activate

On Windows:
```bash
.venv\Scripts\activate
````


Install dependencies:Use uv to install the dependencies listed in pyproject.toml:uv pip install -e .The -e option installs the project in "editable" mode, which is recommended for development.4. Database ConfigurationCreate a user and a database in PostgreSQL.For example, using psql:

```bash
psql -d postgres
```
```sql
-- Start by creating the database user, without any special privileges
-- or permissions.
CREATE ROLE epic_events_app 
LOGIN PASSWORD 'your_secure_password' -- [https://dim-gggl.github.io/ClinKey/](https://dim-gggl.github.io/ClinKey/)
NOSUPERUSER NOCREATEDB 
NOCREATEROLE NOREPLICATION;

-- Then, create the database, 
-- and assign it to the user.
CREATE DATABASE epic_events_db 
OWNER epic_events_app;

-- Exit psql
\q -- quit psql
Connect to the database with the created user:psql -d epic_events_db -U epic_events_app
-- Restrict read and write on the public schema
-- to the epic_events_app user
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO PUBLIC;
```
```sql

-- Create a new schema named epic_events
-- and assign it to the epic_events_app user
CREATE SCHEMA epic_events 
AUTHORIZATION epic_events_app;

-- Set the search path for the epic_events_app user
-- to epic_events, public
ALTER ROLE epic_events_app 
SET search_path TO epic_events, public;

-- Grant all privileges on the epic_events_db 
-- database to the epic_events_app user
GRANT ALL PRIVILEGES 
ON DATABASE epic_events_db 
TO epic_events_app;
````

Configure environment variables:

Copy the example file:

```bash
cp .env.example .env
```
Open the .env file and modify the values to match your PostgreSQL configuration. 
Also, make sure to set a strong SECRET_KEY for JWT token security.
```bash
# .env
POSTGRES_USER="epic_events_app"
POSTGRES_PASSWORD="your_secure_password"
POSTGRES_HOST="127.0.0.1"
POSTGRES_PORT=5432
POSTGRES_DB="epic_events_db"

DATABASE_URL="postgresql+psycopg://"$POSTGRES_USER":"$POSTGRES_PASSWORD"@"$POSTGRES_HOST":"$POSTGRES_PORT"/"$POSTGRES_DB

# Secret key for JWT tokens (use a random and complex string)
SECRET_KEY="replace_with_a_strong_secret_key"

# Optional: DSN for Sentry integration
SENTRY_DSN=""
```

> **Tip** :
*You can generate the SECRET_KEY on [ClinKey](https://dim-gggl.github.io/ClinKey/) 

### Application Initialization

#### Create the database tables:

This command initializes the database schema and inserts the default roles and permissions.
```bash
python epev db-create
```
It creates the first user (Manager):

To administer the application, you must create a user with the "Management" role. 
This operation requires elevated privileges as it creates the first administrator.

On macOS/Linux:
```bash
sudo python epic_events.py manager-create
```

On Windows, run your terminal as an administrator before executing:
```bash
sudo python epic_events.py manager-create
# or uv run epic_events.py manager-create
```

Follow the prompts to set the username, full name, and email. 
You will be asked for the password securely.

6. Launching the Application

You're all set! 

To start using the application, log in with the user you just created.

```bash
epev login
```

To see all available commands, use the built-in help:

```bash
epev help
```

## 7. Utilisation de l'Application

Vous êtes prêt ! Pour commencer à utiliser l'application, connectez-vous avec l'utilisateur que vous venez de créer.

```bash
epev login
```
