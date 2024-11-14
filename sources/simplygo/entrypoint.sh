#
# Providence
# SimplyGo Source
# Container Entrypoint
#

set -exu -o pipefail

# scrape SimplyGo with SimplyGo source
python simplygo_src.py --trips-from $1 --trips-to $1 --output /tmp/out.json
# copy scraped data to B2
rclone copy --size-only --fast-list /tmp/out :b2:mrzzy-co-data-lake/staging/by=simplygo_src_v2/date=$1
