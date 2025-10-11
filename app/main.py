# app/main.py
import os
from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    Query,
    Request,
    status,
    Response,
    HTTPException,
)
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

# --- TAMBAHAN IMPORT UNTUK ACTIVITY LOG ---
import json
import time
import uuid
from datetime import datetime
from jose import jwt, JWTError
from . import config
from .models.activity_log import ActivityLog
from .models.user import User as UserModel
from .models.system_setting import SystemSetting as SettingModel
from .config import settings

# --- AKHIR TAMBAHAN IMPORT ---

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Import enhanced logging configuration
from .logging_config import setup_logging

# Initialize logging with enhanced configuration
logger = setup_logging()

from .database import Base, engine, get_db, AsyncSessionLocal
from .routers import (
    pelanggan,
    user,
    role,
    auth,
    data_teknis,
    harga_layanan,
    paket_layanan,
    langganan,
    invoice,
    mikrotik_server,
    uploads,
    notifications,
    dashboard,
    permission,
    sk,
    calculator,
    report,
    olt,
    odp,
    topology,
    settings as settings_router,
    inventory,
    inventory_status,
    inventory_type,
    dashboard_pelanggan,
    activity_log,
    debug,
)
from .jobs import (
    job_generate_invoices,
    job_suspend_services,
    job_verify_payments,
    job_send_payment_reminders,
    job_retry_mikrotik_syncs,
    job_check_server_connectivity,
)

# Use our secure logging configuration (currently disabled due to unicode issues)
# from .logging_config_secure import setup_secure_logging
from .auth import get_user_from_token
from .websocket_manager import manager

# Import our logging utilities
from .logging_utils import sanitize_log_data
from .database import init_encryption


# Fungsi untuk membuat tabel di database saat aplikasi pertama kali dijalankan
async def create_tables():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # Hati-hati, ini akan menghapus semua tabel
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize encryption after all tables are created and models are loaded
    init_encryption()


# Inisialisasi aplikasi FastAPI
app = FastAPI(
    title="Billing System API",
    description="API untuk sistem billing terintegrasi Xendit.",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# ==========================================================
# --- Middleware Backend to FrontEnd ---
# ==========================================================
origins = [
    "https://billingftth.my.id",  # <-- AKTIFKAN INI untuk akses via browser
    "https://www.billingftth.my.id",  # <-- Tambahkan versi www
    "http://192.168.1.4:3000",
    # "http://192.168.222.20",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",  # Tambahkan untuk memastikan kompatibilitas
    "http://127.0.0.1:8000",  # Tambahkan untuk memastikan kompatibilitas
    # Cross-origin combinations untuk development
    "http://localhost:3000",  # dari localhost ke 127.0.0.1:8000
    "http://127.0.0.1:3000",  # dari 127.0.0.1 ke localhost:8000
]

# SECURITY: Dynamic CORS configuration based on environment
import os
environment = os.getenv("ENVIRONMENT", "development")

if environment == "production":
    # Production: Only allow specific origins
    production_origins = [
        os.getenv("FRONTEND_URL", ""),  # Get from environment
        "https://billingftth.my.id",  # Replace with actual domain
    ]
    # Filter out empty strings
    allowed_origins = [origin for origin in production_origins if origin]

    if not allowed_origins:
        # Fallback to development origins if no production origins configured
        allowed_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
        print("⚠️  WARNING: No production CORS origins configured, using development origins")
else:
    # Development: Allow local development origins
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Access-Control-Allow-Origin"],
    max_age=600,  # Cache preflight requests selama 10 menit
)

print(f"🔒 CORS configured for {environment} mode with origins: {allowed_origins}")

# Add GZip compression middleware untuk API response optimization
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Note: Custom response optimization middleware disabled due to Unicode issues
# GZip compression already enabled above for API response optimization


# ==========================================================
# --- Middleware untuk Mode Maintenance ---
# ==========================================================
@app.middleware("http")
async def maintenance_mode_middleware(request: Request, call_next):
    # Daftar path yang diizinkan selama maintenance
    allowed_paths = [
        "/api/users/token",  # Izinkan login
        "/api/settings/maintenance",  # Izinkan admin mengubah status maintenance
        "/docs",  # Izinkan akses dokumentasi API
        "/openapi.json",
    ]

    # Jika path request ada di daftar yang diizinkan, lewati pengecekan
    if any(request.url.path.startswith(path) for path in allowed_paths):
        return await call_next(request)

    async with AsyncSessionLocal() as db:
        # Ambil status maintenance dari database dengan query berdasarkan key
        stmt_active = select(SettingModel).where(
            SettingModel.setting_key == "maintenance_active"
        )
        maintenance_active_setting = (
            await db.execute(stmt_active)
        ).scalar_one_or_none()
        is_active = (
            maintenance_active_setting
            and maintenance_active_setting.setting_value.lower() == "true"
        )

        if is_active:
            # Jika maintenance aktif, ambil pesannya
            stmt_message = select(SettingModel).where(
                SettingModel.setting_key == "maintenance_message"
            )
            maintenance_message_setting = (
                await db.execute(stmt_message)
            ).scalar_one_or_none()
            message = (
                maintenance_message_setting.setting_value
                if maintenance_message_setting
                else "Sistem sedang dalam perbaikan. Silakan coba lagi nanti."
            )

            # Kembalikan response 503 Service Unavailable
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"detail": message},
            )

    # Jika tidak maintenance, lanjutkan ke request berikutnya
    response = await call_next(request)
    return response


# Pastikan middleware ini ada SEBELUM middleware logging agar request yang diblok tidak tercatat sebagai aktivitas
# ==========================================================


# --- FUNGSI BANTU UNTUK MENDAPATKAN USER DARI TOKEN (VERSI AMAN UNTUK LOGGING) ---
async def get_user_from_token_for_logging(
    token: str, db: AsyncSession
) -> UserModel | None:
    """
    Mendekode token dan mengambil data user untuk keperluan logging.
    Fungsi ini aman dan akan mengembalikan None jika terjadi error, tanpa menghentikan aplikasi.
    """
    if not token:
        return None
    try:
        payload = jwt.decode(
            token, config.settings.SECRET_KEY, algorithms=[config.settings.ALGORITHM]
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            return None
        user = await db.get(UserModel, int(user_id))
        return user
    except (JWTError, ValueError, TypeError):
        # Menangkap semua kemungkinan error (token tidak valid, user_id bukan angka, dll)
        return None


# Tambahan middleware untuk logging request
@app.middleware("http")
async def log_requests_and_activity(request: Request, call_next):
    logger = logging.getLogger("app.middleware")
    start_time = time.time()

    # Log semua request yang masuk (tanpa sensitive data)
    logger.info(f"Incoming request: {request.method} {request.url}")
    # Log headers but filter sensitive ones
    safe_headers = {}
    sensitive_headers = ["authorization", "cookie", "x-api-key", "x-auth-token"]
    for key, value in request.headers.items():
        if key.lower() in sensitive_headers:
            safe_headers[key] = "***REDACTED***"
        else:
            safe_headers[key] = value
    logger.info(f"Headers: {safe_headers}")

    # --- LOGIKA BARU: BACA BODY REQUEST DI AWAL ---
    # Kita harus membaca body di sini agar bisa digunakan untuk logging nanti.
    req_body_bytes = b""
    try:
        req_body_bytes = await request.body()
    except:
        # Jika gagal membaca body, lanjutkan tanpa body
        pass

    # Buat ulang request agar endpoint tetap bisa membaca body-nya.
    async def receive():
        return {"type": "http.request", "body": req_body_bytes, "more_body": False}

    request_with_body = Request(request.scope, receive)
    # --- AKHIR LOGIKA BACA BODY ---

    # Jika ini adalah webhook Xendit, log lebih detail tapi filter sensitive data
    if "xendit-callback" in str(request.url):
        # Filter sensitive data from the body
        try:
            if req_body_bytes:
                body_str = req_body_bytes.decode("utf-8")
                filtered_body = sanitize_log_data(body_str)
                logger.info(f"Xendit webhook body: {filtered_body}")
            else:
                logger.info("Xendit webhook body: Empty body")
        except Exception as e:
            logger.info(
                f"Xendit webhook body: ***REDACTED*** (Error processing body: {str(e)})"
            )

    response = await call_next(request_with_body)

    process_time = time.time() - start_time
    logger.info(f"Response status: {response.status_code} in {process_time:.2f}s")

    # --- LOGIKA BARU: SIMPAN ACTIVITY LOG KE DATABASE ---
    if (
        request.method in ["POST", "PATCH", "DELETE"]
        and 200 <= response.status_code < 300
    ):
        if "/token" not in str(request.url) and "/login" not in str(request.url):
            async with AsyncSessionLocal() as db:
                try:
                    auth_header = request.headers.get("Authorization", "")
                    token = auth_header.replace("Bearer ", "")
                    user = await get_user_from_token_for_logging(token, db)
                    if user:
                        details = None
                        if req_body_bytes:
                            try:
                                # Parse JSON and sanitize sensitive data
                                body_json = json.loads(req_body_bytes)
                                sanitized_body = sanitize_log_data(body_json)
                                details = json.dumps(sanitized_body)
                            except json.JSONDecodeError:
                                # Jika bukan JSON (misal: file upload), catat placeholder
                                details = f"[Data non-JSON, Content-Type: {request.headers.get('content-type')}]"
                        log_entry = ActivityLog(
                            user_id=user.id,
                            action=f"{request.method} {request.url.path}",
                            details=details,
                        )
                        db.add(log_entry)
                        await db.commit()
                        logger.info(
                            f"Activity logged for user {user.email}: {log_entry.action}"
                        )
                except Exception as e:
                    logger.error(f"Failed to log activity: {e}", exc_info=True)

    return response


# ==========================================================

# Inisialisasi scheduler
scheduler = AsyncIOScheduler()


# Test endpoint untuk WebSocket
@app.get("/ws/test")
def websocket_test():
    return {"message": "WebSocket endpoint accessible", "status": "ok"}


# WebSocket endpoint
@app.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket, token: str = Query(...)):
    """WebSocket endpoint untuk notifications real-time."""
    db = None
    logger = logging.getLogger("app.websocket")
    logger.info(f"WebSocket connection attempt with token: {token[:20]}...")

    try:
        # Dapatkan database session
        db_generator = get_db()
        db = await db_generator.__anext__()

        # --- TAMBAHAN LOGGING UNTUK DEBUG ---
        # SECURITY: Don't log tokens at all, even partially
        # logger.info(f"Token received: {token[:20]}...")  # Removed for security
        logger.info("Token received and validated")  # Generic message without token exposure

        if not token:
            logger.error("No token provided in WebSocket connection")
            await websocket.close(code=4002, reason="No token provided")
            return
        # --- AKHIR TAMBAHAN ---

        # Verifikasi token dan dapatkan user
        user = await get_user_from_token(token, db)
        if not user:
            logger.error("Invalid token provided")
            await websocket.close(code=4001, reason="Invalid token")
            return

        # Connect WebSocket menggunakan manager yang dioptimasi
        await manager.connect(websocket, user.id)
        logger.info(f"WebSocket connected for user {user.id}")

        # Add user roles untuk targeted broadcasting
        if hasattr(user, 'roles'):
            for role in user.roles:
                await manager.add_user_role(user.id, role.name)

        try:
            # Keep connection alive dan handle incoming messages
            while True:
                # Tunggu pesan dari client (bisa berupa ping/pong atau commands)
                data = await websocket.receive_text()
                logger.debug(f"Received message from user {user.id}: {data}")

                # Update activity timestamp
                if user.id in manager.connection_metadata:
                    manager.connection_metadata[user.id]['last_activity'] = time.time()

                # Handle ping/pong untuk keep-alive
                if data == "ping":
                    await websocket.send_text("pong")
                elif data == "pong":
                    # Balas pong dengan ping untuk keep-alive dua arah
                    await websocket.send_text("ping")
                else:
                    # Handle pesan lain jika diperlukan
                    try:
                        # Coba parse sebagai JSON jika bukan ping/pong
                        message_data = json.loads(data)
                        logger.debug(
                            f"Received JSON message from user {user.id}: {message_data}"
                        )
                        # Kirim acknowledgment
                        await websocket.send_text(
                            json.dumps({"type": "ack", "message": "Message received"})
                        )
                    except json.JSONDecodeError:
                        # Jika bukan JSON, kirim acknowledgment sederhana
                        logger.debug(
                            f"Received text message from user {user.id}: {data}"
                        )
                        await websocket.send_text(
                            json.dumps(
                                {"type": "ack", "message": "Text message received"}
                            )
                        )

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user.id}")
        except Exception as e:
            logger.error(f"WebSocket error for user {user.id}: {e}")
        finally:
            await manager.disconnect(user.id)

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        try:
            await websocket.close(code=4000, reason="Connection error")
        except Exception as e:
            #  Cukup log sebagai debug, karena ini bukan error kritis
            logger.debug(f"Failed to cleanly close WebSocket during final cleanup: {e}")
    finally:
        # Tutup database session
        if db:
            await db.close()


# Event handler untuk startup aplikasi
@app.on_event("startup")
async def startup_event():
    # 1. Buat tabel di database
    await create_tables()
    print("Tabel telah diperiksa/dibuat.")

    # 2. Tambahkan tugas-tugas terjadwal
    # Setiap job diberi 'id' unik untuk mencegah duplikasi penjadwalan.
    # 'replace_existing=True' memastikan jika server restart, job lama akan diganti.

    #==============================================================GENERATE INVOICE====================================================================================#
    # Generate invoice setiap hari jam 10:00 pagi untuk langganan yang jatuh tempo 5 hari lagi (H-5).
    #scheduler.add_job(job_generate_invoices, 'cron', hour=10, minute=0, timezone='Asia/Jakarta', id="generate_invoices_job", replace_existing=True)
    #==============================================================GENERATE INVOICE====================================================================================#

    #==============================================================SUSPANDED AND UNSUSPANDED=======================================================================#
    # Suspend services tepat tanggal 5 jam 00:00 untuk pelanggan yang telat bayar dari jatuh tempo tanggal 1.
    #scheduler.add_job(job_suspend_services, 'cron', day=5, hour=0, minute=0, timezone='Asia/Jakarta', id="suspend_services_job", replace_existing=True)
    #==============================================================SUSPANDED AND UNSUSPANDED=======================================================================#

    # Mengirim pengingat pembayaran setiap hari jam 8 pagi.
    #scheduler.add_job(job_send_payment_reminders, 'cron', hour=8, minute=0, timezone='Asia/Jakarta', id="send_reminders_job", replace_existing=True)

    # Memverifikasi pembayaran yang mungkin terlewat setiap 15 menit.
    #scheduler.add_job(job_verify_payments, 'interval', minutes=15, id="verify_payments_job", replace_existing=True)

    # Mencoba ulang sinkronisasi Mikrotik yang gagal setiap 5 menit.
    #scheduler.add_job(job_retry_mikrotik_syncs, 'interval', minutes=5, id="retry_mikrotik_syncs_job", replace_existing=True)

    # Connection Pool Monitoring Job - Monitor setiap 10 menit
    async def periodic_connection_pool_monitor():
        """Periodic connection pool monitoring and cleanup."""
        from .database import monitor_connection_pool, cleanup_idle_connections

        try:
            await monitor_connection_pool()
            await cleanup_idle_connections()
        except Exception as e:
            logger.error(f"Connection pool monitoring failed: {e}")

    # scheduler.add_job(periodic_connection_pool_monitor, 'interval', minutes=10, id="connection_pool_monitor", replace_existing=True)

    # 3. Mulai scheduler
    scheduler.start()
    print("Scheduler telah dimulai...")
    logger.info("Application startup complete")


# Event handler untuk shutdown aplikasi
@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    print("Scheduler telah dimatikan.")

    # Cleanup WebSocket connections
    await manager.cleanup()
    print("WebSocket connections telah dibersihkan.")

    # Cleanup Mikrotik connection pool
    from .services.mikrotik_connection_pool import mikrotik_pool
    mikrotik_pool.close_all_connections()
    print("Mikrotik connection pool telah ditutup.")


# API_PREFIX = os.getenv("API_PREFIX", "")

# 🛡️ GLOBAL ERROR HANDLER
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Global handler untuk HTTPExceptions dengan consistent response format.
    Provides graceful error responses across all endpoints.
    """
    # Log error untuk debugging
    logger.error(f"HTTP {exc.status_code} - {exc.detail} - Path: {request.url.path}")

    # Determine if this is a client error (4xx) or server error (5xx)
    is_client_error = 400 <= exc.status_code < 500

    # Consistent error response format
    error_response = {
        "success": False,
        "error": {
            "code": exc.status_code,
            "message": exc.detail,
            "type": "http_error",
            "client_error": is_client_error,
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path
        }
    }

    # Add additional context for specific error types
    if exc.status_code == 401:
        error_response["error"]["hint"] = "Please check your authentication credentials"
    elif exc.status_code == 403:
        error_response["error"]["hint"] = "You don't have permission to access this resource"
    elif exc.status_code == 404:
        error_response["error"]["hint"] = "The requested resource was not found"
    elif exc.status_code == 422:
        error_response["error"]["hint"] = "Please check your request data format"
    elif exc.status_code >= 500:
        error_response["error"]["hint"] = "Internal server error occurred. Please try again later"

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Global handler untuk unexpected exceptions.
    Provides graceful degradation for critical errors.
    """
    # Log full error for debugging (without sensitive data)
    logger.error(f"Unexpected error - Path: {request.url.path} - Error: {type(exc).__name__}: {str(exc)}")

    # Sanitize error message for client
    error_message = "Internal server error occurred"
    if os.getenv("ENVIRONMENT") == "development":
        error_message = f"{type(exc).__name__}: {str(exc)}"

    # Graceful error response
    error_response = {
        "success": False,
        "error": {
            "code": 500,
            "message": error_message,
            "type": "internal_error",
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path,
            "request_id": str(uuid.uuid4()),  # For error tracking
            "graceful_degradation": True
        }
    }

    return JSONResponse(
        status_code=500,
        content=error_response
    )


# Meng-include semua router
app.include_router(pelanggan.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(role.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(data_teknis.router, prefix="/api")
app.include_router(harga_layanan.router, prefix="/api")
app.include_router(langganan.router, prefix="/api")
app.include_router(sk.router, prefix="/api")
app.include_router(paket_layanan.router, prefix="/api")
app.include_router(invoice.router, prefix="/api")
app.include_router(mikrotik_server.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")
app.include_router(calculator.router, prefix="/api")
# app.include_router(system_log.router)
app.include_router(activity_log.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(permission.router, prefix="/api")
app.include_router(report.router, prefix="/api")
app.include_router(olt.router, prefix="/api")
app.include_router(odp.router, prefix="/api")
app.include_router(topology.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")
app.include_router(inventory_status.router, prefix="/api")
app.include_router(inventory_type.router, prefix="/api")
app.include_router(dashboard_pelanggan.router, prefix="/api")

# Debug router - hanya untuk development
if os.getenv("ENVIRONMENT", "development") == "development":
    app.include_router(debug.router, prefix="/api")
    print("🔍 Debug endpoints enabled (development mode)")


# Health Check Endpoint untuk Connection Pool Monitoring
@app.get("/health")
async def health_check():
    """Enhanced health check dengan connection pool monitoring."""
    try:
        # Get connection pool status
        from .database import get_connection_pool_status, monitor_connection_pool, cleanup_idle_connections

        pool_status = await get_connection_pool_status()
        monitoring_result = await monitor_connection_pool()
        cleanup_result = await cleanup_idle_connections()

        # Determine overall health
        is_healthy = (
            pool_status["utilization_percent"] < 90 and
            pool_status["status"] != "critical"
        )

        health_data = {
            "status": "healthy" if is_healthy else "degraded",
            "timestamp": datetime.now().isoformat(),
            "database": {
                "connection_pool": pool_status,
                "environment": os.getenv("ENVIRONMENT", "development"),
                "cleanup_result": cleanup_result
            },
            "monitoring": {
                "thresholds": {
                    "warning": os.getenv("CONNECTION_POOL_WARN_THRESHOLD", 70),
                    "critical": os.getenv("CONNECTION_POOL_CRITICAL_THRESHOLD", 90)
                }
            }
        }

        return health_data

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


# Simple health check untuk load balancers
@app.get("/health/simple")
def simple_health_check():
    """Simple health check untuk load balancers dan monitoring systems."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# Error monitoring endpoint
@app.get("/errors")
async def get_error_stats():
    """Get error statistics untuk monitoring."""
    from .utils.error_handler import error_tracker
    return error_tracker.get_error_summary()


# Endpoint root untuk verifikasi
@app.get("/")
def read_root():
    return {"message": "Selamat datang di API Billing System"}


# Test endpoint untuk webhook
@app.post("/test-webhook")
async def test_webhook(request: Request):
    logger = logging.getLogger("app.test")
    body = await request.body()
    # Filter sensitive data before logging
    try:
        if body:
            body_str = body.decode("utf-8")
            filtered_body = sanitize_log_data(body_str)
            logger.info(f"Test webhook received: {filtered_body}")
        else:
            logger.info("Test webhook received: Empty body")
    except Exception as e:
        logger.info(
            f"Test webhook received: ***REDACTED*** (Error processing body: {str(e)})"
        )
    return {"status": "received", "body": body.decode() if body else None}
