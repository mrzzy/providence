#
# Providence
# SimplyGo Source
#

FROM rust:1.68.2 AS build
RUN mkdir /app
WORKDIR /app
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    rclone=1.53.3-1+b6 \
    # install CA certificates needed by openssl to verify server identity
    ca-certificates=20210119 \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# build dependencies in separate layer to cache dependencies
COPY Cargo.toml Cargo.lock /app/
RUN mkdir src && touch src/lib.rs && cargo build --release
# remove marker for library built with empty lib.rs to trigger rebuild of simplygo_src's lib.rs
# otherwise, cargo will assume simplygo_src's lib.rs as empty library with no symbols,
# causing linking issues for main.rs
RUN rm target/release/deps/libsimplygo_src*
# build source code
COPY src/ /app/src/
RUN cargo build --release

# Binary only production image
FROM debian:bullseye-slim AS release
# create non root user to simplygo source
ARG USER=simplygo
RUN adduser --system simplygo
# copy ca certificates
COPY --from=build /etc/ssl/certs /etc/ssl/certs
# copy release & rclone binary
COPY --from=build /usr/bin/rclone /usr/bin/rclone
COPY --from=build /app/target/release/simplygo_src /bin/simplygo_src

USER simplygo
ENTRYPOINT [ "/bin/simplygo_src" ]
