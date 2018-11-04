# hsvdotbeer

[![Build Status](https://travis-ci.org/hsv-dot-beer/hsvdotbeer.svg?branch=master)](https://travis-ci.org/hsv-dot-beer/hsvdotbeer)
[![Built with](https://img.shields.io/badge/Built_with-Cookiecutter_Django_Rest-F7B633.svg)](https://github.com/agconti/cookiecutter-django-rest)

Collate ALL the Huntsville beers. Check out the project's [documentation](http://hsv-dot-beer.github.io/hsvdotbeer/).

## What is this?

- It's a concept spearheaded by @mjcarroll to make a one-stop-shop for all the Huntsville breweries and bottle shops.

## How do I get started?

### Reading material

- First, get yourself familiar with Django. There are two excellent tutorials to get yourself started:
  - [Django Girls](https://tutorial.djangogirls.org/) assumes you have no experience with Python or the command line and is a great place for total newbies to get started.
  - The [Django](https://docs.djangoproject.com/en/2.1/intro/) tutorial assumes a little bit of basic Python knowledge but is also good.
- Next, take a look at the [Django REST Framework](https://www.django-rest-framework.org/tutorial/1-serialization/) tutorial

### Installing software

- [Python 3.6](https://www.python.org/downloads/)
  - NOTE: We're stuck using Python 3.6 until [Celery 5.0](https://github.com/celery/celery/issues/4500) is released.
- [Docker](https://docs.docker.com/docker-for-mac/install/) (Download for your platform)
  - NOTE: if you intend to develop on Windows, you need to have Windows 10 Pro or Enterprise to be able to use Docker, and you have to have at least a somewhat recent CPU that supports Hyper-V. Any non-Atom CPU from the past 5 years should more than suffice. Also, it'll break VirtualBox. 😿

### Setting Up a Dev Environment

- After you get Python installed, you need to open a command line (see the Django Girls tutorial above) and run `pip3 install pipenv` to be able to install packages.
- Once you have pipenv installed, install packages:

```bash
pipenv install
```

## Local Development

Start the dev server for local use:

```bash
docker-compose up
```

Run a command inside the docker container:

```bash
docker-compose run --rm web [command]
```

## Running without Docker

Say you don't want to use Docker (or can't if you'd rather not kill VirtualBox). Don't worry, here's what you need to get started:

```bash
pipenv install --dev
export DJANGO_SECRET_KEY=your_secret_key
pipenv run python manage.py runserver
```

You'll need to set this up anyway if you're making migrations (i.e. modifying models).

## Contributing and Community

PRs are more than welcome.  As we get a better idea of what we need to do, we'll create issues that need fixing if you don't know where to start.  All contributors are required to follow the [Tech256 Code of Conduct](https://github.com/tech256/CoC).

You can find us on the [Tech256 Slack](https://tech256.com) in the `#hsv_dot_beer` channel.
