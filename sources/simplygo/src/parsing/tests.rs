/*
 * Providence
 * SimplyGo Source
 * Parsing Unit Tests
*/

use std::fs::read_to_string;

use chrono::NaiveDate;

use super::*;

// Load HTML page from resources for testing
fn load_html(filename: &str) -> Html {
    Html::parse_document(
        &read_to_string(format!(
                "{}/resources/{}",
                env!("CARGO_MANIFEST_DIR"),
                filename
        ))
        .unwrap(),
    )
}

// Get a <tr> tag representing a leg of a trip for testing foom the given html
fn load_leg_tr(html: &Html) -> ElementRef {
    html.select(&Selector::parse(".data-p-row-item-01 tbody > tr").unwrap())
        .next()
        .unwrap()
}

#[test]
fn parse_cards_test() {
    assert!(
        parse_cards(&load_html("simplygo_card_transactions.html").html())
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
        .all(|(actual, expected)| actual == expected)
    )
}

#[test]
fn parse_date_test() {
    assert_eq!(
        parse_date("Wed, 22-Feb-2023"),
        NaiveDate::from_ymd_opt(2023, 2, 22).unwrap(),
    );
}

#[test]
fn parse_posting_test() {
    let posting_ref = "_POSTING_REF";
    assert_eq!(
        parse_posting(&format!("[Posting Ref No : {}]", posting_ref)),
        posting_ref
    );
}

#[test]
fn parse_journey_test() {
    let html = load_html("simplygo_card_gettransactions.html");
    assert_eq!(
        ("Raffles Place".to_owned(), "Bedok".to_owned()),
        parse_journey(&load_leg_tr(&html))
    )
}

#[test]
fn parse_tranport_mode_test() {
    let html = load_html("simplygo_card_gettransactions.html");
    assert_eq!(Mode::Rail, parse_tranport_mode(&load_leg_tr(&html)));
}
