from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import logging
import time
from typing import List

# Imports locais
from core.config import settings
from core.database import create_tables, close_db
from core.websocket_manager import websocket_manager
from auth import get_current_user, auth_manager
from routers import auth_router, chat_router, user_router, contact_router, admin_router

# Configuração de logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação."""
    # Startup
    logger.info("Iniciando aplicação...")
    try:
        await create_tables()
        logger.info("Tabelas do banco criadas/verificadas")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {e}")
        raise

    yield

    # Shutdown
    logger.info("Encerrando aplicação...")
    try:
        await close_db()
        logger.info("Conexões do banco fechadas")
    except Exception as e:
        logger.error(f"Erro ao fechar banco: {e}")


# Criar aplicação FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="API moderna para chat em tempo real",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Middleware de segurança
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=settings.allowed_methods,
    allow_headers=settings.allowed_headers,
)

# Middleware de compressão
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Middleware personalizado para logging e métricas
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logging de requests."""
    start_time = time.time()

    # Log da request
    logger.info(f"Request: {request.method} {request.url}")

    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Request failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Erro interno do servidor"}
        )

    # Calcular tempo de processamento
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # Log da response
    logger.info(
        f"Response: {response.status_code} - "
        f"Time: {process_time:.3f}s - "
        f"Size: {response.headers.get('content-length', 'unknown')}"
    )

    return response


# Middleware para rate limiting
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Middleware para rate limiting."""
    client_ip = request.client.host

    # Pular rate limiting para endpoints estáticos
    if request.url.path.startswith("/static/"):
        return await call_next(request)

    # Verificar rate limit apenas para endpoints de auth
    if request.url.path.startswith("/auth/"):
        if not auth_manager.check_rate_limit(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Muitas tentativas. Tente novamente mais tarde."}
            )

    return await call_next(request)


# Configurar arquivos estáticos e templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Rotas da API
app.include_router(auth_router, prefix="/auth", tags=["Autenticação"])
app.include_router(user_router, prefix="/users", tags=["Usuários"])
app.include_router(chat_router, prefix="/chats", tags=["Chats"])
app.include_router(contact_router, prefix="/contacts", tags=["Contatos"])
app.include_router(admin_router, prefix="/admin", tags=["Administração"])


# Rotas WebSocket
@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """Endpoint principal do WebSocket."""
    connection_id = None

    try:
        # Validar token
        from core.security import verify_token
        payload = verify_token(token)
        user_id = int(payload.get("sub"))

        # Conectar usuário
        connection_id = await websocket_manager.connect(websocket, user_id)

        # Loop principal de mensagens
        while True:
            try:
                data = await websocket.receive_text()
                await websocket_manager.handle_message(connection_id, data)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Erro no WebSocket: {e}")
                break

    except HTTPException as e:
        logger.warning(f"Token inválido no WebSocket: {e.detail}")
        await websocket.close(code=1008, reason="Token inválido")
    except Exception as e:
        logger.error(f"Erro na conexão WebSocket: {e}")
        if websocket.client_state.CONNECTED:
            await websocket.close(code=1011, reason="Erro interno")
    finally:
        if connection_id:
            await websocket_manager.disconnect(connection_id)


# Rotas de páginas web
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página inicial."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Página de login."""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Página de registro."""
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard principal (requer autenticação via cookie/session)."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/chats", response_class=HTMLResponse)
async def chats_page(request: Request):
    """Página de chats."""
    return templates.TemplateResponse("chats.html", {"request": request})


@app.get("/contacts", response_class=HTMLResponse)
async def contacts_page(request: Request):
    """Página de contatos."""
    return templates.TemplateResponse("contacts.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """Página de administração."""
    return templates.TemplateResponse("admin.html", {"request": request})


# Rotas de API para informações do sistema
@app.get("/health")
async def health_check():
    """Health check da aplicação."""
    return {
        "status": "healthy",
        "version": settings.version,
        "timestamp": time.time()
    }


@app.get("/metrics")
async def get_metrics():
    """Métricas básicas da aplicação."""
    return {
        "active_connections": len(websocket_manager.active_connections),
        "online_users": len(websocket_manager.user_connections),
        "active_chats": len(websocket_manager.chat_users)
    }


@app.get("/ws/stats")
async def websocket_stats():
    """Estatísticas do WebSocket."""
    return {
        "total_connections": len(websocket_manager.active_connections),
        "users_online": len(websocket_manager.user_connections),
        "active_chats": len(websocket_manager.chat_users),
        "connections_by_user": {
            user_id: len(connections)
            for user_id, connections in websocket_manager.user_connections.items()
        }
    }


# Handlers de erro personalizados
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handler para 404."""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=404,
            content={"detail": "Endpoint não encontrado"}
        )
    return templates.TemplateResponse(
        "404.html",
        {"request": request},
        status_code=404
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handler para erros internos."""
    logger.error(f"Erro interno: {exc}")

    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"detail": "Erro interno do servidor"}
        )
    return templates.TemplateResponse(
        "500.html",
        {"request": request},
        status_code=500
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler para HTTPException."""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

    # Para páginas web, redirecionar conforme o erro
    if exc.status_code == 401:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Acesso não autorizado"},
            status_code=401
        )
    elif exc.status_code == 403:
        return templates.TemplateResponse(
            "403.html",
            {"request": request},
            status_code=403
        )
    else:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )


# Rotas de desenvolvimento (apenas em modo debug)
if settings.debug:
    @app.get("/debug/users")
    async def debug_users():
        """Lista usuários online (apenas debug)."""
        return {
            "online_users": list(websocket_manager.user_connections.keys()),
            "user_connections": {
                user_id: len(connections)
                for user_id, connections in websocket_manager.user_connections.items()
            }
        }


    @app.get("/debug/chats")
    async def debug_chats():
        """Lista chats ativos (apenas debug)."""
        return {
            "active_chats": dict(websocket_manager.chat_users),
            "chat_count": len(websocket_manager.chat_users)
        }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug",
        access_log=True
    )