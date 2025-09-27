"""Production-ready FastAPI server for TradingHours API."""
import os
import sys, time
import logging
import logging.handlers
from datetime import datetime, date
from typing import Optional
from pathlib import Path
import io

try:
    from fastapi import FastAPI, HTTPException, Query, Depends, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from fastapi.responses import JSONResponse
except ImportError:
    raise ImportError(
        "Server dependencies not installed. Run: pip install tradinghours[server]"
    )

from .market import Market
from .currency import Currency
from .store import db
from .exceptions import NoAccess, NotCovered, MICDoesNotExist, DateNotAvailable, InvalidType, InvalidValue
from .config import main_config
from . import __version__

def configure_logging():
    """Configure logging based on tradinghours.ini settings."""
    log_level_str = main_config.get("server-mode", "log_level").upper()
    log_folder = main_config.get("server-mode", "log_folder")
    log_days_to_keep = main_config.getint("server-mode", "log_days_to_keep")
    
    # Convert string log level to logging constant
    log_level = getattr(logging, log_level_str)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove any existing handlers
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)

    # Create logs directory if it doesn't exist
    logs_path = Path(log_folder)
    logs_path.mkdir(parents=True, exist_ok=True)
    
    # Create log file path with daily rotation
    log_file_path = logs_path / "th_server.log"
    
    # Use TimedRotatingFileHandler for daily rotation
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=str(log_file_path),
        when='midnight',
        interval=1,
        backupCount=log_days_to_keep,
        encoding='utf-8'
    )
    # Set suffix for rotated files (YYYY-MM-DD format)
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers to use our handlers
    # Gunicorn loggers
    gunicorn_logger = logging.getLogger('gunicorn')
    gunicorn_logger.handlers = []
    gunicorn_logger.propagate = True
    
    gunicorn_error_logger = logging.getLogger('gunicorn.error')
    gunicorn_error_logger.handlers = []
    gunicorn_error_logger.propagate = True
    
    gunicorn_access_logger = logging.getLogger('gunicorn.access')
    gunicorn_access_logger.handlers = []
    gunicorn_access_logger.propagate = True
    
    # Uvicorn loggers
    uvicorn_logger = logging.getLogger('uvicorn')
    uvicorn_logger.handlers = []
    uvicorn_logger.propagate = True
    
    uvicorn_access_logger = logging.getLogger('uvicorn.access')
    uvicorn_access_logger.handlers = []
    uvicorn_access_logger.propagate = True
    
    uvicorn_error_logger = logging.getLogger('uvicorn.error')
    uvicorn_error_logger.handlers = []
    uvicorn_error_logger.propagate = True


class LogCapture(io.TextIOWrapper):
    """Custom stream to capture stdout/stderr and send to our logger."""
    def __init__(self, original_stream, logger_name):
        self.original_stream = original_stream
        self.logger = logging.getLogger(logger_name)
        
    def write(self, text):
        # Write to original stream (console)
        # self.original_stream.write(text)
        # self.original_stream.flush()
        
        # Also log to our files (strip newlines since logger adds them)
        text = text.strip()
        if text:  # Only log non-empty lines
            self.logger.info(text)
        
    def flush(self):
        self.original_stream.flush()
        
    def __getattr__(self, name):
        return getattr(self.original_stream, name)


# Configure logging
configure_logging()
logger = logging.getLogger(__name__)

# Capture stdout/stderr to also log to our files
original_stdout = sys.stdout
original_stderr = sys.stderr
sys.stdout = LogCapture(original_stdout, "gunicorn.stdout")
sys.stderr = LogCapture(original_stderr, "gunicorn.stderr")

# Access logger for HTTP requests
access_logger = logging.getLogger("tradinghours.access")

# Create FastAPI app
app = FastAPI(
    title="TradingHours API",
    description="REST API for TradingHours market and currency data",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Custom logging middleware for access logs
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    method = request.method
    url = str(request.url)
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        process_time = time.time() - start_time
        access_logger.error(
            f"{client_ip} - {method} {url} - ERROR - {process_time:.3f}s - {type(e).__name__}: {str(e)}"
        )
        raise
    
    process_time = time.time() - start_time    
    access_logger.info(
        f"{client_ip} - {method} {url} - {status_code} - {process_time:.3f}s"
    )
    return response

# Security middleware for production
allowed_hosts = main_config.get("server-mode", "allowed_hosts").split(",")
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=allowed_hosts
)

# CORS middleware (configure for production)  
allowed_origins = main_config.get("server-mode", "allowed_origins").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Database dependency
async def get_db():
    """Database dependency to ensure DB is ready."""
    try:
        db.ready()
        return db
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database not ready: {str(e)}")

# Custom JSON encoder for datetime objects
class CustomJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        # Handle datetime serialization
        def serialize_datetime(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: serialize_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_datetime(item) for item in obj]
            return obj
        
        if content is not None:
            content = serialize_datetime(content)
        return super().render(content)

# Override default response class
app.response_class = CustomJSONResponse

# Exception handlers
@app.exception_handler(NoAccess)
async def no_access_handler(request, exc):
    logger.warning(f"Access denied for {request.url}: {exc}")
    raise HTTPException(status_code=403, detail=str(exc))

@app.exception_handler(NotCovered)
async def not_covered_handler(request, exc):
    logger.info(f"Resource not found for {request.url}: {exc}")
    raise HTTPException(status_code=404, detail=str(exc))

@app.exception_handler(MICDoesNotExist)
async def mic_not_exist_handler(request, exc):
    logger.info(f"MIC not found for {request.url}: {exc}")
    raise HTTPException(status_code=404, detail=str(exc))

@app.exception_handler(DateNotAvailable)
async def date_not_available_handler(request, exc):
    logger.warning(f"Date not available for {request.url}: {exc}")
    raise HTTPException(status_code=400, detail=str(exc))

@app.exception_handler(InvalidType)
async def invalid_type_handler(request, exc):
    logger.warning(f"Invalid type for {request.url}: {exc}")
    raise HTTPException(status_code=400, detail=str(exc))

@app.exception_handler(InvalidValue)
async def invalid_value_handler(request, exc):
    logger.warning(f"Invalid value for {request.url}: {exc}")
    raise HTTPException(status_code=400, detail=str(exc))


# Health and info endpoints
@app.get("/health")
async def health_check(db=Depends(get_db)):
    """Health check endpoint."""
    return {
        "status": "healthy", 
        "message": "TradingHours API is running",
        "version": __version__
    }

@app.get("/info")
async def api_info(db=Depends(get_db)):
    """API information and statistics."""
    try:
        num_markets, num_currencies = db.get_num_covered()
        local_timestamp = db.get_local_timestamp()
        
        return {
            "api_version": __version__,
            "total_markets": num_markets,
            "total_currencies": num_currencies,
            "last_data_update": local_timestamp.isoformat() if local_timestamp else None,
            "access_level": db.access_level.value if db.access_level else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting API info: {str(e)}")

# Market endpoints
@app.get("/markets", summary="List markets")
async def list_markets(
    subset: str = Query("*", description="Filter markets by FinID pattern (e.g., 'US.*')"),
    db=Depends(get_db)
):
    """List all available markets with optional filtering."""
    try:
        markets = Market.list_all(subset)
        logger.info(f"Listed {len(markets)} markets with subset '{subset}'")
        return [market.to_dict() for market in markets]
    except Exception as e:
        logger.error(f"Error listing markets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/markets/{identifier}", summary="Get market")
async def get_market(
    identifier: str,
    follow: bool = Query(True, description="Follow replaced markets"),
    db=Depends(get_db)
):
    """Get market by FinID or MIC."""
    market = Market.get(identifier, follow=follow)
    logger.info(f"Retrieved market: {market.fin_id}")
    return market.to_dict()

@app.get("/markets/{identifier}/holidays", summary="Get market holidays")
async def get_market_holidays(
    identifier: str,
    start: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end: date = Query(..., description="End date (YYYY-MM-DD)"),
    db=Depends(get_db)
):
    """Get market holidays for a date range."""
    market = Market.get(identifier)
    holidays = market.list_holidays(start, end)
    logger.info(f"Retrieved {len(holidays)} holidays for {identifier}")
    return [holiday.to_dict() for holiday in holidays]

@app.get("/markets/{identifier}/phases", summary="Generate market phases")
async def get_market_phases(
    identifier: str,
    start: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end: date = Query(..., description="End date (YYYY-MM-DD)"),
    db=Depends(get_db)
):
    """Generate market phases for a date range."""
    market = Market.get(identifier)
    phases = list(market.generate_phases(start, end))
    logger.info(f"Generated {len(phases)} phases for {identifier}")
    return [phase.to_dict() for phase in phases]

@app.get("/markets/{identifier}/schedules", summary="Get market schedules")
async def get_market_schedules(
    identifier: str,
    db=Depends(get_db)
):
    """Get market schedules."""
    market = Market.get(identifier)
    schedules = market.list_schedules()
    logger.info(f"Retrieved {len(schedules)} schedules for {identifier}")
    return [schedule.to_dict() for schedule in schedules]

@app.get("/markets/{identifier}/status", summary="Get market status")
async def get_market_status(
    identifier: str,
    datetime_str: Optional[str] = Query(None, alias="datetime", description="ISO datetime (YYYY-MM-DDTHH:MM:SS+TZ)"),
    db=Depends(get_db)
):
    """Get market status at a specific time (or current time if not provided)."""
    market = Market.get(identifier)
    
    if datetime_str:
        try:
            dt = datetime.fromisoformat(datetime_str)
            status = market.status(dt)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail="Invalid datetime format. Use ISO format: YYYY-MM-DDTHH:MM:SS+TZ"
            )
    else:
        status = market.status()
    
    logger.info(f"Retrieved status for {identifier}")
    return status.to_dict()

@app.get("/markets/{identifier}/is_available", summary="Check if market is available")
async def check_market_available(identifier: str, db=Depends(get_db)):
    """Check if market is available under current plan."""
    is_available = Market.is_available(identifier)
    logger.info(f"Checked availability for market {identifier}: {is_available}")
    return {"identifier": identifier, "is_available": is_available}

@app.get("/markets/{identifier}/is_covered", summary="Check if market is covered")
async def check_market_covered(identifier: str, db=Depends(get_db)):
    """Check if market is covered by TradingHours data."""
    # Note: is_covered expects a finid, so we need to handle MICs
    try:
        if "." in identifier:
            finid = identifier
        else:
            # It's a MIC, we need to get the finid first
            market = Market.get_by_mic(identifier, follow=False)
            finid = market.fin_id
        is_covered = Market.is_covered(finid)
        logger.info(f"Checked coverage for market {identifier} (finid: {finid}): {is_covered}")
        return {"identifier": identifier, "finid": finid, "is_covered": is_covered}
    except Exception as e:
        logger.error(f"Error checking coverage for {identifier}: {e}")
        return {"identifier": identifier, "finid": None, "is_covered": False}

@app.get("/markets/{identifier}/date_range", summary="Get market date range")
async def get_market_date_range(identifier: str, db=Depends(get_db)):
    """Get the first and last available dates for the market."""
    market = Market.get(identifier)
    logger.info(f"Retrieved date range for {identifier}")
    return {
        "identifier": identifier,
        "fin_id": market.fin_id,
        "first_available_date": market.first_available_date.isoformat(),
        "last_available_date": market.last_available_date.isoformat(),
        "country_code": market.country_code
    }

@app.get("/markets/finid/{finid}", summary="Get market by FinID")
async def get_market_by_finid(
    finid: str,
    follow: bool = Query(True, description="Follow replaced markets"),
    db=Depends(get_db)
):
    """Get market specifically by FinID."""
    market = Market.get_by_finid(finid, follow=follow)
    logger.info(f"Retrieved market by FinID: {market.fin_id}")
    return market.to_dict()

@app.get("/markets/mic/{mic}", summary="Get market by MIC")
async def get_market_by_mic(
    mic: str,
    follow: bool = Query(True, description="Follow replaced markets"),
    db=Depends(get_db)
):
    """Get market specifically by MIC."""
    market = Market.get_by_mic(mic, follow=follow)
    logger.info(f"Retrieved market by MIC {mic}: {market.fin_id}")
    return market.to_dict()

# Currency endpoints
@app.get("/currencies", summary="List currencies")
async def list_currencies(db=Depends(get_db)):
    """List all available currencies."""
    currencies = Currency.list_all()
    logger.info(f"Listed {len(currencies)} currencies")
    return [currency.to_dict() for currency in currencies]

@app.get("/currencies/{code}", summary="Get currency")
async def get_currency(code: str, db=Depends(get_db)):
    """Get currency by code."""
    currency = Currency.get(code)
    logger.info(f"Retrieved currency: {currency.currency_code}")
    return currency.to_dict()

@app.get("/currencies/{code}/holidays", summary="Get currency holidays")
async def get_currency_holidays(
    code: str,
    start: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end: date = Query(..., description="End date (YYYY-MM-DD)"),
    db=Depends(get_db)
):
    """Get currency holidays for a date range."""
    currency = Currency.get(code)
    holidays = currency.list_holidays(start, end)
    logger.info(f"Retrieved {len(holidays)} holidays for currency {code}")
    return [holiday.to_dict() for holiday in holidays]

@app.get("/currencies/{code}/is_available", summary="Check if currency is available")
async def check_currency_available(code: str, db=Depends(get_db)):
    """Check if currency is available under current plan."""
    is_available = Currency.is_available(code)
    logger.info(f"Checked availability for currency {code}: {is_available}")
    return {"currency_code": code, "is_available": is_available}

@app.get("/currencies/{code}/is_covered", summary="Check if currency is covered")
async def check_currency_covered(code: str, db=Depends(get_db)):
    """Check if currency is covered by TradingHours data."""
    is_covered = Currency.is_covered(code)
    logger.info(f"Checked coverage for currency {code}: {is_covered}")
    return {"currency_code": code, "is_covered": is_covered}


class GunicornApplication:
    """Custom Gunicorn application for programmatic server startup."""
    
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        
    def load_config(self):
        """Load configuration from options."""
        # Import here to avoid dependency issues
        from gunicorn.app.base import BaseApplication
        from gunicorn.config import Config
        
        # Create a proper config object
        config = Config()
        for key, value in self.options.items():
            if key in config.settings and value is not None:
                config.set(key.lower(), value)
                
        return config
        
    def load(self):
        """Return the WSGI application."""
        return self.application
        
    def run(self):
        """Run the Gunicorn server."""
        try:
            from gunicorn.app.base import BaseApplication
            class StandaloneApplication(BaseApplication):
                def __init__(self, app, options=None):
                    self.options = options or {}
                    self.application = app
                    super().__init__()

                def load_config(self):
                    for key, value in self.options.items():
                        if key in self.cfg.settings and value is not None:
                            self.cfg.set(key.lower(), value)

                def load(self):
                    return self.application
            
            gunicorn_app = StandaloneApplication(self.application, self.options)
            gunicorn_app.run()
            
        except ImportError:
            raise ImportError("gunicorn not installed. Install with: pip install gunicorn")


def run_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    uds: Optional[str] = None,
    workers: int = 2,
    log_level: Optional[str] = None,
):
    """Run server with gunicorn or uvicorn.
    
    Args:
        host: Host to bind to
        port: Port to bind to  
        uds: Unix domain socket path (overrides host/port)
        workers: Number of worker processes (only for gunicorn)
        log_level: Log level (if None, uses config from tradinghours.ini)
    """
    # Use log_level from config if not provided
    if log_level is None:
        log_level = main_config.get("server-mode", "log_level", fallback="info")
    if uds:
        bind = f"unix:{uds}"
        logger.info(f"Starting TradingHours API on Unix socket: {uds}")
        # Ensure socket directory exists
        socket_dir = Path(uds).parent
        socket_dir.mkdir(parents=True, exist_ok=True)
    else:
        bind = f"{host}:{port}"
        logger.info(f"Starting TradingHours API on http://{host}:{port}")
    

    # Use Gunicorn for production with multiple workers
    options = {
        'bind': bind,
        'workers': workers,
        'worker_class': 'uvicorn.workers.UvicornWorker',
        'loglevel': log_level,
        'capture_output': True,
        'enable_stdio_inheritance': True,
        'accesslog': '-',    # Log to stdout, captured by our LogCapture
        'errorlog': '-'      # Log to stderr, captured by our LogCapture
    }
    
    gunicorn_app = GunicornApplication(app, options)
    gunicorn_app.run()
    

# For backwards compatibility
create_app = lambda: app
