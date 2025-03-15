# Clash Prometheus Exporter
Prometheus exporter for [Clash For Windows](https://github.com/Fndroid/clash_for_windows_pkg). Uses the API to get online proxy servers and their latency.

# Install
```bash
pip install -r requirements.txt
```

# Usage
```bash
cp .env.example .env
```
Edit `.env` file and set the `CLASH_HOST`, `CLASH_PORT`, and `CLASH_API_KEY` to your Clash config.
You can get `CLASH_API_KEY` from `%userprofile%\.config\clash\config.yaml` file.


### Run
```bash
python main.py
```
Go to `http://localhost:8000/metrics` to see the metrics.
If you run this on a different host than Prometheus change `HTTP_HOST` to `0.0.0.0`.

# Metrics
- `proxy_latency` - Latency of the proxy servers in milliseconds.
- `proxy_online` - Proxy servers that are online.