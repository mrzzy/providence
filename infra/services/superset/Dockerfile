#
# Providence
# Superset Config
# Superset Container for Docker Compose Deploymeent
#

# Environment variables:
# ADMIN_PASSWORD: sets the password of the admin user

FROM apache/superset:0e3f1f638c06de11668c37329ca7141fd1159293

USER root
# create data mountpoint to store state
RUN mkdir -p /data && \
  chown -R superset:superset /data
# copy entrypoint script
COPY --chown=superset:superset entrypoint.sh /app/
RUN chmod a+x /app/entrypoint.sh
# copy custom superset config overrides
COPY --chown=superset:superset superset_config.py /app/

USER superset
CMD [ "/app/entrypoint.sh" ]
