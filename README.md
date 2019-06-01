
[![Built with](https://img.shields.io/badge/Built_with-Cookiecutter_Django_Rest-F7B633.svg)](https://github.com/agconti/cookiecutter-django-rest)

Collate ALL the Huntsville beers. Check out the project's [documentation](https://github.com/austinprog/hsvdotbeer/wiki).

## What is this?

- It's a concept spearheaded by @mjcarroll, @drewbrew, and @drewmcdowell to
make a one-stop-shop for all the Huntsville-area breweries, taprooms, and
bottle shops.

## I want my venue listed!

First, three questions:
1. Are you located within the city of Huntsville, the city of Madison, or
   Madison County, Alabama (this includes smaller cities like Triana or
   Owens Cross Roads)?
2. Do you have at least 6 beer taps in regular use?
3. Of those taps, are 50% or 5 taps, whichever is lower, typically featuring
   beers made in Alabama or Middle Tennessee (we're pretty flexible here)?

If the answer to all 3 of those is yes, great! If not, ask us anyway and we
may be willing to grant you an exception. We're doing this in our spare time
and don't have time to get every bar in Alabama signed up!

Sign up for a free account at https://taplist.io/. Once you're in, create your
taps and beers.

At that point, contact us either via [Twitter](https://twitter.com/hsvdotbeer)
or creating an issue here. We'll guide you through the process of creating a
fake display that we'll use to get the info we need. It doesn't matter whether
you want to use a chalkboard or a digital display; if you want to do the latter,
you can simply create another display.

If you want to have a digital display, you can use either a Fire TV Stick or
a Raspberry Pi. They have great instructions for both at
[their help site](https://taplist.io/help).

## How do I get started?

### Reading material

- First, get yourself familiar with Django. There are two excellent tutorials to get yourself started:
  - [Django Girls](https://tutorial.djangogirls.org/) assumes you have no experience with Python or the command line and is a great place for total newbies to get started.
  - The [Django](https://docs.djangoproject.com/en/2.2/intro/) tutorial assumes a little bit of basic Python knowledge but is also good.
- Next, take a look at the [Django REST Framework](https://www.django-rest-framework.org/tutorial/1-serialization/) tutorial

### Installing software

- [Python 3.7](https://www.python.org/downloads/)
   - Windows 10 users can also install Python from the [Windows Store](https://docs.python.org/3.7/using/windows.html#windows-store)
- [Docker](https://docs.docker.com/docker-for-mac/install/) (Download for your platform)
  - NOTE: if you intend to develop on Windows, you need to have Windows 10 Pro
    or Enterprise to be able to use Docker, and you have to have at least a
    somewhat recent CPU that supports Hyper-V. Any non-Atom CPU from the past 5
    years should more than suffice. Also, it'll break VirtualBox 5.x and older.

### Setting Up a Dev Environment

- After you get Python installed, you need to open a command line (see the
  Django Girls tutorial above) and run `pip3 install pipenv` to be able to
  install packages.
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

Say you don't want to use Docker. Don't worry, here's what you need to get started:

```bash
pipenv install --dev
export DJANGO_SECRET_KEY=your_secret_key
pipenv run python manage.py runserver
```

You'll need to set this up anyway if you're making migrations (i.e. modifying models).

## Contributing and Community

PRs are more than welcome.  As we get a better idea of what we need to do, we'll
create issues that need fixing if you don't know where to start.  All
contributors are required to follow the [Tech256 Code of Conduct](https://github.com/tech256/CoC).

You can find us on the [Tech256 Slack](https://tech256.com) in the `#hsv_dot_beer` channel.
