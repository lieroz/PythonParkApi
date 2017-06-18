FROM ubuntu:16.04

MAINTAINER Sergey Krestov

# Обвновление списка пакетов
RUN apt-get -y update

#
# Установка postgresql
#
ENV PGVER 9.5
RUN apt-get install -y postgresql-$PGVER

# Установка Python3
RUN apt-get install -y python3
RUN apt-get install -y python3-pip
RUN pip3 install --upgrade pip
RUN pip3 install pytz
RUN pip3 install psycopg2
RUN pip3 install gunicorn
RUN pip3 install flask

USER postgres

# Create a PostgreSQL role named ``docker`` with ``docker`` as the password and
# then create a database `dbapi` owned by the ``docker`` role.
RUN /etc/init.d/postgresql start &&\
    psql --command "CREATE USER docker WITH SUPERUSER PASSWORD 'docker';" &&\
    createdb -E UTF8 -T template0 -O docker docker &&\
    /etc/init.d/postgresql stop

# Adjust PostgreSQL configuration so that remote connections to the
# database are possible.
RUN echo "host all  all    0.0.0.0/0  md5" >> /etc/postgresql/$PGVER/main/pg_hba.conf

RUN echo "listen_addresses='*'" >> /etc/postgresql/$PGVER/main/postgresql.conf
RUN echo "synchronous_commit=off" >> /etc/postgresql/$PGVER/main/postgresql.conf

# Expose the PostgreSQL port
EXPOSE 5432

# Add VOLUMEs to allow backup of config, logs and databases
VOLUME  ["/etc/postgresql", "/var/log/postgresql", "/var/lib/postgresql"]

# Back to the root user
USER root

# Копируем исходный код в Docker-контейнер
ENV WORK /opt/forum_db
ADD database/ $WORK/database/
ADD appconfig.py $WORK/appconfig.py
ADD routes.py $WORK/routes.py
ADD main.py $WORK/main.py
ADD schema.sql $WORK/schema.sql

# Объявлем порт сервера
EXPOSE 5000

#
# Запускаем PostgreSQL и сервер
#
ENV PGPASSWORD docker
CMD service postgresql start &&\
    cd $WORK/ &&\
    psql -h localhost -U docker -d docker -f schema.sql &&\
    gunicorn -w 4 -b :5000 main:app
