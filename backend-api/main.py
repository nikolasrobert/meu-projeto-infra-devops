# =============================================================================
# Painel de Voos — API REST com FastAPI + SQLAlchemy (síncrono) + PostgreSQL
# =============================================================================

from datetime import datetime
from typing import Generator

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# -----------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DO BANCO DE DADOS
# -----------------------------------------------------------------------------

# URL de conexão direta com o PostgreSQL usando o driver psycopg2
DATABASE_URL = "postgresql://admin:senha_segura@127.0.0.1:5433/voos_db"

# Cria o motor de conexão (engine) do SQLAlchemy.
# connect_args vazio; check_same_thread é desnecessário para PostgreSQL,
# mas echo=True imprime as queries no terminal — útil para depuração.
engine = create_engine(DATABASE_URL, echo=True)

# Fábrica de sessões: cada requisição HTTP receberá sua própria sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# -----------------------------------------------------------------------------
# 2. MODELO ORM (tabela no banco)
# -----------------------------------------------------------------------------

class Base(DeclarativeBase):
    """Classe base da qual todos os modelos ORM herdam."""
    pass


class Voo(Base):
    """
    Representa a tabela 'voos' no banco de dados.

    Campos:
        codigo      — código único do voo (chave primária)
        gate        — número do portão de embarque
        boarding_time — data e hora do embarque
        status      — situação atual no painel
    """

    __tablename__ = "voos"

    # String única que identifica o voo (ex.: "LA1234") — chave primária
    codigo = Column(String, primary_key=True, unique=True, nullable=False)

    # Número inteiro do portão de embarque (ex.: 12)
    gate = Column(Integer, nullable=False)

    # Data e hora do início do embarque
    boarding_time = Column(DateTime, nullable=False)

    # Situação atual: 'proceed to gate' | 'boarding' | 'last call' | 'closed'
    status = Column(String, nullable=False)


# -----------------------------------------------------------------------------
# 3. INICIALIZAÇÃO — cria as tabelas automaticamente ao subir a API
# -----------------------------------------------------------------------------

# Criação das tabelas no banco. Caso já existam, o comando é ignorado.
Base.metadata.create_all(bind=engine)

# -----------------------------------------------------------------------------
# 4. INSTÂNCIA DO FASTAPI
# -----------------------------------------------------------------------------

app = FastAPI(
    title="Painel de Voos",
    description="API REST para consulta e gestão de voos em um painel de aeroporto.",
    version="1.0.0",
)

# -----------------------------------------------------------------------------
# 5. VALORES PERMITIDOS PARA O CAMPO STATUS
# -----------------------------------------------------------------------------

# Conjunto imutável com os únicos valores aceitos para o campo status
STATUS_VALIDOS = frozenset({"proceed to gate", "boarding", "last call", "closed"})


def validar_status(status: str) -> None:
    """
    Valida se o status informado é um dos quatro valores exatos permitidos.
    Lança HTTP 400 (Bad Request) caso o valor seja inválido.
    """
    if status not in STATUS_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Status '{status}' inválido. "
                "Os valores aceitos são: 'proceed to gate', 'boarding', "
                "'last call', 'closed'."
            ),
        )


# -----------------------------------------------------------------------------
# 6. SCHEMAS PYDANTIC (validação e serialização de dados)
# -----------------------------------------------------------------------------

class VooBase(BaseModel):
    """Campos base compartilhados entre criação e atualização."""

    gate: int
    boardingTime: datetime  # nome em camelCase para a API; mapeado para boarding_time no ORM
    status: str


class VooCreate(VooBase):
    """Payload esperado na criação de um novo voo (POST /voos)."""

    codigo: str


class VooUpdate(BaseModel):
    """
    Payload parcial para atualização de voo (PUT /voos/{codigo}).
    Todos os campos são opcionais: apenas os informados serão atualizados.
    """

    gate: int | None = None
    boardingTime: datetime | None = None
    status: str | None = None


class VooResponse(BaseModel):
    """Formato de saída de um voo nas respostas da API."""

    codigo: str
    gate: int
    boardingTime: datetime
    status: str

    # Permite que o Pydantic leia atributos diretamente de um objeto ORM
    model_config = {"from_attributes": True}


# -----------------------------------------------------------------------------
# 7. DEPENDÊNCIA DE SESSÃO DO BANCO
# -----------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """
    Dependência injetada nas rotas via FastAPI Depends.
    Abre uma sessão no início da requisição e a fecha ao final,
    garantindo que recursos do banco sejam sempre liberados.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------------------------------------------------------
# 8. ROTAS CRUD
# -----------------------------------------------------------------------------

@app.post("/voos", response_model=VooResponse, status_code=201)
def criar_voo(payload: VooCreate, db: Session = Depends(get_db)) -> VooResponse:
    """
    POST /voos — Cria um novo voo no banco de dados.

    Retorna 400 se:
      - o status não for um dos quatro valores permitidos.
      - já existir um voo com o mesmo código.
    Retorna 201 com os dados do voo criado em caso de sucesso.
    """
    # Valida o campo status antes de qualquer operação no banco
    validar_status(payload.status)

    # Impede duplicidade de código
    if db.get(Voo, payload.codigo) is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Já existe um voo com o código '{payload.codigo}'.",
        )

    # Cria a instância do ORM e persiste no banco
    novo_voo = Voo(
        codigo=payload.codigo,
        gate=payload.gate,
        boarding_time=payload.boardingTime,   # camelCase → snake_case
        status=payload.status,
    )
    db.add(novo_voo)
    db.commit()
    db.refresh(novo_voo)  # recarrega os dados persistidos do banco

    # Converte o ORM para o schema de resposta manualmente
    return VooResponse(
        codigo=novo_voo.codigo,
        gate=novo_voo.gate,
        boardingTime=novo_voo.boarding_time,
        status=novo_voo.status,
    )


@app.get("/voos", response_model=list[VooResponse])
def listar_voos(db: Session = Depends(get_db)) -> list[VooResponse]:
    """
    GET /voos — Retorna a lista de todos os voos cadastrados.

    Os voos são ordenados pelo código em ordem alfabética.
    """
    voos = db.query(Voo).order_by(Voo.codigo).all()

    return [
        VooResponse(
            codigo=v.codigo,
            gate=v.gate,
            boardingTime=v.boarding_time,
            status=v.status,
        )
        for v in voos
    ]


@app.put("/voos/{codigo}", response_model=VooResponse)
def atualizar_voo(
    codigo: str,
    payload: VooUpdate,
    db: Session = Depends(get_db),
) -> VooResponse:
    """
    PUT /voos/{codigo} — Atualiza os dados de um voo existente.

    Retorna 404 se o voo não for encontrado.
    Retorna 400 se o novo status for inválido.
    Apenas os campos informados no payload são alterados.
    """
    # Busca o voo pelo código (chave primária)
    voo = db.get(Voo, codigo)
    if voo is None:
        raise HTTPException(
            status_code=404,
            detail=f"Voo '{codigo}' não encontrado.",
        )

    # Atualiza somente os campos que vieram no payload
    if payload.gate is not None:
        voo.gate = payload.gate

    if payload.boardingTime is not None:
        voo.boarding_time = payload.boardingTime

    if payload.status is not None:
        validar_status(payload.status)  # valida antes de salvar
        voo.status = payload.status

    db.commit()
    db.refresh(voo)

    return VooResponse(
        codigo=voo.codigo,
        gate=voo.gate,
        boardingTime=voo.boarding_time,
        status=voo.status,
    )


@app.delete("/voos/{codigo}", status_code=204)
def remover_voo(codigo: str, db: Session = Depends(get_db)) -> None:
    """
    DELETE /voos/{codigo} — Remove um voo do banco de dados.

    Retorna 404 se o voo não for encontrado.
    Retorna 204 (sem conteúdo) em caso de sucesso.
    """
    voo = db.get(Voo, codigo)
    if voo is None:
        raise HTTPException(
            status_code=404,
            detail=f"Voo '{codigo}' não encontrado.",
        )

    db.delete(voo)
    db.commit()
