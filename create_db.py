# create_db.py
from app.database import Base, engine
from app.models import Solicitacao

print("Criando as tabelas no banco...")
Base.metadata.create_all(bind=engine)
print("Tabelas criadas com sucesso.")
