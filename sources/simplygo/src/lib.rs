/*
 * Providence
 * SimplyGo Source
 * SimplyGo Client
*/

mod csrf;
mod http;
pub mod models;
mod parsing;
#[cfg(test)]
mod tests;

use std::collections::HashMap;

use crate::http::parse_set_cookies;
use chrono::NaiveDate;
use csrf::{CSRF, CSRF_KEY};
use models::{Card, Trip};
use parsing::{parse_cards, parse_trips};
use reqwest::{
    blocking::{multipart::Form, Client, RequestBuilder},
    header::COOKIE,
    redirect::Policy,
    Method,
};

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
    http: Client,
    csrf: CSRF,
    session: Option<Session>,
}
impl SimplyGo {
    pub fn new() -> Self {
        let http = Client::builder().redirect(Policy::none()).build().unwrap();
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

    /// Make a HTTP request builder with the given method & URL path to SimplyGo
    /// Attaches CSRF & session tokens (if present) to the request.
    /// Returns the Response on success, Error on failure.
    fn request(&self, method: Method, url_path: &str) -> RequestBuilder {
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
    }

    /// Make a HTTP request with form data with the given method & URL path to SimplyGo.
    /// Similar to `request()`, but passes form data as multipart encoded parts.
    fn request_form(
        &self,
        method: Method,
        url_path: &str,
        form_data: HashMap<&str, &str>,
    ) -> RequestBuilder {
        // embed form data into multipart form text fields
        let login_form = form_data
            .into_iter()
            .fold(Form::new(), |form, (key, value)| {
                form.text(key.to_owned(), value.to_owned())
            })
            // insert csrf token into form data
            .text(CSRF_KEY, self.csrf.form.clone());

        self.request(method, url_path).multipart(login_form)
    }

    /// Login on SimplyGo with the given credentials.
    /// Username is typically a mobile number.
    /// Returns an authenciated version of this client.
    pub fn login(self, username: &str, password: &str) -> Self {
        let response = self
            .request_form(
                Method::POST,
                "/Account/Complete",
                HashMap::from([("Username", username), ("Password", password)]),
            )
            .send()
            .expect("Failed to authenticate on Simplygo with username & password.");

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

    /// Scrape the ids of SimplyGo registered bank card from /Cards/Transactions page
    pub fn cards(&self) -> Vec<Card> {
        let url_path = "/Cards/Transactions";
        parse_cards(
            &self
                .request(Method::GET, url_path)
                .send()
                .expect(&format!("Failed to get SimplyGo's {} page.", url_path))
                .text()
                .expect(&format!(
                    "Could not decode SimplyGo's {} page as HTML.",
                    url_path
                )),
        )
    }

    /// Scrape Trips made on the given bank card in the time period starting
    /// on `from` &amp; toing on `to` dates.
    pub fn trips(&self, card: &Card, from: &NaiveDate, to: &NaiveDate) -> Vec<Trip> {
        // build request multipart form with params
        let date_fmt = "%d-%b-%Y";

        let url_path = "/Cards/GetTransactions";
        parse_trips(
            &self
                .request_form(
                    Method::POST,
                    url_path,
                    HashMap::from([
                        ("Card_Token", card.id.as_str()),
                        ("FromDate", format!("{}", from.format(date_fmt)).as_str()),
                        ("ToDate", format!("{}", to.format(date_fmt)).as_str()),
                    ]),
                )
                .send()
                .expect(&format!(
                    "Failed to Get Transactions for Card {} from SimplyGo's {} page.",
                    card.id, url_path
                ))
                .text()
                .expect(&format!(
                    "Could not decode SimplyGo's {} page as HTML.",
                    url_path
                )),
        )
    }
}
