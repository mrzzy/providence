/*
 * Providence
 * SimplyGo Source
 * CSRF Token
*/

use reqwest::{blocking::Response, header::HeaderMap};
use scraper::{Html, Selector};

use crate::http::parse_set_cookies;

pub const CSRF_KEY: &str = "__RequestVerificationToken";

/// Extract the value of the CSRF cookie from given SimplyGo homepage response headers
fn extract_csrf_cookie(headers: &HeaderMap) -> &str {
    // get value of csrf cookie
    parse_set_cookies(headers)
        .get(CSRF_KEY)
        .copied()
        .expect("Expected cookie with CSRF token is missing.")
}

/// Extract the value of the CSRF form input from the given SimplyGo homepage html
fn extract_csrf_form(html: &str) -> String {
    let document = Html::parse_document(html);
    // find <input> tag with the csrf token
    let inputs = document
        .select(&Selector::parse(&format!("input[name=\"{}\"]", CSRF_KEY)).unwrap())
        .take(1)
        .collect::<Vec<_>>();
    // extract token from value attribute of <input> tag
    inputs
        .get(0)
        .expect("Could not locate <input> element for form CSRF token.")
        .value()
        .attr("value")
        .expect("Expected <input> element to have a 'value' attribute")
        .to_owned()
}

/// CSRF Tokens to be submitted in requests to SimplyGo.
#[derive(Debug)]
pub struct Csrf {
    /// CSRF token to be submitted as a cookie.
    pub cookie: String,
    /// CSRF token to be submitted as a url encoded form data.
    pub form: String,
}
impl Csrf {
    /// Derive CSRF by scraping give SimplyGo homepage resposne
    pub fn from(homepage: Response) -> Self {
        Self {
            cookie: extract_csrf_cookie(homepage.headers()).to_owned(),
            form: extract_csrf_form(
                &homepage
                    .text()
                    .expect("Could not parse SimplyGo homepage as text."),
            ),
        }
    }
}

#[cfg(test)]
mod tests {

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
}
