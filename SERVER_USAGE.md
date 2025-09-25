# TradingHours API Server

The TradingHours Python package now includes a built-in REST API server powered by FastAPI. This allows you to expose the TradingHours data via HTTP endpoints for use by applications written in any programming language.

## Installation

To use the server functionality, install the package with server dependencies:

```bash
pip install tradinghours[server]
```

This installs the additional dependencies: `fastapi`, `uvicorn[standard]`, and `gunicorn`.

## Basic Usage

### Start the Development Server

```bash
# Basic server on localhost:8000
tradinghours serve

# Custom host and port
tradinghours serve --host 0.0.0.0 --port 3000

# Development mode with auto-reload
tradinghours serve --reload
```

### Production Deployment

```bash
# Production with multiple workers (uvicorn)
tradinghours serve --workers 4 --host 0.0.0.0

# Production with gunicorn (recommended for high load)
tradinghours serve --workers 4 --server-type gunicorn --host 0.0.0.0

# Unix Domain Socket (enterprise deployment)
tradinghours serve --uds /var/run/tradinghours/api.sock --workers 4 --server-type gunicorn
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--host` | Host to bind to | `127.0.0.1` |
| `--port` | Port to bind to | `8000` |
| `--uds` | Unix domain socket path (overrides host/port) | None |
| `--workers` | Number of worker processes | `1` |
| `--server-type` | Server type: `uvicorn` or `gunicorn` | `uvicorn` |
| `--reload` | Auto-reload on code changes (development) | `False` |
| `--log-level` | Log level: `debug`, `info`, `warning`, `error` | `info` |

## API Endpoints

Once the server is running, you can access these endpoints:

### Health & Info
- `GET /health` - Health check
- `GET /info` - API information and statistics
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

### Markets
- `GET /markets` - List all markets
- `GET /markets?subset=US.*` - Filter markets by FinID pattern
- `GET /markets/{identifier}` - Get market by FinID or MIC
- `GET /markets/{identifier}/holidays?start=2024-01-01&end=2024-12-31` - Market holidays
- `GET /markets/{identifier}/phases?start=2024-01-01&end=2024-01-31` - Market phases
- `GET /markets/{identifier}/schedules` - Market schedules
- `GET /markets/{identifier}/status` - Current market status
- `GET /markets/{identifier}/status?datetime=2024-01-01T12:00:00-05:00` - Status at specific time

### Currencies
- `GET /currencies` - List all currencies
- `GET /currencies/{code}` - Get currency by code
- `GET /currencies/{code}/holidays?start=2024-01-01&end=2024-12-31` - Currency holidays

## Example Usage

### Using curl

```bash
# List first few markets
curl "http://localhost:8000/markets" | head

# Get NYSE market info
curl "http://localhost:8000/markets/US.NYSE"

# Get NYSE holidays for 2024
curl "http://localhost:8000/markets/US.NYSE/holidays?start=2024-01-01&end=2024-12-31"

# Get current NYSE status
curl "http://localhost:8000/markets/US.NYSE/status"

# List currencies
curl "http://localhost:8000/currencies"
```

### Using Python requests

```python
import requests

# Get market info
response = requests.get("http://localhost:8000/markets/US.NYSE")
market = response.json()
print(f"Market: {market['exchange_name']}")

# Get holidays
response = requests.get(
    "http://localhost:8000/markets/US.NYSE/holidays",
    params={"start": "2024-01-01", "end": "2024-12-31"}
)
holidays = response.json()
print(f"Found {len(holidays)} holidays")

# Get current status
response = requests.get("http://localhost:8000/markets/US.NYSE/status")
status = response.json()
print(f"Market status: {status['status']}")
```

### Using JavaScript/Node.js

```javascript
// Get market info
const response = await fetch('http://localhost:8000/markets/US.NYSE');
const market = await response.json();
console.log(`Market: ${market.exchange_name}`);

// Get holidays
const holidayResponse = await fetch(
    'http://localhost:8000/markets/US.NYSE/holidays?start=2024-01-01&end=2024-12-31'
);
const holidays = await holidayResponse.json();
console.log(`Found ${holidays.length} holidays`);
```

## Production Deployment

### With Nginx + Unix Socket

1. Start the server with UDS:
```bash
tradinghours serve --uds /var/run/tradinghours/api.sock --workers 4 --server-type gunicorn
```

2. Configure Nginx:
```nginx
upstream tradinghours_api {
    server unix:/var/run/tradinghours/api.sock;
}

server {
    listen 80;
    server_name api.tradinghours.internal;
    
    location / {
        proxy_pass http://tradinghours_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### As a Systemd Service

Create `/etc/systemd/system/tradinghours-api.service`:

```ini
[Unit]
Description=TradingHours API Server
After=network.target

[Service]
Type=exec
User=tradinghours
Group=tradinghours
WorkingDirectory=/opt/tradinghours
Environment=TRADINGHOURS_TOKEN=your-token-here
ExecStart=/opt/tradinghours/venv/bin/tradinghours serve --uds /var/run/tradinghours/api.sock --workers 4 --server-type gunicorn
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable tradinghours-api
sudo systemctl start tradinghours-api
```

## Performance Notes

- **uvicorn**: Good for development and simple production use
- **gunicorn + uvicorn workers**: Better for high-load production environments
- **Multiple workers**: Improves performance for concurrent requests
- **Unix Domain Sockets**: Faster than TCP for local communication and more secure

## Error Handling

The API returns appropriate HTTP status codes:

- `200 OK` - Successful request
- `400 Bad Request` - Invalid parameters (e.g., bad date format)
- `403 Forbidden` - Access denied (insufficient permissions)
- `404 Not Found` - Resource not found (market/currency doesn't exist)
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Database not ready

## Troubleshooting

### Server won't start
- Ensure you have the server dependencies: `pip install tradinghours[server]`
- Check that the port isn't already in use
- For UDS, ensure the directory exists and is writable

### No data available
- Run `tradinghours import` first to download data
- Check that your API token is valid: `tradinghours status`

### Performance issues
- Use multiple workers: `--workers 4`
- Use gunicorn for production: `--server-type gunicorn`
- Consider using Unix domain sockets for local communication
