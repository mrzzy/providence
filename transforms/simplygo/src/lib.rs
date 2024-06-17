/*
 * Providence
 * SimplyGo Transform
*/

use std::io::Write;

use arrow::datatypes::FieldRef;
use chrono::{DateTime, NaiveDateTime, Utc};
use chrono_tz::Asia;
use parquet::arrow::ArrowWriter;
use serde::{Deserialize, Serialize};
use serde_arrow::schema::{SchemaLike, TracingOptions};
use simplygo::models::{Card, Trip};

/// Trip Record defines the structure of the tabular trip data extracted. Most
/// fields are flattened from SimplyGo models `Card`, `Trip`,`Leg` etc. Documentation
/// for the fields can be found in respective source model.
#[derive(Serialize, Deserialize, Clone, Debug, PartialEq, Eq)]
pub struct Record<'a> {
    card_id: &'a str,
    card_name: &'a str,
    cost_sgd: &'a str,
    source: &'a str,
    destination: &'a str,
    mode: String,
    posting_ref: &'a str,
    /// Identifier that uniquely identifies which trip the trip leg belongs to
    trip_id: String,
    /// Timestamp when the trip leg was performed in the Asia/Singapore timezone.
    traveled_on: String,
    /// Timestamp when the data was scraped by 'simplygo_src' in Asia/Singapore timezone.
    scraped_on: String,
    /// Timestamp when the data was extracted by this program in Asia/Singapore timezone.
    transformed_on: String,
}

impl Record<'_> {
    fn schema() -> Vec<FieldRef> {
        Vec::<FieldRef>::from_type::<Record>(TracingOptions::default().allow_null_fields(true))
            .unwrap_or_else(|e| panic!("{}", e))
    }
}

/// Constructs unique identifier for the given trip.
/// Expects the given trip to contain at least one leg.
fn trip_id(trip: &Trip) -> String {
    format!(
        "{}_{}",
        trip.card_id,
        trip.traveled_on.and_time(trip.legs[0].begin_at)
    )
}

/// Flatten the given trip data into records. Each leg of the trip is flattened
/// into 1 record.
/// `scraped_on` & `transformed_on` timestamps should be given in Asia/Singapore
/// timezone.
pub fn flatten_records<'a>(
    card: &'a Card,
    trips: &'a [Trip],
    scraped_on: &'a NaiveDateTime,
    transformed_on: &'a NaiveDateTime,
) -> Vec<Record<'a>> {
    trips
        .iter()
        // filter out trips with no legs
        .filter(|trip| !trip.legs.is_empty())
        .flat_map(|trip| {
            trip.legs
                .iter()
                .map(|leg| Record {
                    trip_id: trip_id(trip),
                    card_id: &card.id,
                    card_name: &card.name,
                    cost_sgd: &leg.cost_sgd,
                    source: &leg.source,
                    destination: &leg.destination,
                    mode: format!("{:?}", leg.mode),
                    posting_ref: trip.posting_ref.as_deref().unwrap_or_default(),
                    traveled_on: trip.traveled_on.and_time(leg.begin_at).to_string(),
                    scraped_on: scraped_on.to_string(),
                    transformed_on: transformed_on.to_string(),
                })
                .collect::<Vec<_>>()
        })
        .collect()
}

/// Convert UTC datetime to naive datetime in Asia/Singapore time.
pub fn to_sgt(utc: DateTime<Utc>) -> NaiveDateTime {
    utc.with_timezone(&Asia::Singapore).naive_local()
}

/// Write given records to given destination in Parquet file format (uncompressed).
pub fn write_parquet<'a, W: Write + Send>(records: &[Record<'a>], dest: &mut W) {
    // convert records to arrow batch
    let batch = serde_arrow::to_record_batch(&Record::schema(), &records)
        .unwrap_or_else(|e| panic!("Could not convert records to Arrow: {}", e));
    // write to dest via parquet writer
    let mut pq = ArrowWriter::try_new(dest, batch.schema(), None)
        .unwrap_or_else(|e| panic!("Failed to create Parquet Arrow Writer: {}", e));
    pq.write(&batch)
        .unwrap_or_else(|e| panic!("Failed to write records to Parquet: {}", e));
    pq.close()
        .unwrap_or_else(|e| panic!("Failed to close Parquet Arrow Writer: {}", e));
}

#[cfg(test)]
mod tests {
    use bytes::Bytes;

    use chrono::Utc;
    use parquet::arrow::arrow_reader::ParquetRecordBatchReader;
    use serde_arrow::Deserializer;
    use simplygo::models::Leg;

    use super::*;

    #[test]
    fn flatten_records_test() {
        let now = Utc::now().naive_local();
        let trips = &[Trip {
            card_id: "id".to_string(),
            posting_ref: Some("posting".to_string()),
            traveled_on: now.date(),
            legs: vec![Leg {
                begin_at: now.time(),
                cost_sgd: "5.00".to_string(),
                source: "Bukit Timah".to_string(),
                destination: "Raffles Place".to_string(),
                mode: simplygo::models::Mode::Rail,
            }],
        }];
        let card = Card {
            id: trips[0].card_id.clone(),
            name: "card".to_owned(),
        };
        let records = flatten_records(&card, trips, &now, &now);

        assert_eq!(
            records,
            vec![Record {
                trip_id: trip_id(&trips[0]),
                card_id: &card.id,
                card_name: &card.name,
                cost_sgd: &trips[0].legs[0].cost_sgd,
                source: &trips[0].legs[0].source,
                destination: &trips[0].legs[0].destination,
                mode: format!("{:?}", trips[0].legs[0].mode),
                posting_ref: "posting",
                traveled_on: now.to_string(),
                transformed_on: now.to_string(),
                scraped_on: now.to_string(),
            }]
        );
    }

    #[test]
    fn to_sgt_test() {
        let utc = Utc::now();
        let sgt = to_sgt(utc);
        let offset = sgt - utc.naive_local();
        // sg time: +08:00 UTC
        assert_eq!(offset.num_hours(), 8);
    }

    #[test]
    fn write_parquet_test() {
        // write a single record as parquet
        let now = Utc::now().naive_local();
        let mut buffer = Vec::new();
        let expected = Record {
            trip_id: "id".to_string(),
            card_id: "id",
            card_name: "name",
            cost_sgd: "5.00",
            source: "JE",
            destination: "FP",
            mode: "Rail".to_string(),
            posting_ref: "posting",
            traveled_on: now.to_string(),
            transformed_on: now.to_string(),
            scraped_on: now.to_string(),
        };
        write_parquet(&[expected.clone()], &mut buffer);

        // read single record from parquet
        let batch = ParquetRecordBatchReader::try_new(Bytes::from(buffer), 1)
            .unwrap()
            .next()
            .unwrap()
            .unwrap();
        let actual =
            Vec::<Record>::deserialize(Deserializer::from_record_batch(&batch).unwrap()).unwrap();
        assert_eq!(actual[0], expected);
    }
}
