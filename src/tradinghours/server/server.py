"""Production-ready FastAPI server for TradingHours API."""
import platform
import sys, time, traceback
import logging
import datetime as dt
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, List
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException, Query, Depends, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from fastapi.responses import JSONResponse
except ImportError as e:
    print(traceback.format_exc())
    raise ImportError(
        "Server dependencies not installed. Run: pip install tradinghours[server]"
    ) from e

from ..market import Market
from ..currency import Currency
from ..store import db
from ..exceptions import TradingHoursError, ConfigError
from ..config import main_config
from ..console import run_import
from .. import __version__
from .util import setup_root_logger, LogCapture

from .responses import (
    MarketResponse,
    MarketHolidayResponse,
    PhaseResponse,
    ScheduleResponse,
    MarketStatusResponse,
    CurrencyResponse,
    CurrencyHolidayResponse,
    IsAvailableResponse
)

# Configure logging
setup_root_logger()
logger = logging.getLogger("th.server")

# Capture stdout/stderr to also log to our files
original_stdout = sys.stdout
original_stderr = sys.stderr
sys.stdout = LogCapture(original_stdout, "stdout")
sys.stderr = LogCapture(original_stderr, "stderr")

# Background task management
background_tasks = set()

async def auto_import_async():
    frequency_minutes = main_config.getint("server-mode", "auto_import_frequency")
    while True:
        await asyncio.sleep(frequency_minutes * 60)
        try:
            await asyncio.to_thread(run_import, quiet=True)
        except Exception as e:
            logger.exception(f"Auto-import failed: {e}")
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    # Startup
    if main_config.getint("server-mode", "auto_import_frequency"):
        task = asyncio.create_task(auto_import_async())
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)
    
    yield
    
    # Shutdown
    if background_tasks:
        for task in background_tasks:
            task.cancel()
        await asyncio.gather(*background_tasks, return_exceptions=True)

# Create FastAPI app
app = FastAPI(
    title="TradingHours API",
    description="REST API for TradingHours market and currency data",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
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
        logger.exception(
            f"{client_ip} - {method} {url} - ERROR - {process_time:.3f}s - {type(e).__name__}: {str(e)}"
        )
        if isinstance(e, TradingHoursError):
            return JSONResponse(status_code=400, content={"message": str(e)})
            
        try:
            log_folder = Path(main_config.get("server-mode", "log_folder")).absolute()
            message = f"Server Error. Logs are saved in `{log_folder}`. Please send them to support@tradinghours.com for further investigation."
        except Exception as e:
            message = "Server Error. Please contact support@tradinghours.com for further investigation."

        return JSONResponse(status_code=500, content={"message": message})
    
    process_time = time.time() - start_time
    logger.debug(
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
    allow_methods=["GET", "OPTIONS"],
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
        local_data_info = db.get_local_data_info()
        local_timestamp = local_data_info.download_timestamp if local_data_info else None
        
        return {
            "api_version": __version__,
            "last_data_update": local_timestamp.isoformat() if local_timestamp else None,
            "access_level": db.access_level.value if db.access_level else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting API info: {str(e)}")

# Market endpoints
@app.get("/markets", summary="List markets", response_model=List[MarketResponse])
async def list_markets(
    subset: str = Query("*", description="Filter markets by FinID pattern (e.g., 'US.*')"),
    db=Depends(get_db),
):
    """List all available markets with optional filtering."""
    markets = Market.list_all(subset)
    logger.info(f"Listed {len(markets)} markets with subset '{subset}'")
    return [market.to_dict() for market in markets]


@app.get("/markets/{identifier}", summary="Get market", response_model=MarketResponse)
async def get_market(
    identifier: str,
    follow: bool = Query(True, description="Follow replaced markets"),
    db=Depends(get_db),
):
    """Get market by FinID or MIC."""
    market = Market.get(identifier, follow=follow)
    logger.info(f"Retrieved market: {market.fin_id}")
    return market.to_dict()

@app.get("/markets/{identifier}/holidays", summary="Get market holidays", response_model=List[MarketHolidayResponse])
async def get_market_holidays(
    identifier: str,
    start: dt.date = Query(..., description="Start date (YYYY-MM-DD)"),
    end: dt.date = Query(..., description="End date (YYYY-MM-DD)"),
    db=Depends(get_db)
):
    """Get market holidays for a date range."""
    market = Market.get(identifier)
    holidays = market.list_holidays(start, end)
    logger.info(f"Retrieved {len(holidays)} holidays for {identifier}")
    return [holiday.to_dict() for holiday in holidays]

@app.get("/markets/{identifier}/phases", summary="Generate market phases", response_model=List[PhaseResponse])
async def get_market_phases(
    identifier: str,
    start: dt.date = Query(..., description="Start date (YYYY-MM-DD)"),
    end: dt.date = Query(..., description="End date (YYYY-MM-DD)"),
    db=Depends(get_db)
):
    """Generate market phases for a date range."""
    market = Market.get(identifier)
    phases = [phase.to_dict() for phase in market.generate_phases(start, end)]
    logger.info(f"Generated {len(phases)} phases for {identifier}")
    return phases

@app.get("/markets/{identifier}/schedules", summary="Get market schedules", response_model=List[ScheduleResponse])
async def get_market_schedules(
    identifier: str,
    db=Depends(get_db)
):
    """Get market schedules."""
    market = Market.get(identifier)
    schedules = market.list_schedules()
    logger.info(f"Retrieved {len(schedules)} schedules for {identifier}")
    return [schedule.to_dict() for schedule in schedules]

@app.get("/markets/{identifier}/status", summary="Get market status", response_model=MarketStatusResponse)
async def get_market_status(
    identifier: str,
    datetime_utc: Optional[dt.datetime] = Query(None, description="UTC datetime in ISO format (YYYY-MM-DDTHH:MM:SS+00:00)"),
    db=Depends(get_db)
):
    """
    Get market status at a specific time (or current time if not provided).
    
    To avoid problems with timezone offsets and conversions, the datetime_utc must have the +00:00 timezone offset.

    All datetimes in the response will still be in the timezone of the market, like it is returned by other endpoints.
    """
    market = Market.get(identifier)

    if datetime_utc:
        if str(datetime_utc.tzinfo) != "UTC":
            raise HTTPException(
                status_code=400, 
                detail="Datetime must have +00:00 timezone offset, so that we agree on the same UTC datetime."
            )

        status = market.status(datetime_utc)
    else:
        status = market.status()
    
    logger.info(f"Retrieved status for {identifier}")
    return status.to_dict()

@app.get("/markets/{identifier}/is_available", summary="Check if market is available", response_model=IsAvailableResponse)
async def check_market_available(identifier: str, db=Depends(get_db)):
    """Check if market is available under current plan."""
    is_available = Market.is_available(identifier)
    logger.info(f"Checked availability for market {identifier}: {is_available}")
    return {"is_available": is_available}

@app.get("/markets/finid/{finid}", summary="Get market by FinID", response_model=MarketResponse)
async def get_market_by_finid(
    finid: str,
    follow: bool = Query(True, description="Follow replaced markets"),
    db=Depends(get_db)
):
    """Get market specifically by FinID."""
    market = Market.get_by_finid(finid, follow=follow)
    logger.info(f"Retrieved market by FinID: {market.fin_id}")
    return market.to_dict()

@app.get("/markets/mic/{mic}", summary="Get market by MIC", response_model=MarketResponse)
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
@app.get("/currencies", summary="List currencies", response_model=List[CurrencyResponse])
async def list_currencies(db=Depends(get_db)):
    """List all available currencies."""
    currencies = Currency.list_all()
    logger.info(f"Listed {len(currencies)} currencies")
    return [currency.to_dict() for currency in currencies]

@app.get("/currencies/{code}", summary="Get currency", response_model=CurrencyResponse)
async def get_currency(code: str, db=Depends(get_db)):
    """Get currency by code."""
    currency = Currency.get(code)
    logger.info(f"Retrieved currency: {currency.currency_code}")
    return currency.to_dict()

@app.get("/currencies/{code}/holidays", summary="Get currency holidays", response_model=List[CurrencyHolidayResponse])
async def get_currency_holidays(
    code: str,
    start: dt.date = Query(..., description="Start date (YYYY-MM-DD)"),
    end: dt.date = Query(..., description="End date (YYYY-MM-DD)"),
    db=Depends(get_db)
):
    """Get currency holidays for a date range."""
    currency = Currency.get(code)
    holidays = currency.list_holidays(start, end)
    logger.info(f"Retrieved {len(holidays)} holidays for currency {code}")
    return [holiday.to_dict() for holiday in holidays]

@app.get("/currencies/{code}/is_available", summary="Check if currency is available", response_model=IsAvailableResponse)
async def check_currency_available(code: str, db=Depends(get_db)):
    """Check if currency is available under current plan."""
    is_available = Currency.is_available(code)
    logger.info(f"Checked availability for currency {code}: {is_available}")
    return {"is_available": is_available}

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
):
    """Run server with gunicorn or uvicorn.
    
    Args:
        host: Host to bind to
        port: Port to bind to  
        uds: Unix domain socket path (overrides host/port)
        no_auto_import: Disable auto-import background task
    """
    if uds:
        bind = f"unix:{uds}"
        logger.info(f"Starting TradingHours API on Unix socket: {uds}")
        # Ensure socket directory exists
        socket_dir = Path(uds).parent
        socket_dir.mkdir(parents=True, exist_ok=True)
    else:
        bind = f"{host}:{port}"
        logger.info(f"Starting TradingHours API on http://{host}:{port}")
    

    log_level = (main_config.get("server-mode", "log_level") or "DEBUG").upper()

    # Use single worker for database consistency
    options = {
        'bind': bind,
        'workers': 1,  # Enforce single worker
        'worker_class': 'uvicorn.workers.UvicornWorker',
        'loglevel': log_level,
        'timeout': 120,
        'graceful_timeout': 30,
        'capture_output': True,
        'enable_stdio_inheritance': True,
        'accesslog': None,
        'errorlog': '-'      # Log to stderr, captured by our LogCapture
    }
    
    if platform.system() == 'Windows':
        # Use uvicorn directly on Windows
        import uvicorn
        try:
            uvicorn.run(app, host=host, port=port, workers=1, log_level=log_level.lower())
        except Exception as e:
            print(traceback.format_exc())
            raise
    else:
        # Use existing gunicorn logic on Unix
        gunicorn_app = GunicornApplication(app, options)
        gunicorn_app.run()

# For backwards compatibility
create_app = lambda: app
