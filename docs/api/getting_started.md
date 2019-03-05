# Getting Started

## Prerequisites

### Linux

Install these packages from your distribution's package manager

- docker
- docker-compose
- python3.6
- pipenv

### Windows

The devs have run into all sorts of weirdness running inside Docker for Windows.

Avoid this if you can.

### macOS

Install [Docker Desktop for Mac](https://hub.docker.com/editions/community/docker-ce-desktop-mac).

Install [Homebrew](https://brew.sh/) and install these packages:

- pipenv

Install the latest 64-bit macOS Installer of Python 3.6 from
[python.org](https://www.python.org/downloads/mac-osx/). **NOTE**: Due to an
incompatibility in one of our dependencies, you *cannot* run this with Python
3.7 or later.

## Installing dependencies

1. Clone the repository.
2. Run from the terminal: `pipenv install --dev`
3. Run tests to make sure everything works:
   ```bash
   docker-compose run --rm web pipenv run ./manage.py test
   ```
5. Run the API:
   ```bash
   docker-compose up
   ```

## Loading fixtures

Seed your database with important values:

```bash
docker-compose run --rm web ./manage.py loaddata */fixtures/*.json
```

### Importing styles

```bash
docker-compose run --rm web ./manage.py import bjcp
```
