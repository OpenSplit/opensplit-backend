FROM python:3.6-alpine

MAINTAINER Felix Breidenstein <mail@felixbreidenstein.de>
ENV PYTHONUNBUFFERED 1

RUN apk update \
  && apk add --no-cache git\
  && pip install pipenv

RUN mkdir /code
WORKDIR /code

# Install dependencys
ADD Pipfile /code/
ADD Pipfile.lock /code/
RUN pipenv install

# Copy src
ADD . /code/


# Clean everything which comes from the outside as volume
RUN rm -rf /code/var
RUN rm -rf /code/config.py

VOLUME /code/var
VOLUME /code/config.py

CMD ["/code/entry.sh"]
