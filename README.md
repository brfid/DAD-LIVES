# DAD-LIVES

Pi-hole companion that replaces blocked HTTP ad slots with dad wisdom — inspired by [They Live](https://en.wikipedia.org/wiki/They_Live).

When Pi-hole blocks an ad domain and redirects the request to your Pi's IP, this server intercepts it and returns a stark black-and-white SVG or HTML page with a slogan. Works best on smart TVs, streaming sticks, and older apps that still fetch ads over HTTP.

> **HTTPS ads:** Pi-hole still blocks them at DNS. They disappear — no replacement. Intercepting HTTPS requires MITM (mitmproxy + CA cert on each device), which is out of scope here.

## Prerequisites

- Pi-hole v6 running on the same host
- Python 3.9+, `flask` (`pip install flask`)

## Setup

### 1. Configure Pi-hole

In `/etc/pihole/pihole.toml`:

```toml
# Move the Pi-hole web UI off port 80
[webserver]
  port = "8090,[::]:8090"

# Redirect blocked domains to this Pi's IP (instead of 0.0.0.0)
[dns.blocking]
  mode = "IP"
```

Restart: `sudo systemctl restart pihole-FTL`

Pi-hole admin UI moves to `http://<pi-ip>:8090/admin`.

### 2. Install the server

```bash
git clone https://github.com/brfid/DAD-LIVES
cd dad-lives
```

Edit `dad-lives.service` — replace both `/path/to/dad-lives` with your clone path, then:

```bash
sudo cp dad-lives.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now dad-lives
```

## Slogans

Edit the `SLOGANS` list at the top of `server.py` and restart the service, or use the admin UI at `http://<pi-ip>/admin` to add/remove at runtime.

Runtime changes are stored in `state.json` (gitignored). Delete it to reset to defaults.

## Tests

```bash
pytest test_server.py
```

## License

MIT
