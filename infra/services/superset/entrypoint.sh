#!/bin/bash
#
# Providence
# Superset Container for Docker Compose Deploymeent
# Entrypoint Script
#

set -ex -o pipefail

# migrate db
superset db upgrade
# create admin user, disabling shell echo to avoid echoing password
set +x
echo "Creating Admin User..."
superset fab create-admin \
  --username admin \
  --firstname Superset \
  --lastname Admin \
  --email admin@superset.com \
  --password $ADMIN_PASSWORD
set -x

# Setting up roles and perms
superset init

/usr/bin/run-server.sh
