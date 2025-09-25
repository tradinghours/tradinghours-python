"""Production-ready FastAPI server for TradingHours API."""
import os
import sys
import logging
from datetime import datetime, date
from typing import Optional, List
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException, Query, Depends
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from fastapi.responses import JSONResponse
    import uvicorn
except ImportError:
    raise ImportError(
        "Server dependencies not installed. Run: pip install tradinghours[server]"
    )

from .market import Market
from .currency import Currency
from .store import db
from .exceptions import NoAccess, NotCovered, MICDoesNotExist, DateNotAvailable
from . import __version__

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TradingHours API",
    description="REST API for TradingHours market and currency data",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Security middleware for production
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # Configure appropriately for production
)

# CORS middleware (configure for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
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
    log_level: str = "info",
):
    """Run server with gunicorn or uvicorn.
    
    Args:
        host: Host to bind to
        port: Port to bind to  
        uds: Unix domain socket path (overrides host/port)
        workers: Number of worker processes (only for gunicorn)
        log_level: Log level
        use_gunicorn: Whether to use gunicorn (True) or uvicorn (False)
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
    

    # Use Gunicorn for production with multiple workers
    options = {
        'bind': bind,
        'workers': workers,
        'worker_class': 'uvicorn.workers.UvicornWorker',
        'loglevel': log_level,
        'accesslog': '-',
        'errorlog': '-'
    }
    
    gunicorn_app = GunicornApplication(app, options)
    gunicorn_app.run()
    

# For backwards compatibility
create_app = lambda: app
