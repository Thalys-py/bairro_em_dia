from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import router as solicitacoes_router

app = FastAPI(debug=True)

# Sessão (importante para login)
app.add_middleware(SessionMiddleware, secret_key="chave-super-secreta")

# Serve arquivos da pasta "uploads" (imagens das solicitações)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Rotas da aplicação
app.include_router(solicitacoes_router)
