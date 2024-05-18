/*
 * Providence
 * SimplyGo Source
 * Models
*/

use chrono::{NaiveDate, NaiveDateTime, NaiveTime};
use serde::{Deserialize, Serialize};
/// Modes of Public Transport.
#[derive(Eq, PartialEq, Debug, Serialize)]
pub enum Mode {
    Rail,
    Bus,
}
/// Leg of a Public Transport Trip made on SimplyGo
#[derive(Debug, Eq, PartialEq, Serialize)]
pub struct Leg {
    /// time when this leg of the trip begins in the Asia/Singapore time zone.
    pub begin_at: NaiveTime,
    /// Cost of this leg of the trip in SGD, expressed as a decimal string
    /// to avoid precision loss in floating point in types. If a concession
    /// pass or travel card is used, cost_sgd will be set to 'Pass Usage'.
    pub cost_sgd: String,
    /// Source location of this leg of the trip.
    pub source: String,
    /// Destination location of this leg of the trip.
    pub destination: String,
    /// Mode of transport.
    pub mode: Mode,
}
/// Public Transport Trip made on SimplyGo
#[derive(Debug, Eq, PartialEq, Serialize)]
pub struct Trip {
    /// Reference no. if the the trip was "Posted" ie. charged on the bank account.
    /// If the trip has not be posted this field will be None.
    pub posting_ref: Option<String>,
    /// Date on which this trip was made in the Asia/Singapore time zone.
    pub traveled_on: NaiveDate,
    /// Legs of the trip
    pub legs: Vec<Leg>,
    /// Id used by SimplyGo to identify Bank Card the trip was made on.
    pub card_id: String,
}
/// A Bank Card registered on SimplyGo
#[derive(Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct Card {
    /// Id used by SimplyGo to identify Card the trip was billed on.
    pub id: String,
    /// Name of Card assigned by user.
    pub name: String,
}
/// Record embeds the raw data produced by SimplyGo source.
#[derive(Debug, Serialize)]
pub struct Record {
    /// Timestamp when the data was scraped in Asia/Singapore timezone.
    #[serde(with = "dt_microsec_fmt")]
    pub scraped_on: NaiveDateTime,
    /// Bank cards registered on SimplyGo.
    pub cards: Vec<Card>,
    /// Date of the start of the time period on Trips were scraped.
    pub trips_from: NaiveDate,
    /// Date of the end of the time period on Trips were scraped.
    pub trips_to: NaiveDate,
    /// Public transport trips scraped from SimplyGo for the specified time period.
    pub trips: Vec<Trip>,
}
/// Defines a datetime format that only retains microsecond resolution
/// from the nanosecond resolution that NaiveDateTime maintains internally.
pub mod dt_microsec_fmt {
    use chrono::NaiveDateTime;
    use serde::Serializer;

    pub fn serialize<S>(timestamp: &NaiveDateTime, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(&timestamp.format("%Y-%m-%dT%H:%M:%S%.6f").to_string())
    }
}
