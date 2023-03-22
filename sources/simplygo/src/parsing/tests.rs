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
fn get_leg_tr(html: &Html) -> ElementRef {
    html.select(&Selector::parse(".data-p-row-item-01 tbody > tr").unwrap())
        .next()
        .unwrap()
}

// Get a <tr> tag representing a full trip record from the given html
fn get_trip_tr(html: &Html) -> ElementRef {
    html.select(&Selector::parse(".form-record > table > tr").unwrap())
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
        parse_journey(&get_leg_tr(&html))
    )
}

#[test]
fn parse_transport_mode_test() {
    let html = load_html("simplygo_card_gettransactions.html");
    assert_eq!(Mode::Rail, parse_transport_mode(&get_leg_tr(&html)));
}

#[test]
fn parse_trip_legs_test() {
    let html = load_html("simplygo_card_gettransactions.html");
    assert!(vec![
        Leg {
            begin_at: NaiveTime::from_hms_opt(22, 13, 00).unwrap(),
            cost_sgd: "1.60".to_owned(),
            source: "Raffles Place".to_owned(),
            destination: "Bedok".to_owned(),
            mode: Mode::Rail,
        },
        Leg {
            begin_at: NaiveTime::from_hms_opt(22, 51, 00).unwrap(),
            cost_sgd: "0.17".to_owned(),
            source: "Bedok Std Exit B".to_owned(),
            destination: "Upp East Coast Ter".to_owned(),
            mode: Mode::Bus,
        }
    ]
    .into_iter()
    .zip(parse_trip_legs(&get_trip_tr(&html)))
    .all(|(expected, actual)| expected == actual))
}
