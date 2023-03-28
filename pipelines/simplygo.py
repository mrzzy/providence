#
# Providence
# Data Pipeline
# Ingest SimplyGo
#

from datetime import timedelta
from airflow.decorators import dag, task
from pendulum import datetime

@dag(
    schedule=timedelta(days=1),
    start_date=datetime(2023, 2, 1, tz="utc"),
    catchup=False,
)
def ingest_simpygo():
    """
    Ingest public transport trip data from SimplyGo into Redshift Data Warehouse,
    using S3 bucket as a staging area.
    """
    @task
    def load_s3():
        pass
