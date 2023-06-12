#
# Providence
# Superset Container for Docker Compose Deploymeent
# Superset Config
#

FROM apache/superset:0e3f1f638c06de11668c37329ca7141fd1159293

USER root
RUN mkdir -p /data /app/docker && \
  # create sqlite db to store superset state
  python -c 'import sqlite3; conn = sqlite3.connect("/data/superset.db"); conn.close()' && \
  chown -R superset:superset /data /app/docker

# download superset container bootstrap scripts
ADD --chown=superset:superset https://github.com/apache/superset/raw/master/docker/docker-bootstrap.sh /app/docker/
ADD --chown=superset:superset https://github.com/apache/superset/raw/master/docker/docker-init.sh /app/docker/
ADD --chown=superset:superset https://github.com/apache/superset/raw/master/docker/docker-ci.sh /app/docker/
RUN chmod a+rx /app/docker/*.sh

# copy custom superset config overrides
COPY --chown=superset:superset superset_config.py /app/

USER superset
CMD [ "/app/docker/docker-ci.sh" ]
