/*
 * Providence
 * SimplyGo Source
 * SimplyGo Client
*/

use std::collections::HashMap;

use reqwest::{
    blocking::{multipart::Form, Client, RequestBuilder, Response},
    header::{HeaderMap, COOKIE, SET_COOKIE},
    redirect::Policy,
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

// Parse Cookies from Set-Cookies headers in the given http headers
fn parse_set_cookies<'a>(headers: &'a HeaderMap) -> HashMap<&'a str, &'a str> {
    headers
        .get_all(SET_COOKIE)
        .into_iter()
        .map(|header| {
            header
                .to_str()
                .expect("Failed to parse Set-Cookie HTTP header")
        })
        // split key value
        .map(|set_cookie| {
            set_cookie
                .split_once("=")
                .expect("Expected Set-Cookie key & value to separated by '='")
        })
        // trim attributes after ';' from value.
        .map(|(k, value)| {
            (
                k,
                match value.find(';') {
                    Some(position) => &value[..position],
                    None => value,
                },
            )
        })
        .collect()
}

/// Extract the value of the CSRF cookie from given SimplyGo homepage response headers
fn extract_csrf_cookie(headers: &HeaderMap) -> &str {
    // get value of csrf cookie
    parse_set_cookies(headers)
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

    // Make a HTTP request builder with the given method & URL path to SimplyGo
    // Attaches CSRF & session tokens (if present) to the request.
    // Returns the Response on success, Error on failure.
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

        // embed form data into form
        let login_form = form_data
            .into_iter()
            .fold(Form::new(), |form, (key, value)| {
                form.text(key.to_owned(), value.to_owned())
            })
            // insert csrf token into form data
            .text(CSRF_KEY, self.csrf.form.clone());

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
            .multipart(login_form)
    }
    // Login on SimplyGo with the given credentials.
    // Username is typically a mobile number.
    // Returns an authenciated version of this client.
    pub fn login(self, username: &str, password: &str) -> Self {
        let response = self
            .request(
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
}
