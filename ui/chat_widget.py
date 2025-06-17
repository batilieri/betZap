from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
from datetime import datetime, timedelta
import uvicorn
import os

from database import get_db, engine, Base
from models import User, Contact, Chat, Message
from schemas import UserCreate, UserLogin, ContactCreate, ChatCreate, MessageCreate
from auth import get_password_hash, verify_password, create_access_token, get_current_user
from permissions import check_permissions, UserRole

# Criar tabelas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Gestão Web", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files e templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

security = HTTPBearer()


# Rotas de Autenticação
@app.post("/api/auth/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Verificar se usuário já existe
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    # Criar novo usuário
    hashed_password = get_password_hash(user.password)
    db_user = User(
        nome=user.nome,
        email=user.email,
        senha=hashed_password,
        role=user.role if user.role else UserRole.USER
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {"message": "Usuário criado com sucesso", "user_id": db_user.id}


@app.post("/api/auth/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.senha):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    access_token = create_access_token(data={"sub": str(db_user.id)})
    return {"access_token": access_token, "token_type": "bearer", "user": {
        "id": db_user.id,
        "nome": db_user.nome,
        "email": db_user.email,
        "role": db_user.role
    }}


# Rotas Web (Frontend)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/contacts", response_class=HTMLResponse)
async def contacts_page(request: Request):
    return templates.TemplateResponse("contacts.html", {"request": request})


@app.get("/chats", response_class=HTMLResponse)
async def chats_page(request: Request):
    return templates.TemplateResponse("chats.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


# API Routes - Contacts
@app.get("/api/contacts")
async def get_contacts(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if current_user.role == UserRole.ADMIN:
        contacts = db.query(Contact).all()
    else:
        contacts = db.query(Contact).filter(Contact.user_id == current_user.id).all()
    return contacts


@app.post("/api/contacts")
async def create_contact(
        contact: ContactCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    db_contact = Contact(
        nome=contact.nome,
        telefone=contact.telefone,
        email=contact.email,
        observacoes=contact.observacoes,
        user_id=current_user.id
    )
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


@app.put("/api/contacts/{contact_id}")
async def update_contact(
        contact_id: int,
        contact: ContactCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contato não encontrado")

    # Verificar permissão
    if current_user.role != UserRole.ADMIN and db_contact.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    db_contact.nome = contact.nome
    db_contact.telefone = contact.telefone
    db_contact.email = contact.email
    db_contact.observacoes = contact.observacoes
    db.commit()
    return db_contact


@app.delete("/api/contacts/{contact_id}")
async def delete_contact(
        contact_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contato não encontrado")

    # Verificar permissão
    if current_user.role != UserRole.ADMIN and db_contact.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    db.delete(db_contact)
    db.commit()
    return {"message": "Contato deletado com sucesso"}


# API Routes - Chats
@app.get("/api/chats")
async def get_chats(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if current_user.role == UserRole.ADMIN:
        chats = db.query(Chat).all()
    else:
        chats = db.query(Chat).filter(Chat.user_id == current_user.id).all()
    return chats


@app.post("/api/chats")
async def create_chat(
        chat: ChatCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    db_chat = Chat(
        titulo=chat.titulo,
        user_id=current_user.id,
        contact_id=chat.contact_id
    )
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat


@app.get("/api/chats/{chat_id}/messages")
async def get_chat_messages(
        chat_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat não encontrado")

    # Verificar permissão
    if current_user.role != UserRole.ADMIN and chat.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    messages = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.timestamp).all()
    return messages


@app.post("/api/chats/{chat_id}/messages")
async def create_message(
        chat_id: int,
        message: MessageCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat não encontrado")

    # Verificar permissão
    if current_user.role != UserRole.ADMIN and chat.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    db_message = Message(
        conteudo=message.conteudo,
        tipo=message.tipo,
        chat_id=chat_id
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


# API Routes - Admin
@app.get("/api/admin/users")
async def get_users(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    check_permissions(current_user, UserRole.ADMIN)
    users = db.query(User).all()
    return users


@app.put("/api/admin/users/{user_id}/role")
async def update_user_role(
        user_id: int,
        role: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    check_permissions(current_user, UserRole.ADMIN)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.role = role
    db.commit()
    return {"message": "Role atualizada com sucesso"}


@app.get("/api/admin/stats")
async def get_stats(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    check_permissions(current_user, UserRole.ADMIN)

    total_users = db.query(User).count()
    total_contacts = db.query(Contact).count()
    total_chats = db.query(Chat).count()
    total_messages = db.query(Message).count()

    return {
        "total_users": total_users,
        "total_contacts": total_contacts,
        "total_chats": total_chats,
        "total_messages": total_messages
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)