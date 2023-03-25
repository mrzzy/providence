/*
 * Providence
 * SimplyGo Source
 * Unit Tests
*/
use std::collections::HashMap;

use reqwest::{blocking::Client, header::HeaderMap};

use crate::csrf::{Csrf, CSRF_KEY};

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
#[test]
fn simplygo_request_test() {
    for has_session in [true, false] {
        let simplygo = SimplyGo {
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
        };
        let request = simplygo.request(Method::GET, "/test").build().unwrap();

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
