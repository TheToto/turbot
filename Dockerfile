FROM python:3.8

RUN pip install pipenv

WORKDIR /app

COPY Pipfile Pipfile.lock ./

RUN set -ex && pipenv install --deploy --system

COPY . /app
