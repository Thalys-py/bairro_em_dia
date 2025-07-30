from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Solicitacao(Base):
    __tablename__ = "solicitacoes"

    id = Column(Integer, primary_key=True, index=True)
    protocolo = Column(String, unique=True, index=True)
    titulo = Column(String, nullable=False)
    categoria = Column(String, nullable=False)
    endereco = Column(String, nullable=False)
    urgencia = Column(String, nullable=False)
    descricao = Column(Text, nullable=True)
    status = Column(String, default="Pendente")
    foto = Column(String, nullable=True)
    nome = Column(String, nullable=True)
    telefone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    acompanhamentos = Column(Text, nullable=True)
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())
    data_atualizacao = Column(DateTime(timezone=True), onupdate=func.now())
