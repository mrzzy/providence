/*
 * Providence
 * SimplyGo Source
*/

use chrono::NaiveDate;
use simplygo_src::SimplyGo;
use std::{collections::HashMap, env};

fn main() {
    let simplygo = SimplyGo::new().login(
        &env::var("SIMPLYGO_SRC_USERNAME").unwrap(),
        &env::var("SIMPLYGO_SRC_PASSWORD").unwrap(),
    );
    println!("{:?}", simplygo);
    let cards: HashMap<_, _> = simplygo
        .cards()
        .into_iter()
        .map(|c| (c.id.clone(), c))
        .collect();
    println!("{:?}", cards);
    println!(
        "{:?}",
        simplygo.trips(
            &cards["9b3R6d4S7c8J2a1U8v8W"],
            &NaiveDate::from_ymd_opt(2023, 2, 1).unwrap(),
            &NaiveDate::from_ymd_opt(2023, 3, 3).unwrap()
        )
    );
}
