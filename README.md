[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv) [![Static Badge](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13%20|%203.14-%233775A9?style=plastic&logo=python&logoColor=%23FFE569)](https://www.python.org/) [![Static Badge](https://img.shields.io/badge/SQLAlchemy-2.0.83-%23a11b18?style=plastic&logo=SQLAlchemy&logoColor=white&color=%23a11b18)](https://www.sqlalchemy.org/) ![Static Badge](https://img.shields.io/badge/PostgreSQL-16.10-%23336690?style=plastic&logo=PostgreSQL&logoColor=white) ![Static Badge](https://img.shields.io/badge/PyJWT-2.10.1-%232980b9?style=plastic&logo=JWT&logoColor=%232980b9) ![Static Badge](https://img.shields.io/badge/Rich-3.8.0-%236ab0de?style=plastic&logo=Rich&logoColor=white) ![Static Badge](https://img.shields.io/badge/sentry--sdk-2.35.1-%23be5db9?style=plastic&logo=Sentry&logoColor=white)


![](src/media/epic_events.png)

# Epic Events CRM

A cool Customer Relationship Management (CRM) system using Python. It’s got all the bells and whistles, like user authentication, role-based permissions, and a really smooth command-line interface.


## Quick Start

To learn more about the installation, it's recommended to read the **[INSTALLATION](./INSTALLATION.md)** page. Here we consider you've already cloned the repository, got Postgresql services running, a database ready to go and a virtual environment activated.

## Usage  

If you try this:
```bash
python epic_events.py help
```
This is what you should see:
![](src/media/help_menu.svg)

At this point, for more convenience, it is recommended to:

```bash
alias epic-events="python epic_events.py"
```

This way, it is possible to 

```bash
epic-events help
```

## Ressources & Commands

The different ressources available in Epic Events database are:

- `Users` (Only Management and admins can see all users)
- `Clients`
- `Contracts`
- `Events`

Each ressource has its own command represented by its name in lowercase and singular form (e.g. `Users` -> `user`).  
  
And each must be completed with the following action commands:

- `list` (to see a list of all the entries for the ressources in a reduced format)
- `view` (to see the details of a specific entry)
- `create` (to create a new entry)
- `update` (to update an existing entry)
- `delete` (to delete an existing entry)
- `help` (to see the help menu for the command)
  
---  
So, if we want the list of all the clients saved in the database, we can do:

```bash
epic-events client list
```

Here is what should appear:

![](src/media/epic-ev-clients.svg)

And from here, we could decide to see the details from the client with the ID #12:

```bash
epic-events client view 12
```

And here's what the oupput should look like :

![](src/media/epic-ev-client.svg)