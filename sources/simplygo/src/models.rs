/*
 * Providence
 * SimplyGo Source
 * Models
*/

use chrono::{NaiveDate, NaiveTime};
use scraper::{ElementRef, Html, Selector};

/// A Bank Card registered on SimplyGo
#[derive(Debug, PartialEq)]
pub struct Card {
    // Id used by SimplyGo to identify Bank Card.
    pub id: String,
    // Name of Bank Card assigned by user.
    pub name: String,
}

/// Parse the Bank Cards from the given /Cards/Transactions page html
pub fn parse_cards(html: &str) -> Vec<Card> {
    let card_sel: &'static Selector =
        &Selector::parse("select#Card_Token[name=\"Card_Token\"] > optgroup > option").unwrap();
    let document = Html::parse_document(html);
    document
        .select(card_sel)
        .map(|option| Card {
            id: option
                .value()
                .attr("value")
                .expect("Missing 'value' attribute in <option> element.")
                .to_owned(),
            name: option.inner_html().to_owned(),
        })
        .collect()
}

/// Public Transport Trip made on SimplyGo
pub struct Trip {
    /// Reference no. if the the trip was "Posted" ie. charged on the bank account.
    /// If the trip has not be posted this field will be null
    pub posting_ref: Option<String>,
    /// Date on which this trip was made.
    pub traveled_on: NaiveDate,
    /// Legs of the trip
    pub legs: Vec<Leg>,
}

/// Modes of Public Transport.
pub enum Mode {
    Unknown,
    Rail,
    Bus,
}
/// Leg of a Public Transport Trip made on SimplyGo
pub struct Leg {
    /// time when this leg of the trip begins in the Asia/Singapore time zone.
    pub begin_at: NaiveTime,
    /// Cost of this leg of the trip in SGD, expressed as a decimal string
    // to avoid precision loss in floating point in types.
    pub cost_sgd: String,
    /// Source location of this leg of the trip.
    pub source: String,
    /// Destination location of this leg of the trip.
    pub destination: String,
    /// Mode of transport.
    pub mode: Mode,
}

/// Parse legs of a Trip given <tr> tag representing a Trip Record.
fn parse_trip_legs(tr: ElementRef) -> Vec<Leg> {
    // css selectors for parsing trip legs
    let trip_legs_sel: &'static Selector =
        &Selector::parse("table.Table-payment-statement-mobile > tbody > tr").unwrap();
    let time_sel: &'static Selector = &Selector::parse("td.col1 > div").unwrap();
    let journey_sel: &'static Selector = &Selector::parse("td.col2 > div").unwrap();
    let cost_sel: &'static Selector = &Selector::parse("td.col3 > div").unwrap();
    let mode_img_sel: &'static Selector = &Selector::parse("td.col5 > div > img").unwrap();

    tr.select(trip_legs_sel)
        .map(|tr| {
            // parse source and destination from journey column in format: <SRC>-<DEST>
            let src_dest = tr
                .select(journey_sel)
                .next()
                .expect("Missing expected 'Journey' column in Trip Leg.")
                .inner_html()
                .split_once("-")
                .expect("Malformed 'Journey' column value in Trip Leg.");
            // parse mode of transport icon img src url
            let mode_img_src = tr
                .select(mode_img_sel)
                .next()
                .expect("Missing expected <img> tag depicting mode of transport.")
                .value()
                .attr("src")
                .unwrap();
            Leg {
                begin_at: NaiveTime::parse_from_str(
                    &tr.select(time_sel)
                        .next()
                        .expect("Missing expected 'Date/Time' column in Trip Leg.")
                        .inner_html(),
                    "%H:%M %p",
                )
                .expect("Could not parse time in format: HH:MM AM|PM"),
                cost_sgd: tr
                    .select(cost_sel)
                    .next()
                    .expect("Missing expected 'Charges' column in Trip Leg.")
                    .inner_html()
                    .replace("$", "")
                    .trim()
                    .to_owned(),
                source: src_dest.0.trim().to_owned(),
                destination: src_dest.1.trim().to_owned(),
                mode: if mode_img_src.contains("icon-rail") {
                    Mode::Rail
                } else if mode_img_src.contains("icon-bus") {
                    Mode::Bus
                } else {
                    Mode::Unknown
                },
            }
        })
        .collect()
}

// Parse Date from simplygo's format (eg. Wed, 22-Feb-2023)
fn parse_date(date_str: &str) -> NaiveDate {
    NaiveDate::parse_from_str(
        date_str
            .split_once(',')
            .expect("Expected date to be SimplyGo's format.")
            .1,
        "%v",
    )
    .expect("Could not parse date in DD-Mmm-YYYY format.")
}

/// Parse Trips from the given /Card/GetTransactions html
pub fn parse_trips(html: &str) -> Vec<Trip> {
    // css selectors for parsing trip
    let trip_record_sel: &'static Selector = &Selector::parse(".form-record > table > tr").unwrap();
    let statement_sel: &'static Selector = &Selector::parse(".journey_p_collapse").unwrap();
    let date_sel: &'static Selector = &Selector::parse("td.col1").unwrap();
    let posting_sel: &'static Selector = &Selector::parse("td.col2 > div").unwrap();
    let document = Html::parse_document(html);
    document
        .select(trip_record_sel)
        // skip payment posting statment row
        .skip(1)
        .map(|tr| {
            // parse trip from payment statement
            let statement = tr
                .select(statement_sel)
                .next()
                .expect("Missing Trip Payment Statement in Trip Record.");
            Trip {
                traveled_on: parse_date(
                    &statement
                        .select(date_sel)
                        .next()
                        .expect("Missing expected 'Date/Time' column in Payment Statement.")
                        .inner_html(),
                ),
                posting_ref: statement
                    .select(posting_sel)
                    .next()
                    // parse posting ref in format: '[Posting Ref No : <POSTING_REF>]'
                    .map(|div| {
                        div.inner_html()
                            .split_once(":")
                            .expect("Malformed Posting Ref.")
                            .1
                            .split_once("]")
                            .expect("Malformed Posting Ref.")
                            .0
                            .trim()
                            .to_owned()
                    }),
                legs: parse_trip_legs(tr),
            }
        })
        .collect()
}
#[cfg(test)]
mod tests {
    use std::fs::read_to_string;

    use super::*;

    #[test]
    fn parse_cards_test() {
        let html = read_to_string(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/resources/simplygo_card_transactions.html"
        ))
        .unwrap();
        assert!(parse_cards(&html)
            .into_iter()
            .zip(
                vec![
                    Card {
                        id: "card-id-1".to_owned(),
                        name: "Visa".to_owned()
                    },
                    Card {
                        id: "card-id-2".to_owned(),
                        name: "Mastercard".to_owned()
                    },
                ]
                .into_iter()
            )
            .all(|(actual, expected)| actual == expected))
    }
}
