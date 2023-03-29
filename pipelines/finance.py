#
# Providence
# Finance
# Data Pipeline
#

from datetime import timedelta
from airflow.decorators import dag, task
from pendulum import datetime

@dag(
    schedule=timedelta(days=1),
    start_date=datetime(2023, 2, 1, tz="utc"),
    catchup=False,
)
def ingest(
    staging_path: str
):
    """
    Ingests data from finance related data sources.

    Parameters:
    - `staging_path`: Path within an already created S3 bucket to stage raw data.
    """
    @task.kubernetes
    def load_s3():
        """Ingest raw public transport trip data from SimplyGo into S3 bucket."""
