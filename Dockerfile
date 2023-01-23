FROM python:3.10
ENV PYTHONUNBUFFERED 1

# Allows docker to cache installed dependencies between builds
RUN pip install pipenv
RUN pip install --upgrade pip setuptools wheel

# Adds our application code to the image
COPY . /code
WORKDIR /code

RUN bash /code/setup_node_16.sh
RUN apt-get update && apt-get -y dist-upgrade && apt-get -y install libmemcached-dev nodejs

# the version of node-sass that tailwind uses doesn't work with npm 5.x under node 10.x, which the debian docker image gives us
RUN npm install npm@latest -g

# even though this is where `which npm` points to, running `npm install` without the absolute path still runs npm 5.x,
# but using the absolute path gives us npm 6.x (current latest as of November 2020)
ENV NPM_BIN_PATH /usr/local/bin/npm

# install deps from Pipfile.lock
RUN pipenv install

EXPOSE 8000

# Migrates the database, builds CSS, uploads staticfiles, and runs the production server
CMD bash bin/entry-point.sh
