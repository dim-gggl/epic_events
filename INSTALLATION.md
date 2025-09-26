# Installation du CRM Epic Events

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
git clone https://github.com/votre-utilisateur/epic_events.git
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

1.  **Créez un utilisateur et une base de données** dans PostgreSQL. Par exemple, en utilisant `psql` :
    ```sql
    CREATE DATABASE epic_events_db;
    CREATE USER epic_events_app WITH PASSWORD 'votre_mot_de_passe_securise';
    GRANT ALL PRIVILEGES ON DATABASE epic_events_db TO epic_events_app;
    ```

2.  **Configurez les variables d'environnement** :
    - Copiez le fichier d'exemple :
      ```bash
      cp .env.example .env
      ```
    - Ouvrez le fichier `.env` et modifiez les valeurs pour correspondre à votre configuration PostgreSQL. Assurez-vous également de définir une `SECRET_KEY` forte pour la sécurité des jetons JWT.

    ```ini
    # .env
    POSTGRES_USER=epic_events_app
    POSTGRES_PASSWORD=votre_mot_de_passe_securise
    POSTGRES_HOST=127.0.0.1
    POSTGRES_PORT=5432
    POSTGRES_DB=epic_events_db

    DATABASE_URL=postgresql+psycopg://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB

    # Clé secrète pour les jetons JWT (utilisez une chaîne aléatoire et complexe)
    SECRET_KEY="remplacer_par_une_cle_secrete_forte"

    # Optionnel : DSN pour l'intégration Sentry
    SENTRY_DSN=""
    ```
	>**Astuce** Vous pouvez générer la `SECRET_KEY` sur [ClinKey](https://dim-gggl.github.io/ClinKey/) 

## 5. Initialisation de l'Application

1.  **Créer les tables de la base de données** :
    Cette commande initialise le schéma de la base de données et insère les rôles et permissions par défaut.
    ```bash
    python epic_events.py db-create
    ```

2.  **Créer le premier utilisateur (Manager)** :
    Pour administrer l'application, vous devez créer un utilisateur avec le rôle "Management". Cette opération nécessite des privilèges élevés car elle crée le premier administrateur.

    - Sur macOS/Linux :
      ```bash
      sudo python epic_events.py manager-create
      ```
    - Sur Windows, lancez votre terminal en tant qu'administrateur avant d'exécuter :
      ```bash
      python epic_events.py manager-create
      ```
    Suivez les instructions pour définir le nom d'utilisateur, le nom complet et l'email. Le mot de passe vous sera demandé de manière sécurisée.

## 6. Lancement de l'Application

Vous êtes prêt ! Pour commencer à utiliser l'application, connectez-vous avec l'utilisateur que vous venez de créer.

```bash
python epic_events.py login
```

Pour voir toutes les commandes disponibles, utilisez l'aide intégrée :

```bash
python epic_events.py --help
```
