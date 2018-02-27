# Category Project
## Contents
- application.py - catalog app.
- database_setup.py - database schemas.
- util.py - some utility functions. 
- templates/: Jinja2 templates. 
- static/: css and js files. 
- client_secrets.json: google oauth client secrets (need to put a real key to login)
- *Not necessay to run*:
	- catalog.db: sample catalog database.
	- prepare_data.py: execute to generate test data. 

## Features
- Display all catalog items on homepage
- Hierarchical category, a category can have (technically) unlimited sub-categories.
- Login to edit categories and items.
- Add, delete, edit, and also move items. 
- URL Slug for better SEO?
- Batch add items: upload a whole category from a json file.
- Setup page: it lead you to a setup page if you run the app with an empty database.

## Environment Requirements
- Python 2.7 or above (tested on Python 2.7 and 3.5.2).
- [Virtual Machine from the class], or you can config your own environment referring to the virtual machine settings if you are an expert (i.e. pip install flask/sqlalchemy/werkzeug/oauth2client). 


## How To Use
Download, unzip, and execute application.py in your Vagrant VM:
```sh
python application.py
```
When it shows "Running on http://0.0.0.0:8000/" you can open http://localhost:8000 to view the catalog.
If you want a whole new app, just delete catalog.db before run the app. It will let you login and lead you to the manage page. 

## JSON API
http://localhost:8000/catalog.json for the whole catalog.
http://localhost:8000/catalog/[slug].json for single item.
http://localhost:8000/catalog/subtree/[slug].json for a category.

## Program Design
As a catalog is often hierarchical, I simply treat categories and items as same kind of record in database. So there is only one database table for the whole catalog. 


## Discussion and Things TODO
- I tried not to install any other dependencies to make the app out-of-the-box available. But in real production environment, there are wheels like [flask-login] or [sqlalchemy_mptt] to make things easier. 
- In a real catalog, it does not need unlimited hierarchy levels. So it may be better to use two tables: one category table and one item table. 
- Actually this is a kind of content management system, so there should be different kinds of users: administrators, editors and viewers. 
- Templates mostly follows the restaurant app. Could be redesigned. 
- SQLite is so lite. Maybe migrate to a better one?

[Virtual Machine from the class]: https://classroom.udacity.com/nanodegrees/nd004/parts/8d3e23e1-9ab6-47eb-b4f3-d5dc7ef27bf0/modules/bc51d967-cb21-46f4-90ea-caf73439dc59/lessons/5475ecd6-cfdb-4418-85a2-f2583074c08d/concepts/14c72fe3-e3fe-4959-9c4b-467cf5b7c3a0
[sqlalchemy_mptt]: http://sqlalchemy-mptt.readthedocs.io
[flask-login]: https://flask-login.readthedocs.io/en/latest/
