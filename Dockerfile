FROM python:3.8.10

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update
RUN apt-get upgrade -y && apt-get -y install postgresql gcc python3-dev musl-dev supervisor



RUN pip install --upgrade pip

COPY . .

COPY ./requirements.txt .
RUN pip install -r requirements.txt
#RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt

#FROM python:3.10

RUN mkdir -p /home/app

RUN groupadd app
RUN useradd -m -g app app -p PASSWORD
RUN usermod -aG app app



ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/static
RUN mkdir $APP_HOME/media
RUN mkdir $APP_HOME/media/declaration

WORKDIR $APP_HOME

RUN apt-get update \
    && apt-get install -y netcat

#COPY --from=builder /usr/src/app/wheels /wheels
#COPY --from=builder /usr/src/app/requirements.txt .
#RUN pip install --no-cache /wheels/*

COPY ./entrypoint.sh $APP_HOME

COPY . $APP_HOME


COPY . $APP_HOME

COPY supervisor/supervisor.conf /etc/supervisor/conf.d/
RUN mkdir /run/daphne/
RUN chown app:app /run/daphne/
RUN mkdir /usr/lib/tmpfiles.d/daphne.conf


RUN chown -R app:app $APP_HOME

RUN ln -s /mnt/volume_fra1_01 local_storage


RUN chmod +x /home/app/web/entrypoint.sh

USER app

ENTRYPOINT ["/home/app/web/entrypoint.sh"]