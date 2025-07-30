from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SolicitacaoBase(BaseModel):
    titulo: str
    categoria: str
    endereco: str
    urgencia: str
    descricao: Optional[str] = None

class SolicitacaoCreate(SolicitacaoBase):
    pass

class SolicitacaoResponse(SolicitacaoBase):
    id: int
    protocolo: str
    status: str
    data_criacao: datetime
    foto: Optional[str] = None  # Novo campo adicionado

    model_config = {
        "from_attributes": True
    }

class SolicitacaoStatusUpdate(BaseModel):
    status: str
