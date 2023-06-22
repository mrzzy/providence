#
# Providence
# Docker Container
# Airflow Container
#

FROM apache/airflow:2.6.1-python3.10

USER root
# create data mountpoint to store state
RUN mkdir -p /data/ && \
  chown -R airflow /data/

USER airflow
# install pipeline requirements
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

CMD ["airflow", "standalone"]
