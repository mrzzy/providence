/*
 * Providence
 * SimplyGo Source
 * Parsing Unit Tests
*/

use std::fs::read_to_string;

use chrono::NaiveDate;

use super::*;

const LEG_CSS_SELECTOR: &str = ".data-p-row-item-02 tbody > tr";

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

// Get a <tr> tag representing a full trip record from the given html
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
        Some(posting_ref)
    );
    assert_eq!(parse_posting("                     "), None);
}

#[test]
fn parse_journey_test() {
    let html = load_html("simplygo_card_gettransactions.html");
    // skip to next row as its a more rigorous test case to parse
    let tr = html
        .select(&Selector::parse(LEG_CSS_SELECTOR).unwrap())
        .skip(1)
        .next()
        .unwrap();
    assert_eq!(
        (
            "Bedok Stn Exit B".to_owned(),
            "Upp East Coast Ter".to_owned()
        ),
        parse_journey(&tr)
    )
}

#[test]
fn parse_transport_mode_test() {
    let html = load_html("simplygo_card_gettransactions.html");
    assert_eq!(
        Mode::Rail,
        parse_transport_mode(
            &html
                .select(&Selector::parse(LEG_CSS_SELECTOR).unwrap())
                .next()
                .unwrap()
        )
    );
}

#[test]
fn parse_trip_legs_test() {
    let html = load_html("simplygo_card_gettransactions.html");
    let trip_legs = parse_trip_legs(
        // extra <tbody> automatically inserted on html parsing
        &html
            .select(&Selector::parse(TRIP_CSS_SELECTOR).unwrap())
            .filter(unmatch_posting_table)
            // skip the first trip as are matching against second trip in this test
            .skip(1)
            .next()
            .unwrap(),
    );

    assert!(trip_legs.len() > 0);
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
            source: "Bedok Stn Exit B".to_owned(),
            destination: "Upp East Coast Ter".to_owned(),
            mode: Mode::Bus,
        }
    ]
    .into_iter()
    .zip(trip_legs)
    .all(|(expected, actual)| { expected == actual }))
}

#[test]
fn parse_trips_test() {
    let html = load_html("simplygo_card_gettransactions.html");
    let trip_trs: Vec<_> = html
        .select(&Selector::parse(TRIP_CSS_SELECTOR).unwrap())
        .filter(unmatch_posting_table)
        .collect();
    let card_id = "card-id";
    let trips = parse_trips(card_id, &html.html());
    assert!(trips.len() > 0);
    assert!(vec![
        Trip {
            posting_ref: Some("BUS/MRT 235310372".to_owned()),
            traveled_on: NaiveDate::from_ymd_opt(2023, 2, 22).unwrap(),
            legs: parse_trip_legs(&trip_trs[0]),
            card_id: card_id.to_owned()
        },
        Trip {
            posting_ref: Some("BUS/MRT 235310372".to_owned()),
            traveled_on: NaiveDate::from_ymd_opt(2023, 2, 22).unwrap(),
            legs: parse_trip_legs(&trip_trs[1]),
            card_id: card_id.to_owned()
        }
    ]
    .into_iter()
    .zip(trips)
    .all(|(expected, actual)| expected == actual))
}

#[test]
fn parse_trips_unposted_test() {
    let html = load_html("simplygo_card_gettransactions_unposted.html");
    let trip_trs: Vec<_> = html
        .select(&Selector::parse(TRIP_CSS_SELECTOR).unwrap())
        .collect();
    let card_id = "card-id".to_owned();
    let trips = parse_trips(&card_id, &html.html());
    assert!(vec![Trip {
        posting_ref: None,
        traveled_on: NaiveDate::from_ymd_opt(2023, 4, 13).unwrap(),
        legs: parse_trip_legs(&trip_trs[0]),
        card_id: card_id.to_owned()
    },]
    .into_iter()
    .zip(trips)
    .all(|(expected, actual)| expected == actual))
}

#[test]
fn parse_trips_empty_test() {
    let html = load_html("simplygo_card_gettransactions_empty.html");
    let card_id = "card-id".to_owned();
    let trips = parse_trips(&card_id, &html.html());
    assert_eq!(trips, vec![]);
}
