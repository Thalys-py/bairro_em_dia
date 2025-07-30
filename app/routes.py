from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models, schemas
import uuid
import os
from typing import Optional

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

templates = Jinja2Templates(directory="app/templates")
templates.env.globals['debug'] = True
templates.env.auto_reload = True

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------- PÁGINA INICIAL PÚBLICA -----------

@router.get("/", response_class=HTMLResponse)
def pagina_inicial(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ----------- LOGIN E AUTENTICAÇÃO -----------

@router.get("/login", response_class=HTMLResponse)
def exibir_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def realizar_login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "123":
        request.session["usuario"] = username
        return RedirectResponse(url="/painel", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "erro": "Credenciais inválidas"})

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)

# ----------- PAINEL HTML PROTEGIDO -----------

@router.get("/painel", response_class=HTMLResponse)
async def painel_solicitacoes(
    request: Request,
    db: Session = Depends(get_db),
    categoria: Optional[str] = Query(None),
    protocolo: Optional[str] = Query(None)
):
    try:
        query = db.query(models.Solicitacao)

        if categoria:
            query = query.filter(models.Solicitacao.categoria == categoria)

        if protocolo:
            query = query.filter(models.Solicitacao.protocolo.ilike(f"%{protocolo}%"))

        solicitacoes = query.order_by(models.Solicitacao.data_criacao.desc()).all()

        categorias = db.query(models.Solicitacao.categoria).distinct().all()
        categorias = [c[0] for c in categorias if c[0]]

        return templates.TemplateResponse("painel.html", {
            "request": request,
            "solicitacoes": solicitacoes,
            "categoria_selecionada": categoria,
            "protocolo_busca": protocolo,
            "categorias": categorias
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return HTMLResponse(content="Erro interno no servidor", status_code=500)

# ----------- ALTERAR STATUS (via painel HTML) -----------

@router.post("/atualizar-status/{protocolo}")
async def alterar_status(protocolo: str, status: str = Form(...), db: Session = Depends(get_db)):
    solicitacao = db.query(models.Solicitacao).filter(models.Solicitacao.protocolo == protocolo).first()
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    solicitacao.status = status
    db.commit()
    return RedirectResponse(url="/painel", status_code=302)

# ----------- ATUALIZAR ACOMPANHAMENTO -----------

@router.post("/atualizar-acompanhamento/{protocolo}")
def atualizar_acompanhamento(
    protocolo: str,
    acompanhamento: str = Form(...),
    db: Session = Depends(get_db)
):
    solicitacao = db.query(models.Solicitacao).filter(models.Solicitacao.protocolo == protocolo).first()
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    
    solicitacao.acompanhamentos = acompanhamento
    db.commit()
    return RedirectResponse(url="/painel", status_code=302)



# ----------- DETALHES HTML (painel ou público) -----------

@router.get("/solicitacoes/{protocolo}", response_class=HTMLResponse)
def detalhes_solicitacao(protocolo: str, request: Request, db: Session = Depends(get_db)):
    solicitacao = db.query(models.Solicitacao).filter(models.Solicitacao.protocolo == protocolo).first()
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    
    # Verifica se o usuário está autenticado
    autenticado = request.session.get("usuario") == "admin"

    return templates.TemplateResponse("detalhes.html", {
        "request": request,
        "s": solicitacao,
        "autenticado": autenticado
    })


# ----------- FORMULÁRIO HTML -----------

@router.get("/formulario", response_class=HTMLResponse)
def exibir_formulario(request: Request):
    return templates.TemplateResponse("formulario.html", {"request": request})

@router.post("/formulario")
async def salvar_formulario(
    request: Request,
    titulo: str = Form(...),
    categoria: str = Form(...),
    endereco: str = Form(...),
    urgencia: str = Form(...),
    descricao: Optional[str] = Form(None),
    nome: Optional[str] = Form(None),
    telefone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    try:
        novo_protocolo = f"AMOB-{uuid.uuid4().hex[:8].upper()}"
        nome_arquivo = None

        if foto:
            nome_arquivo = f"{novo_protocolo}_{foto.filename}"
            caminho = os.path.join(UPLOAD_FOLDER, nome_arquivo)
            with open(caminho, "wb") as buffer:
                buffer.write(await foto.read())

        nova = models.Solicitacao(
            protocolo=novo_protocolo,
            titulo=titulo,
            categoria=categoria,
            endereco=endereco,
            urgencia=urgencia,
            descricao=descricao,
            foto=nome_arquivo,
            nome=nome,
            telefone=telefone,
            email=email
        )
        db.add(nova)
        db.commit()
        db.refresh(nova)

        return RedirectResponse(url=f"/solicitacoes/{novo_protocolo}", status_code=302)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("formulario.html", {
            "request": request,
            "erro": "Erro ao enviar solicitação"
        })

# ----------- ROTAS API JSON -----------

@router.get("/teste")
def testar_roteamento():
    return {"message": "GET funcionando"}

@router.post("/solicitacoes", response_model=schemas.SolicitacaoResponse)
async def criar_solicitacao_com_foto(
    titulo: str = Form(...),
    categoria: str = Form(...),
    endereco: str = Form(...),
    urgencia: str = Form(...),
    descricao: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    novo_protocolo = f"AMOB-{uuid.uuid4().hex[:8].upper()}"
    nome_arquivo = None

    if foto:
        nome_arquivo = f"{novo_protocolo}_{foto.filename}"
        caminho = os.path.join(UPLOAD_FOLDER, nome_arquivo)
        with open(caminho, "wb") as buffer:
            buffer.write(await foto.read())

    nova = models.Solicitacao(
        protocolo=novo_protocolo,
        titulo=titulo,
        categoria=categoria,
        endereco=endereco,
        urgencia=urgencia,
        descricao=descricao,
        foto=nome_arquivo
    )
    db.add(nova)
    db.commit()
    db.refresh(nova)

    return nova

@router.get("/solicitacoes", response_model=list[schemas.SolicitacaoResponse])
def listar_solicitacoes(db: Session = Depends(get_db)):
    return db.query(models.Solicitacao).all()

@router.get("/api/solicitacoes/{protocolo}", response_model=schemas.SolicitacaoResponse)
def buscar_por_protocolo_api(protocolo: str, db: Session = Depends(get_db)):
    solicitacao = db.query(models.Solicitacao).filter(models.Solicitacao.protocolo == protocolo).first()
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    return solicitacao
