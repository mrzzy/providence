/*
 * Providence
 * Simplygo Source
*/

use std::collections::HashMap;

use reqwest::blocking::Client;
use scraper::{Html, Selector};

const SIMPLYGO_URL: &str = "https://simplygo.transitlink.com.sg";
const CSRF_KEY: &str = "__RequestVerificationToken";

/// CSRF Tokens to be submitted in requests to SimplyGo.
#[derive(Debug)]
struct CSRF {
    /// CSRF token to be submitted as a cookie.
    cookie: String,
    /// CSRF token to be submitted as a url encoded form data.
    form: String,
}
/// Scrape CSRF tokens by scraping the response from requesting the SimplyGo homepage
fn scrape_csrf(http: &Client) -> CSRF {
    let response = http
        .get(SIMPLYGO_URL)
        .send()
        .expect("Failed to GET Simplygo homepage.");

    // parse cookies from Set-Cookie http header
    let headers = response.headers().to_owned();
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

    // parse homepage for <input> element with form csrf token
    let document = Html::parse_document(
        &response
            .text()
            .expect("Could not parse SimplyGo homepage as text."),
    );
    let input = document
        .select(&Selector::parse(&format!("input[name=\"{}\"]", CSRF_KEY)).unwrap())
        .take(1)
        .collect::<Vec<_>>()
        .get(0)
        .expect("Could not locate <input> element for form CSRF token.")
        .value();

    CSRF {
        cookie: cookies
            .get(CSRF_KEY)
            .map(|&v| v)
            .expect("Expected cookie with CSRF token is missing.")
            .to_owned(),
        form: input
            .attr("value")
            .expect("Expected <input> element to have a 'value' attribute")
            .to_owned(),
    }
}

/// Represents a SimplyGo session.
struct Session {
    http: Client,
    csrf: CSRF,
    auth: Option<String>,
}
impl Session {
    pub fn new() -> Self {
        let http = Client::new();
        let csrf = scrape_csrf(&http);
        Self {
            http,
            csrf,
            auth: None,
        }
    }
}

fn main() {
    let simplygo = Session::new();
    println!("{:?}", simplygo.csrf);
}
