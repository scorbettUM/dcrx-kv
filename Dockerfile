FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /tmp/requirements.txt
COPY README.md /README.md
COPY .version /.version

COPY ./scripts/start.sh /start.sh
RUN chmod +x /start.sh

COPY ./scripts/start-reload.sh /start-reload.sh
RUN chmod +x /start-reload.sh

COPY ./scripts/prestart.sh /prestart.sh
RUN chmod +x /prestart.sh

COPY ./dcrx_kv /dcrx_kv

COPY ./setup.py /setup.py

RUN apt-get update && \
    apt-get install -y postgresql-dev musl-dev


RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && pip install -e .


WORKDIR /dcrx_kv/

EXPOSE 2278

CMD ["/start.sh"]