#
# Providence
# SimplyGo Transform
# Container Entrypoint
#

set -exuo pipefail

# Copy scraped data from B2
rclone copy --size-only --fast-list :b2:mrzzy-co-data-lake/staging/by=simplygo_src/date=$1 /tmp/raw
# Transform SimplyGo Raw Data to CSV
simplygo_tfm --input-dir /tmp/raw --output /tmp/out.csv
# Copy scraped data to B2
rclone copy --size-only --fast-list /tmp/out.csv :b2:mrzzy-co-data-lake/staging/by=simplygo-tfm/date=$1/out.csv
