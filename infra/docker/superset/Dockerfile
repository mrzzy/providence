#
# Providence
# Superset Config
# Superset Container for Docker Compose Deploymeent
#

FROM apache/superset:0e3f1f638c06de11668c37329ca7141fd1159293

USER root
# create data mountpoint to store state
RUN mkdir -p /data /app/docker && \
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
