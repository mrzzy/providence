#
# Providence
# DBT Transform
# Dockerfile
#

FROM ghcr.io/dbt-labs/dbt-redshift:1.4.0

# create system user for dbt
ARG USER=dbt
RUN adduser --system ${USER}
USER ${USER}
WORKDIR /home/${USER}

# install dbt packages
COPY packages.yml dbt_project.yml ./
RUN dbt deps

# copy dbt project
COPY profiles.yml analyses macros models seeds snapshots tests /usr/app/dbt/
