/*
 * Providence
 * SimplyGo Source
 * Unit Tests
*/

use std::fs::read_to_string;

use reqwest::{blocking::Client, header::SET_COOKIE};

use super::*;

const CSRF_TOKEN: &str = "_CSRF-TOKEN";
const SESSION_ID: &str = "_session_id";
const AUTH_TOKEN: &str = "_auth_token";

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

#[test]
fn parse_set_cookies_test() {
    // header, value, expected
    let test_cases = [
        ("no-semicolon", "value", "value"),
        ("semicolon", "value;", "value"),
        (
            "semicolon-attributes",
            "value; SameSite=Lax Secure HttpOnly",
            "value",
        ),
        ("duplicate", "value1", "value2"),
        ("duplicate", "value2", "value2"),
    ];

    let mut headers = HeaderMap::new();
    for (key, value, _) in test_cases {
        headers.append(SET_COOKIE, format!("{}={}", key, value).parse().unwrap());
    }
    let set_cookies = parse_set_cookies(&headers);

    for (key, _, expected) in test_cases {
        assert_eq!(expected, set_cookies[key]);
    }
}

#[test]
fn extract_csrf_cookie_test() {
    let mut headers = HeaderMap::new();
    headers.insert(
        SET_COOKIE,
        format!(
            "__RequestVerificationToken={}; path=/; secure; HttpOnly",
            CSRF_TOKEN
        )
        .parse()
        .unwrap(),
    );
    assert_eq!(CSRF_TOKEN, extract_csrf_cookie(&headers));
}

#[test]
fn extract_csrf_form_test() {
    let html = read_to_string(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/resources/simplygo_homepage.html"
    ))
    .unwrap();
    assert_eq!(CSRF_TOKEN, extract_csrf_form(&html));
}

#[test]
fn simplygo_request_test() {
    for has_session in [true, false] {
        let simplygo = SimplyGo {
            http: Client::new(),
            csrf: CSRF {
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
        };
        let request = simplygo
            .request(Method::GET, "/test", HashMap::new())
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
