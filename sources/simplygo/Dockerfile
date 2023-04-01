#
# Providence
# SimplyGo Source
#

FROM rust:1.68.2 AS build
RUN mkdir /app
WORKDIR /app
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
# install CA certificates needed by openssl to verify server identity
RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates=20211016ubuntu0.22.04.1 \
  && rm -rf /var/lib/apt/lists/*
COPY --from=build /app/target/release/simplygo_src /bin/simplygo_src
ENTRYPOINT [ "/bin/simplygo_src" ]
