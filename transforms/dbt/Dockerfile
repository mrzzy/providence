#
# Providence
# DBT Transform
# Dockerfile
#

FROM ghcr.io/dbt-labs/dbt-redshift:1.4.0

# install dbt packages
WORKDIR /usr/app/dbt
COPY packages.yml dbt_project.yml ./
RUN dbt deps

# copy dbt project
COPY profiles.yml analyses macros models seeds snapshots tests /usr/app/dbt/
