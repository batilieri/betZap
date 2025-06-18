from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from core.database import get_db_session
from core.security import verify_token, security_manager
from models import User, UserRole
from crud.user import user_crud

logger = logging.getLogger(__name__)

# Esquema de autenticação Bearer
security = HTTPBearer(auto_error=False)


class AuthenticationError(HTTPException):
    """Exceção personalizada para erros de autenticação."""

    def __init__(self, detail: str = "Não autorizado"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(HTTPException):
    """Exceção personalizada para erros de autorização."""

    def __init__(self, detail: str = "Acesso negado"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class RateLimitError(HTTPException):
    """Exceção para rate limiting."""

    def __init__(self, detail: str = "Muitas tentativas. Tente novamente mais tarde."):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail
        )


class AuthManager:
    """Gerenciador de autenticação e autorização."""

    def __init__(self):
        self.failed_attempts: Dict[str, list] = {}  # IP -> lista de tentativas
        self.max_attempts = 5
        self.lockout_duration = timedelta(minutes=15)

    async def authenticate_user(self, email: str, password: str, db: AsyncSession) -> Optional[User]:
        """Autentica usuário por email e senha."""
        try:
            # Buscar usuário por email
            result = await db.execute(
                select(User).where(User.email == email, User.is_active == True)
            )
            user = result.scalar_one_or_none()

            if not user:
                return None

            # Verificar senha
            if not security_manager.verify_password(password, user.hashed_password):
                return None

            # Atualizar último acesso
            user.last_seen = datetime.utcnow()
            await db.commit()

            return user

        except Exception as e:
            logger.error(f"Erro na autenticação: {e}")
            return None

    def check_rate_limit(self, identifier: str) -> bool:
        """Verifica se o identificador (IP/email) está dentro do rate limit."""
        now = datetime.utcnow()

        if identifier not in self.failed_attempts:
            return True

        # Filtrar tentativas dentro da janela de tempo
        valid_attempts = [
            attempt for attempt in self.failed_attempts[identifier]
            if now - attempt < self.lockout_duration
        ]

        self.failed_attempts[identifier] = valid_attempts

        return len(valid_attempts) < self.max_attempts

    def record_failed_attempt(self, identifier: str):
        """Registra tentativa de login falhada."""
        now = datetime.utcnow()

        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []

        self.failed_attempts[identifier].append(now)

    def clear_failed_attempts(self, identifier: str):
        """Limpa tentativas falhadas após login bem-sucedido."""
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]


# Instância global
auth_manager = AuthManager()


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db_session)
) -> User:
    """Dependency para obter usuário atual."""
    if not credentials:
        raise AuthenticationError("Token de acesso requerido")

    try:
        # Verificar token
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")

        if user_id is None:
            raise AuthenticationError("Token inválido")

        # Buscar usuário no banco
        result = await db.execute(
            select(User).where(User.id == int(user_id), User.is_active == True)
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise AuthenticationError("Usuário não encontrado")

        # Atualizar último acesso
        user.last_seen = datetime.utcnow()
        await db.commit()

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter usuário atual: {e}")
        raise AuthenticationError("Erro na autenticação")


async def get_current_active_user(
        current_user: User = Depends(get_current_user)
) -> User:
    """Dependency para usuário ativo."""
    if not current_user.is_active:
        raise AuthenticationError("Usuário inativo")

    return current_user


async def get_current_verified_user(
        current_user: User = Depends(get_current_active_user)
) -> User:
    """Dependency para usuário verificado."""
    if not current_user.is_verified:
        raise AuthorizationError("Usuário não verificado")

    return current_user


def require_role(required_role: UserRole):
    """Decorator para exigir role específica."""

    async def role_checker(current_user: User = Depends(get_current_verified_user)) -> User:
        if current_user.role != required_role and current_user.role != UserRole.ADMIN:
            raise AuthorizationError(f"Role {required_role} requerida")
        return current_user

    return role_checker


def require_roles(required_roles: list[UserRole]):
    """Decorator para exigir uma das roles especificadas."""

    async def roles_checker(current_user: User = Depends(get_current_verified_user)) -> User:
        if current_user.role not in required_roles and current_user.role != UserRole.ADMIN:
            roles_str = ", ".join(required_roles)
            raise AuthorizationError(f"Uma das seguintes roles é requerida: {roles_str}")
        return current_user

    return roles_checker


async def get_optional_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db_session)
) -> Optional[User]:
    """Dependency para usuário opcional (pode ser None)."""
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def check_rate_limit_dependency():
    """Dependency para verificar rate limit."""

    async def rate_limit_checker(request: Request):
        client_ip = request.client.host

        if not auth_manager.check_rate_limit(client_ip):
            raise RateLimitError()

        return True

    return rate_limit_checker


class TokenData:
    """Classe para dados do token."""

    def __init__(self, user_id: int, email: str, role: str):
        self.user_id = user_id
        self.email = email
        self.role = role


async def create_user_tokens(user: User) -> Dict[str, str]:
    """Cria tokens de acesso e refresh para o usuário."""
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role
    }

    access_token = security_manager.create_access_token(token_data)
    refresh_token = security_manager.create_refresh_token({"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


async def refresh_access_token(refresh_token: str, db: AsyncSession) -> Dict[str, str]:
    """Renova token de acesso usando refresh token."""
    try:
        # Verificar refresh token
        payload = verify_token(refresh_token, "refresh")
        user_id = payload.get("sub")

        if user_id is None:
            raise AuthenticationError("Refresh token inválido")

        # Buscar usuário
        result = await db.execute(
            select(User).where(User.id == int(user_id), User.is_active == True)
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise AuthenticationError("Usuário não encontrado")

        # Criar novos tokens
        return await create_user_tokens(user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao renovar token: {e}")
        raise AuthenticationError("Erro na renovação do token")


# Dependencies exportadas
RequireAdmin = require_role(UserRole.ADMIN)
RequireModerator = require_roles([UserRole.ADMIN, UserRole.MODERATOR])
CheckRateLimit = check_rate_limit_dependency()