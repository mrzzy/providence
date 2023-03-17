/*
 * Providence
 * SimplyGo Source
 * Unit Tests
*/

use std::{fs::read_to_string, str::from_utf8};

use reqwest::{blocking::Client, header::SET_COOKIE};

use super::*;

const CSRF_TOKEN: &str = "_CSRF-TOKEN";
const SESSION_ID: &str = "_session_id";
const AUTH_TOKEN: &str = "_auth_token";

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
        let request = simplygo.request(Method::GET, "/test", HashMap::new());

        // parse cookies from 'Cookie' http header
        let cookies = parse_cookies(request.headers().get("Cookie").unwrap().to_str().unwrap());
        // parse url encoded form data in request body
        let body = from_utf8(request.body().unwrap().as_bytes().unwrap()).unwrap();
        let form_data: HashMap<_, _> = body
            .split('&')
            .map(|entry| entry.split('=').collect::<Vec<_>>())
            .map(|key_value| (key_value[0], key_value[1]))
            .collect();

        // test: http method & url
        assert_eq!(format!("{}/test", SIMPLYGO_URL), request.url().as_str());
        assert_eq!(Method::GET, request.method());
        // test: csrf tokens are attached in form data & cookies
        assert_eq!(CSRF_TOKEN, form_data[CSRF_KEY]);
        assert_eq!(CSRF_TOKEN, cookies[CSRF_KEY]);
        if has_session {
            // test: session id & auth token attached in cookies
            assert_eq!(SESSION_ID, cookies[SESSION_ID_KEY]);
            assert_eq!(AUTH_TOKEN, cookies[AUTH_TOKEN_KEY]);
        }
    }
}
