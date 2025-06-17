#!/usr/bin/env python3
"""
Script de inicialização do Sistema de Gestão Web
Configura o banco de dados e inicia o servidor
"""

import os
import sys
from sqlalchemy.orm import Session
from database import engine, SessionLocal, init_db
from models import User
from auth import get_password_hash
from permissions import UserRole


def create_admin_user():
    """Criar usuário administrador padrão se não existir"""
    db = SessionLocal()
    try:
        # Verificar se já existe um admin
        admin_exists = db.query(User).filter(User.role == UserRole.ADMIN).first()

        if not admin_exists:
            admin_user = User(
                nome="Administrador",
                email="admin@sistema.com",
                senha=get_password_hash("admin123"),
                role=UserRole.ADMIN
            )
            db.add(admin_user)
            db.commit()
            print("✅ Usuário administrador criado:")
            print("   Email: admin@sistema.com")
            print("   Senha: admin123")
            print("   ⚠️  ALTERE A SENHA APÓS O PRIMEIRO LOGIN!")
        else:
            print("✅ Usuário administrador já existe")

    except Exception as e:
        print(f"❌ Erro ao criar usuário administrador: {e}")
        db.rollback()
    finally:
        db.close()


def setup_environment():
    """Configurar variáveis de ambiente necessárias"""
    # Definir variáveis padrão se não existirem
    env_vars = {
        'DATABASE_URL': 'sqlite:///./sistema_gestao.db',
        'SECRET_KEY': 'your-secret-key-change-in-production',
        'ACCESS_TOKEN_EXPIRE_MINUTES': '1440',
    }

    for key, default_value in env_vars.items():
        if not os.getenv(key):
            os.environ[key] = default_value


def create_directories():
    """Criar diretórios necessários"""
    directories = [
        'templates',
        'static',
        'static/css',
        'static/js',
        'static/images',
        'logs'
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Diretório criado/verificado: {directory}")


def initialize_database():
    """Inicializar banco de dados"""
    try:
        print("🔄 Inicializando banco de dados...")
        init_db()
        print("✅ Banco de dados inicializado com sucesso")

        # Criar usuário admin
        create_admin_user()

    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        sys.exit(1)


def main():
    """Função principal de inicialização"""
    print("🚀 Iniciando Sistema de Gestão Web")
    print("=" * 50)

    # Configurar ambiente
    print("🔧 Configurando ambiente...")
    setup_environment()

    # Criar diretórios
    print("📁 Criando diretórios...")
    create_directories()

    # Inicializar banco
    initialize_database()

    print("=" * 50)
    print("✅ Sistema pronto para uso!")
    print("\n📋 Informações importantes:")
    print("   - Acesse: http://localhost:8000")
    print("   - Login admin: admin@sistema.com")
    print("   - Senha admin: admin123")
    print("   - Altere a senha após o primeiro login!")
    print("\n🔧 Para rodar o servidor:")
    print("   python main.py")
    print("   ou")
    print("   uvicorn main:app --host 0.0.0.0 --port 8000 --reload")


if __name__ == "__main__":
    main()