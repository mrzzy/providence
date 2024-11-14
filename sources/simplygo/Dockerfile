#
# Providence
# Dockerfile
# simplygo_src
#

# Stage: Build from source
FROM python:3.10.15-slim
RUN adduser --system simplygo
RUN mkdir -p /app
WORKDIR /app
# install rclone for cloud storage support
COPY --from=rclone/rclone:1.66.0 /usr/local/bin/rclone /bin/rclone
# build dependencies in separate layer to cache
COPY requirements.txt /app/
RUN pip install -r  requirements.txt
# copy source code
COPY . /app/
USER simplygo
ENTRYPOINT ["bash", "/app/entrypoint.sh"]
