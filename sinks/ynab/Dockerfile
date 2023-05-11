#
# Providence
# YNAB Sink Dockerfile
# Dockerfile
#

FROM node:18.16.0 AS base

# create system user for ynab sink
ARG USER=ynab
RUN adduser --system ${USER}
USER ${USER}
WORKDIR /home/${USER}

# install npm packages
COPY --chown=ynab:root package.json package-lock.json ./

FROM base AS build
RUN npm ci --ignore-scripts
# copy source code
COPY src ./src
COPY tsconfig.json ./
# compile typescript
RUN npx tsc

FROM base AS production
COPY --from=build /home/ynab/package.json ./
COPY --from=build /home/ynab/package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts
COPY --from=build /home/ynab/dist /home/ynab/dist
ENTRYPOINT [ "/usr/local/bin/node", "/home/ynab/dist/index.js" ]
