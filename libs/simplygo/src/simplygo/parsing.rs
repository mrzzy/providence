/*
 * Providence
 * SimplyGo Source
 * Parsing
*/

use chrono::{NaiveDate, NaiveTime};
use regex::Regex;
use scraper::{ElementRef, Html, Selector};

use crate::models::{Card, Leg, Mode, Trip};

#[cfg(test)]
mod tests;

const TRIP_CSS_SELECTOR: &str = ".form-record > table > tbody > tr";

/// Parse the Bank Cards from the given /Cards/Transactions page html
pub fn parse_cards(html: &str) -> Vec<Card> {
    let card_sel =
        Selector::parse("select#Card_Token[name=\"Card_Token\"] > optgroup > option").unwrap();
    let document = Html::parse_document(html);
    document
        .select(&card_sel)
        .map(|option| Card {
            id: option
                .value()
                .attr("value")
                .expect("Missing 'value' attribute in <option> element.")
                .to_owned(),
            name: option.inner_html(),
        })
        .collect()
}

/// Parse Date from simplygo's format (eg. Wed, 22-Feb-2023)
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

/// Parse Posting Ref in format: '[Posting Ref No : <POSTING_REF>]'
fn parse_posting(posting_str: &str) -> Option<&str> {
    let trim_posting = posting_str.trim();
    if trim_posting.is_empty() {
        None
    } else {
        Some(
            posting_str
                .split_once(':')
                .expect("Malformed Posting Ref.")
                .1
                .split_once(']')
                .expect("Malformed Posting Ref.")
                .0
                .trim(),
        )
    }
}

/// Parse source and destination from journey column in the <tr> tag representing
/// a Trip Record.
fn parse_journey(tr: &ElementRef) -> (String, String) {
    let journey_sel = Selector::parse("td.col2 > div").unwrap();
    let journey_str = tr
        .select(&journey_sel)
        .next()
        .expect("Missing expected 'Journey' column in Trip Leg.")
        .inner_html();
    // extract source & destination from journey via regex
    let journey_re = Regex::new(r"(?P<source>\b[\w ]+\b) - (?P<destination>\b[\w ]+\b)").unwrap();
    let captures = journey_re
        .captures(&journey_str)
        .expect("Malformed 'Journey' column value in Trip Leg.");
    (
        captures["source"].to_owned(),
        captures["destination"].to_owned(),
    )
}

/// Parse transport Mode from <img>'s 'src' attribute in the <tr> tag representing
/// a Trip Record.
fn parse_transport_mode(tr: &ElementRef) -> Mode {
    let mode_img_sel = Selector::parse("td.col5 > div > img").unwrap();
    let mode_img_src = tr
        .select(&mode_img_sel)
        .next()
        .expect("Missing expected <img> tag depicting mode of transport.")
        .value()
        .attr("src")
        .unwrap();

    use Mode::*;
    match mode_img_src {
        s if s.contains("bus") => Bus,
        s if s.contains("rail") => Rail,
        _ => panic!("Could not determine transport mode from <img> tag."),
    }
}
/// Parse legs of a Trip given <tr> tag representing a Trip Record.
fn parse_trip_legs(tr: &ElementRef) -> Vec<Leg> {
    // css selectors for parsing trip legs
    let trip_legs_sel =
        Selector::parse("table.Table-payment-statement-mobile > tbody > tr").unwrap();
    let time_sel = Selector::parse("td.col1 > div").unwrap();
    let cost_sel = Selector::parse("td.col3 > div").unwrap();

    tr.select(&trip_legs_sel)
        .map(|tr| {
            let (source, destination) = parse_journey(&tr);
            // parse mode of transport icon img src url
            Leg {
                begin_at: NaiveTime::parse_from_str(
                    &tr.select(&time_sel)
                        .next()
                        .expect("Missing expected 'Date/Time' column in Trip Leg.")
                        .inner_html(),
                    "%I:%M %p",
                )
                .expect("Could not parse time in format: HH:MM AM|PM"),
                cost_sgd: tr
                    .select(&cost_sel)
                    .next()
                    .expect("Missing expected 'Charges' column in Trip Leg.")
                    .inner_html()
                    .replace('$', "")
                    .trim()
                    .to_owned(),
                source,
                destination,
                mode: parse_transport_mode(&tr),
            }
        })
        .collect()
}

/// Predicate that all matches all elements except the Payment Posting Statement
/// table in the given element.
fn unmatch_posting_table(element: &ElementRef) -> bool {
    let posting_table_sel = Selector::parse(".Table-payment-statement-post").unwrap();
    element.select(&posting_table_sel).count() == 0
}

/// Parse Trips from the given /Card/GetTransactions html
pub fn parse_trips(card_id: &str, html: &str) -> Vec<Trip> {
    // css selectors for parsing trip
    // extra <tbody> automatically inserted on html parsing
    let trip_record_sel = Selector::parse(TRIP_CSS_SELECTOR).unwrap();
    let statement_sel = Selector::parse(".journey_p_collapse").unwrap();
    let date_sel = Selector::parse("td.col1").unwrap();
    let posting_sel = Selector::parse("td.col2 > div").unwrap();
    let document = Html::parse_document(html);
    document
        .select(&trip_record_sel)
        .filter(unmatch_posting_table)
        .map(|tr| (tr, tr.select(&statement_sel).next()))
        // skip <tr> without a payment statement
        .filter(|(_, statement)| statement.is_some())
        .map(|(tr, statement)| {
            // parse trip from payment statement
            Trip {
                traveled_on: parse_date(
                    &statement
                        .unwrap()
                        .select(&date_sel)
                        .next()
                        .expect("Missing expected 'Date/Time' column in Payment Statement.")
                        .inner_html(),
                ),
                posting_ref: parse_posting(
                    &statement
                        .unwrap()
                        .select(&posting_sel)
                        .next()
                        .expect("Missing expected Posting Ref <div> in Payment Statement.")
                        .inner_html(),
                )
                .map(|s| s.to_owned()),
                legs: parse_trip_legs(&tr),
                card_id: card_id.to_owned(),
            }
        })
        .collect()
}
