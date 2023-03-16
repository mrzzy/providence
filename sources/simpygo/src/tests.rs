/*
 * Providence
 * SimplyGo Source
 * Unit Tests
*/

use std::fs::read_to_string;

use reqwest::header::SET_COOKIE;

use super::*;

const CSRF_TOKEN: &str = "_CSRF-TOKEN";

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
