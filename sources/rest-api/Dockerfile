#
# Providence
# REST API Source
# Dockerfile
#

FROM python:3.12.4-slim

# create system user for rest-api source
ARG USER=api
RUN adduser --system ${USER}
USER ${USER}
ENV PATH=/home/${USER}/.local/bin:${PATH}
WORKDIR /home/${USER}

# install pip module requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy source code
COPY rest_api.py .

ENTRYPOINT [ "python", "rest_api.py"]
