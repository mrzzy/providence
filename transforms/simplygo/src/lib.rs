/*
 * Providence
 * SimplyGo Transform
*/

use chrono::{DateTime, NaiveDateTime, Utc};
use chrono_tz::Asia;
use serde::Serialize;
use simplygo::models::{dt_microsec_fmt, Card, Mode, Trip};

/// Trip Record defines the structure of the tabular trip data extracted. Most
/// fields are flattened from SimplyGo models `Card`, `Trip`,`Leg` etc. Documentation
/// for the fields can be found in respective source model.
#[derive(Serialize, Debug, PartialEq, Eq)]
pub struct Record<'a> {
    card_id: &'a str,
    card_name: &'a str,
    cost_sgd: &'a str,
    source: &'a str,
    destination: &'a str,
    mode: &'a Mode,
    posting_ref: &'a str,
    // Identifier that uniquely identifies which trip the trip leg belongs to
    trip_id: String,
    /// Timestamp when the trip leg was performed in the Asia/Singapore timezone.
    #[serde(with = "dt_microsec_fmt")]
    traveled_on: NaiveDateTime,
    /// Timestamp when the data was scraped by 'simplygo_src' in Asia/Singapore timezone.
    #[serde(with = "dt_microsec_fmt")]
    scraped_on: &'a NaiveDateTime,
    /// Timestamp when the data was extracted by this program in Asia/Singapore timezone.
    #[serde(with = "dt_microsec_fmt")]
    transformed_on: &'a NaiveDateTime,
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
                    mode: &leg.mode,
                    posting_ref: trip.posting_ref.as_deref().unwrap_or_default(),
                    traveled_on: trip.traveled_on.and_time(leg.begin_at),
                    scraped_on,
                    transformed_on,
                })
                .collect::<Vec<_>>()
        })
        .collect()
}

// Convert UTC datetime to naive datetime in Asia/Singapore time.
pub fn to_sgt(utc: DateTime<Utc>) -> NaiveDateTime {
    utc.with_timezone(&Asia::Singapore).naive_local()
}

#[cfg(test)]
mod tests {
    use chrono::Utc;
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
                mode: &trips[0].legs[0].mode,
                posting_ref: "posting",
                traveled_on: now,
                transformed_on: &now,
                scraped_on: &now,
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
}
