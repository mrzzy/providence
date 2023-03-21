/*
 * Providence
 * SimplyGo Source
 * Models
*/

use std::time::Duration;

use chrono::{DateTime, offset::Utc, NaiveTime};
use scraper::{Html, Selector};

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
    let document = Html::parse_document(html);
    document
        .select(
            &Selector::parse("select#Card_Token[name=\"Card_Token\"] > optgroup > option").unwrap(),
        )
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
    /// Bank card to charge for the cost of the trip.
    pub card: Card,
    /// Reference no. if the the trip was "Posted" ie. charged on the bank account.
    /// If the trip has not be posted this field will be null
    pub posting_ref: Option<String>,
    /// Date on which this trip was made
    pub duration: Duration,
    /// Legs of the trip
    pub legs: Vec<Leg>,
}

/// Modes of Public Transport.
pub enum Mode {
    Rail,
    Bus,
}
/// Leg of a Public Transport Trip made on SimplyGo
pub struct Leg {
    /// time when this leg of the trip begins.
    pub begin: NaiveTime,
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
