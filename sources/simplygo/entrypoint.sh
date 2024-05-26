#
# Providence
# SimplyGo Source
# Container Entrypoint
#

set -exuo pipefail

# scrape SimplyGo with SimplyGo source
simplygo_src --trips-from $1 --trips-to $1 --output-dir /tmp/out
# copy scraped data to B2
rclone copy --size-only --fast-list /tmp/out :b2:mrzzy-co-data-lake/staging/by=simplygo_src/date=$1
