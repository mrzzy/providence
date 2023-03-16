/*
 * Providence
 * SimplyGo Source
*/

use std::collections::HashMap;

use reqwest::{
    blocking::{Client, Request, Response},
    header::{HeaderMap, COOKIE},
    Method,
};
use scraper::{Html, Selector};

const SIMPLYGO_URL: &str = "https://simplygo.transitlink.com.sg";
const CSRF_KEY: &str = "__RequestVerificationToken";
const SESSION_ID_KEY: &str = "ASP.NET_SessionId";
const AUTH_TOKEN_KEY: &str = "AuthToken";

// Unit Tests
#[cfg(test)]
mod tests;

fn parse_cookies(cookies: &str) -> HashMap<&str, &str> {
    // split up multple cookies
    cookies
        .split(";")
        .map(|cookie| cookie.trim())
        // split cookie key & value
        .filter_map(|cookie| {
            let parts: Vec<_> = cookie.split("=").collect();
            parts.get(0).zip(parts.get(1)).map(|(&k, &v)| (k, v))
        })
        .collect()
}

/// Extract the value of the CSRF cookie from given SimplyGo homepage response headers
fn extract_csrf_cookie(headers: &HeaderMap) -> &str {
    // parse cookies from Set-Cookie http header
    let cookies_text = headers
        .get("Set-Cookie")
        .expect("Missing 'Set-Cookie' header in Simplygo homepage response.")
        .to_str()
        .expect("Could not parse value of 'Set-Cookie' header.");

    // get value of csrf cookie
    parse_cookies(cookies_text)
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
#[derive(Debug, Clone)]
struct CSRF {
    /// CSRF token to be submitted as a cookie.
    cookie: String,
    /// CSRF token to be submitted as a url encoded form data.
    form: String,
}
impl CSRF {
    /// Derive CSRF by scraping give SimplyGo homepage resposne
    fn from(homepage: Response) -> Self {
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
struct SimplyGo {
    http: Client,
    csrf: CSRF,
    session: Option<Session>,
}
impl SimplyGo {
    pub fn new() -> Self {
        let http = Client::new();
        let csrf = CSRF::from(
            http.get(SIMPLYGO_URL)
                .send()
                .expect("Failed to GET Simplygo homepage."),
        );
        Self {
            http,
            csrf,
            session: None,
        }
    }

    // Make a HTTP request with the given method & URL path to SimplyGo
    // Attaches CSRF & session tokens (if present) to the request.
    // Returns the Response on success, Error on failure.
    fn request(
        self,
        method: Method,
        url_path: &str,
        mut form_data: HashMap<String, String>,
    ) -> Request {
        // insert csrf token into form data
        form_data.insert(CSRF_KEY.to_owned(), self.csrf.form);

        let cookies = [
            // pass csrf token as cookie
            vec![(CSRF_KEY, self.csrf.cookie)],
            // pass auth & session id as cookies
            self.session.map_or(vec![], |session| {
                vec![(AUTH_TOKEN_KEY, session.auth), (SESSION_ID_KEY, session.id)]
            }),
        ]
        .concat();

        self.http
            .request(method, format!("{}{}", SIMPLYGO_URL, url_path))
            // build cookies header by expressing cookies in the format:
            // <KEY1>=<VALUE1>; <KEY2>=<VALUE2> ...
            .header(
                COOKIE,
                cookies
                    .into_iter()
                    .map(|(k, v)| format!("{}={}", k, v))
                    .collect::<Vec<_>>()
                    .join("; "),
            )
            .form(&form_data)
            .build()
            .expect("Failed to build SimplyGo request.")
    }
}

fn main() {
    let simplygo = SimplyGo::new();
    println!("{:?}", simplygo.csrf);
}
