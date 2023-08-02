#
# Providence
# Transforms
# UOB Export
#

# build container
FROM sbtscala/scala-sbt:eclipse-temurin-jammy-17.0.5_8_1.9.0_2.13.10 AS build
# copy build specification
COPY build.sbt /root/
COPY project /root/project
# install dependencies in separate layer for caching
RUN sbt update
# copy source files
COPY src /root/src
# build fat jar with bundled dependencies
# hadolint ignore=DL3059
RUN sbt assembly

# build release container spark runtime +fat jar
FROM apache/spark:3.4.0 AS release
COPY --from=build /root/target/scala-*/uob_export-assembly*.jar /uob_export.jar
