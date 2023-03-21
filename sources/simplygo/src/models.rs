/*
 * Providence
 * SimplyGo Source
 * Models
*/

use chrono::{DateTime, offset::Utc};
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
    /// Reference no. if the the trip was "Posted" ie. charged on the bank account.
    posting_ref: String,
    /// Timestamp when the trip begins.
    begin: DateTime<Utc>,
    /// Duration of the trip in seconds.
    duration_secs: u32,
    // Cost of the trip in SGD, expressed as a decimal string to avoid precision 
    // lost in floating point in types.
    cost_sgd: String,
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
