/*
 * Providence
 * SimplyGo Source
 * SimplyGo Client
*/

mod csrf;
mod http;
pub mod models;
pub mod parsing;
#[cfg(test)]
mod tests;

use std::collections::HashMap;
use std::time::Duration;

use chrono::NaiveDate;
use csrf::{Csrf, CSRF_KEY};
use http::parse_set_cookies;
use reqwest::{
    blocking::{multipart::Form, Client, RequestBuilder},
    header::COOKIE,
    redirect::Policy,
    Method, StatusCode,
};

use self::{models::Card, parsing::parse_cards};
const SIMPLYGO_URL: &str = "https://simplygo.transitlink.com.sg";
const SESSION_ID_KEY: &str = "ASP.NET_SessionId";
const AUTH_TOKEN_KEY: &str = "AuthToken";

/// Defines an authenticated session on SimplyGo
#[derive(Debug)]
struct Session {
    id: String,
    auth: String,
}

/// SimplyGo client
#[derive(Debug)]
pub struct SimplyGo {
    base_url: String,
    http: Client,
    csrf: Csrf,
    session: Option<Session>,
}
impl SimplyGo {
    pub fn new(base_url: &str) -> Self {
        let http = Client::builder()
            .timeout(Some(Duration::from_secs(60)))
            .redirect(Policy::none())
            .build()
            .unwrap();
        let csrf = Csrf::from(
            http.get(base_url)
                .send()
                .expect("Failed to GET Simplygo homepage."),
        );
        Self {
            base_url: base_url.to_string(),
            http,
            csrf,
            session: None,
        }
    }

    /// Make a HTTP request builder with the given method & URL path to SimplyGo
    /// Attaches CSRF & session tokens (if present) to the request.
    /// Attaches multipart form data (if present) to the request.
    /// Returns the request builder.
    fn request(
        &self,
        method: Method,
        url_path: &str,
        form_data: HashMap<&str, &str>,
    ) -> RequestBuilder {
        let cookies = [
            // pass csrf token as cookie
            vec![(CSRF_KEY, &self.csrf.cookie)],
            // pass auth & session id as cookies
            self.session.as_ref().map_or(vec![], |session| {
                vec![
                    (AUTH_TOKEN_KEY, &session.auth),
                    (SESSION_ID_KEY, &session.id),
                ]
            }),
        ]
        .concat();

        let request = self
            .http
            .request(method, format!("{}{}", self.base_url, url_path))
            // build cookies header by expressing cookies in the format:
            // <KEY1>=<VALUE1>; <KEY2>=<VALUE2> ...
            .header(
                COOKIE,
                cookies
                    .into_iter()
                    .map(|(k, v)| format!("{}={}", k, v))
                    .collect::<Vec<_>>()
                    .join("; "),
            );

        // attach multipart form data if given
        if form_data.len() > 0 {
            let login_form = form_data
                .into_iter()
                .fold(Form::new(), |form, (key, value)| {
                    form.text(key.to_owned(), value.to_owned())
                })
                // insert csrf token into form data
                .text(CSRF_KEY, self.csrf.form.clone());
            return request.multipart(login_form);
        }
        request
    }

    // Execute the given request and scrape the given HTML
    fn scrape(&self, request: RequestBuilder) -> String {
        let request = request
            .build()
            .unwrap_or_else(|e| panic!("Failed to build request: {}", e));
        let path = request.url().path().to_string();
        self.http
            .execute(request)
            .unwrap_or_else(|e| {
                panic!(
                    "Failed to perform request to scrape SimplyGo page: {}: {}",
                    path, e
                )
            })
            .text()
            .unwrap_or_else(|e| panic!("Could not decode SimplyGo page as HTML: {}: {}", path, e,))
    }

    /// Login on SimplyGo with the given credentials.
    /// Username is typically a mobile number.
    /// Returns an authenticated version of this client.
    pub fn login(self, username: &str, password: &str) -> Self {
        let response = self
            .request(
                Method::POST,
                "/Account/Complete",
                HashMap::from([("Username", username), ("Password", password)]),
            )
            .send()
            .expect("Could not make authentication request to Simplygo.");

        // check whether authentication was successful via http status code
        // if authenticated, simplygo will perform a FOUND 302 redirect
        if response.status() != StatusCode::FOUND {
            panic!("Failed to authenticate on Simplygo with username & password.");
        }

        let cookies = parse_set_cookies(response.headers());
        Self {
            session: Some(Session {
                id: (*cookies
                    .get(SESSION_ID_KEY)
                    .expect("Expected Session ID to be present in set cookies"))
                .to_owned(),
                auth: (*cookies
                    .get(AUTH_TOKEN_KEY)
                    .expect("Expected Auth Token to be present in set cookies"))
                .to_owned(),
            }),
            ..self
        }
    }

    /// Scrape the SimplyGo registered Cards from /Cards/Transactions page
    pub fn cards(&self) -> Vec<Card> {
        parse_cards(&self.scrape(self.request(Method::GET, "/Cards/Transactions", HashMap::new())))
    }

    /// Scrape Trips listing HTML made on the given Card in the time period starting
    /// on `from` &amp; to `to` dates.
    /// Returns the scrapped HTML.
    pub fn trips(&self, card: &Card, from: &NaiveDate, to: &NaiveDate) -> String {
        // build request multipart form with params
        let date_fmt = "%d-%b-%Y";
        self.scrape(self.request(
            Method::POST,
            "/Cards/GetTransactions",
            HashMap::from([
                ("Card_Token", card.id.as_str()),
                ("FromDate", format!("{}", from.format(date_fmt)).as_str()),
                ("ToDate", format!("{}", to.format(date_fmt)).as_str()),
            ]),
        ))
    }
}
impl Default for SimplyGo {
    fn default() -> Self {
        Self::new(SIMPLYGO_URL)
    }
}
