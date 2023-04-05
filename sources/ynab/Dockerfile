#
# Providence
# YNAB Source
# Dockerfile
#

FROM python:3.10.10-slim

# create system user for ynab source
ARG USER=ynab
RUN adduser --system ${USER}
USER ${USER}
WORKDIR /home/${USER}

# install pip module requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy source code
COPY ynab.py .

ENTRYPOINT [ "python", "ynab.py"]
