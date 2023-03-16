/*
 * Providence
 * SimplyGo Source
*/

use std::collections::HashMap;

use reqwest::{
    blocking::{Client, Response, RequestBuilder},
    header::{HeaderMap, self}, Request,
};
use scraper::{Html, Selector};

const SIMPLYGO_URL: &str = "https://simplygo.transitlink.com.sg";
const CSRF_KEY: &str = "__RequestVerificationToken";

// Unit Tests
#[cfg(test)]
mod tests;

/// Extract the value of the CSRF cookie from given SimplyGo homepage response headers
fn extract_csrf_cookie(headers: &HeaderMap) -> &str {
    // parse cookies from Set-Cookie http header
    let cookies: HashMap<_, _> = headers
        .get("Set-Cookie")
        .expect("Missing 'Set-Cookie' header in Simplygo homepage response.")
        .to_str()
        .expect("Could not parse value of 'Set-Cookie' header.")
        // split up multple cookies
        .split(";")
        .map(|cookie| cookie.trim())
        // split cookie key & value
        .filter_map(|cookie| {
            let parts: Vec<_> = cookie.split("=").collect();
            parts.get(0).zip(parts.get(1)).map(|(&k, &v)| (k, v))
        })
        .collect();

    // get value of csrf cookie
    cookies
        .get(CSRF_KEY)
        .map(|&v| v)
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
struct CSRF {
    /// CSRF token to be submitted as a cookie.
    cookie: String,
    /// CSRF token to be submitted as a url encoded form data.
    form: String,
}
impl CSRF {
    /// Derive CSRF by scraping give SimplyGo homepage resposne
    fn from(homepage: &Response) -> Self {
        Self {
            cookie: extract_csrf_cookie(&homepage.headers()).to_owned(),
            form: extract_csrf_form(
                &homepage
                    .text()
                    .expect("Could not parse SimplyGo homepage as text."),
            ),
        }
    }
}


// Defines an authenticated session on Simplygo
struct Session {
    id: String,
    auth: String,
}

/// SimplyGo client
struct Client {
    http: Client,
    csrf: CSRF,
    session: Option<Session>,
}
impl Client {
    pub fn new() -> Self {
        let http = Client::new();
        let csrf = CSRF::from(http
            .get(SIMPLYGO_URL)
            .send()
            .expect("Failed to GET Simplygo homepage."));
        Self {
            http,
            csrf,
            session: None,
        }
    }
}

fn main() {
    let simplygo = Client::new();
    println!("{:?}", simplygo.csrf);
}
