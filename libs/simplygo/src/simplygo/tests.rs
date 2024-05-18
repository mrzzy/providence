/*
 * Providence
 * SimplyGo Source
 * Unit Tests
*/
use std::collections::HashMap;
use std::str;

use httpmock::prelude::*;
use reqwest::{blocking::Client, header::HeaderMap};

use crate::simplygo::csrf::{Csrf, CSRF_KEY};

use super::*;

const SESSION_ID: &str = "_session_id";
const AUTH_TOKEN: &str = "_auth_token";
const CSRF_TOKEN: &str = "_CSRF-TOKEN";

/// Parse Cookies from Cookie http header values.
fn parse_cookies(headers: &HeaderMap) -> HashMap<&str, &str> {
    headers
        .get("Cookie")
        .unwrap()
        .to_str()
        .unwrap()
        .split(";")
        .map(|cookie| cookie.trim())
        // split cookie key & value
        .filter_map(|cookie| {
            let parts: Vec<_> = cookie.split("=").collect();
            parts.get(0).zip(parts.get(1)).map(|(&k, &v)| (k, v))
        })
        .collect()
}

fn simplygo_new(base_url: &str, has_session: bool) -> SimplyGo {
    SimplyGo {
        base_url: base_url.to_string(),
        http: Client::new(),
        csrf: Csrf {
            cookie: CSRF_TOKEN.to_owned(),
            form: CSRF_TOKEN.to_owned(),
        },
        session: if has_session {
            Some(Session {
                id: SESSION_ID.to_owned(),
                auth: AUTH_TOKEN.to_owned(),
            })
        } else {
            None
        },
    }
}

#[test]
fn simplygo_request_test() {
    for has_session in [true, false] {
        let (key, value) = ("_key", "_value");
        let request = simplygo_new(SIMPLYGO_URL, has_session)
            .request(Method::GET, "/test", HashMap::from([(key, value)]))
            .build()
            .unwrap();

        // parse cookies from 'Cookie' http header
        let headers = request.headers();
        let cookies = parse_cookies(headers);

        // test: http method & url
        assert_eq!(format!("{}/test", SIMPLYGO_URL), request.url().as_str());
        assert_eq!(Method::GET, request.method());
        assert_eq!(CSRF_TOKEN, cookies[CSRF_KEY]);
        if has_session {
            // test: session id & auth token attached in cookies
            assert_eq!(SESSION_ID, cookies[SESSION_ID_KEY]);
            assert_eq!(AUTH_TOKEN, cookies[AUTH_TOKEN_KEY]);
        }
    }
}

#[test]
fn simplygo_scrape_test() {
    // mock simplygo api
    let (content, path) = ("ok", "/test");
    let server = MockServer::start();
    server.mock(|when, then| {
        when.method(GET).path(path);
        then.status(200)
            .header("Content-Type", "text/html")
            .body(content);
    });

    let simplygo = simplygo_new(&server.base_url(), false);
    let got = simplygo.scrape(simplygo.request(Method::GET, path, HashMap::new()));
    assert_eq!(got, content);
}

#[test]
fn simplygo_trips_test() {
    // mock simplygo api
    let (content, path) = ("ok", "/Cards/GetTransactions");
    let card = Card {
        id: "id".to_string(),
        name: "card".to_string(),
    };
    let from = NaiveDate::from_ymd_opt(2022, 12, 31).unwrap();
    let to = NaiveDate::from_ymd_opt(2024, 5, 13).unwrap();
    let server = MockServer::start();
    server.mock(|when, then| {
        when.method(POST)
            .path(path)
            .body_contains("Card_Token")
            .body_contains(&card.id)
            .body_contains("FromDate")
            .body_contains("31-Dec-2022")
            .body_contains("ToDate")
            .body_contains("13-May-2024");
        then.status(200)
            .header("Content-Type", "text/html")
            .body(content);
    });

    let simplygo = simplygo_new(&server.base_url(), true);
    let got = simplygo.trips(&card, &from, &to);
    assert_eq!(got, content);
}
