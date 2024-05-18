# simplygo
`simplygo` is an Rust SDK for programming interfacing with the [Translink Simplygo](https://simplygo.transitlink.com.sg/) site.


## Features
- `SimplyGo` client: login with credentials, scrape HTML from SimplyGo site.
- `parsing` module: Parse scraped HTML from SimplyGo site into native rust structs.

## Installation
```bash
cargo add simplygo
```

## Usage
```rust
use simplygo::SimplyGo;
use simplygo::parsing::parse_trips;

let simplygo = SimplyGo::default().login(&args.username, &args.password);
let cards = simplygo.cards();
cards.iter().for_each(|card| {
    let html = simplygo.trips(card, NaiveDate::from_ymd(...), NaiveDate::from_ymd(...));
    let trips = parse_trips(&card.id, html)
});
```
## License
[MIT](https://choosealicense.com/licenses/mit/)
