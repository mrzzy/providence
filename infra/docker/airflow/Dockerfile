#
# Providence
# Docker Container
# Airflow Container for Docker Compose Deploymeent
#

FROM apache/airflow:2.6.1-python3.10

USER root
# create data mountpoint to store state
RUN mkdir -p /data/ && \
  chown -R airflow /data/

USER airflow
CMD ["airflow", "standalone"]
