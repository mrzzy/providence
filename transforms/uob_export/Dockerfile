#
# Providence
# Transforms
# UOB Export
#

# build container
FROM sbtscala/scala-sbt:eclipse-temurin-jammy-17.0.5_8_1.9.0_2.13.10 AS build
# copy source files
COPY . /root
# install dependencies in separate layer for caching
RUN sbt update
# build fat jar with bundled dependencies
# hadolint ignore=DL3059
RUN sbt assembly

# build release container spark runtime +fat jar
FROM apache/spark:3.4.0 AS release
COPY --from=build /root/target/scala-*/uob_export-assembly*.jar /opt/spark/work-dir/uob_export.jar
