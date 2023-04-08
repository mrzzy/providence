#
# Providence
# Pandas ETL Transform
# Dockerfile
#

FROM python:3.10.10-slim

# create system user for pandas_etl source
ARG USER=pandas-etl
RUN adduser --system ${USER}
USER ${USER}
WORKDIR /home/${USER}

# install pip module requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy source code
COPY *.py ./

ENTRYPOINT [ "python", "pandas_etl.py"]
