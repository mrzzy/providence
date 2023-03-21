/*
 * Providence
 * SimplyGo Source
 * HTTP Utilities
*/

use std::collections::HashMap;

use reqwest::header::{HeaderMap, SET_COOKIE};

pub fn parse_set_cookies<'a>(headers: &'a HeaderMap) -> HashMap<&'a str, &'a str> {
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_set_cookies_test() {
        // header, value, expected
        let test_cases = [
            ("no-semicolon", "value", "value"),
            ("semicolon", "value;", "value"),
            (
                "semicolon-attributes",
                "value; SameSite=Lax Secure HttpOnly",
                "value",
            ),
            ("duplicate", "value1", "value2"),
            ("duplicate", "value2", "value2"),
        ];

        let mut headers = HeaderMap::new();
        for (key, value, _) in test_cases {
            headers.append(SET_COOKIE, format!("{}={}", key, value).parse().unwrap());
        }
        let set_cookies = parse_set_cookies(&headers);

        for (key, _, expected) in test_cases {
            assert_eq!(expected, set_cookies[key]);
        }
    }
}
