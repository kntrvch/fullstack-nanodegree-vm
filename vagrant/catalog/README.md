# Catalog App

## Description

Catalog App is a basic CRUD application that lets us add/edit/delete items to particular
category based on OAuth2 authentication.

## What's included

```
├── catalog/
│   ├── static/
│   │   ├── style.css
│   ├── templates/
│   │   ├── addcategory.html
│   │   ├── additem.html
│   │   ├── categories.html
│   │   ├── deletecategory.html
│   │   ├── deleteitem.html
│   │   ├── editcategory.html
│   │   ├── edititem.html
│   │   ├── flash.html
│   │   ├── items.html
│   │   ├── login.html
│   │   ├── main.html
│   │   ├── publiccategories.html
│   │   ├── publicitems.html
│   │   ├── sidebar.html
│   ├── application.py
│   ├── client_secrets.json
│   ├── database_setup.py
│   ├── fixtures.py
│   ├── README.md
```

## Installation

After mounting your fullstack-nanodegree-vm machine and log in to it via SSH, prepare your SQLite database by running database_setup.py:

```sh
$ python /vagrant/catalog/database_setup.py
```

.. and run fixtures script to fill it with test data:

```sh
$ python /vagrant/catalog/fixtures.py
```

Now you can run the actual app by executing application.py:

```sh
$ python /vagrant/catalog/application.py
```
