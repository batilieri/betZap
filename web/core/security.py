from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from .config import settings
import secrets
import bcrypt
import logging

logger = logging.getLogger(__name__)

# Configuração robusta para hash de senhas
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)


class SecurityManager:
    """Gerenciador centralizado de segurança."""

    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        self.refresh_token_expire_days = settings.refresh_token_expire_days

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica se a senha está correta."""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Erro ao verificar senha: {e}")
            return False

    def get_password_hash(self, password: str) -> str:
        """Gera hash da senha."""
        return pwd_context.hash(password)

    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Valida força da senha."""
        errors = []

        if len(password) < 8:
            errors.append("Senha deve ter pelo menos 8 caracteres")

        if not any(c.isupper() for c in password):
            errors.append("Senha deve conter pelo menos uma letra maiúscula")

        if not any(c.islower() for c in password):
            errors.append("Senha deve conter pelo menos uma letra minúscula")

        if not any(c.isdigit() for c in password):
            errors.append("Senha deve conter pelo menos um número")

        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Senha deve conter pelo menos um caractere especial")

        # Verificar sequências comuns
        common_sequences = ['123456', 'abcdef', 'qwerty', 'password']
        if any(seq in password.lower() for seq in common_sequences):
            errors.append("Senha não pode conter sequências comuns")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "strength": self._calculate_strength(password)
        }

    def _calculate_strength(self, password: str) -> str:
        """Calcula força da senha."""
        score = 0

        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if any(c.isupper() for c in password):
            score += 1
        if any(c.islower() for c in password):
            score += 1
        if any(c.isdigit() for c in password):
            score += 1
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 1

        if score <= 2:
            return "fraca"
        elif score <= 4:
            return "média"
        else:
            return "forte"

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Cria token de acesso."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({"exp": expire, "type": "access"})

        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Erro ao criar token de acesso: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno do servidor"
            )

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Cria token de refresh."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        to_encode.update({"exp": expire, "type": "refresh"})

        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Erro ao criar refresh token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno do servidor"
            )

    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verifica e decodifica token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Verificar tipo do token
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Tipo de token inválido"
                )

            # Verificar expiração
            exp = payload.get("exp")
            if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expirado"
                )

            return payload

        except JWTError as e:
            logger.warning(f"Token inválido: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
        except Exception as e:
            logger.error(f"Erro ao verificar token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno do servidor"
            )

    def generate_secure_token(self, length: int = 32) -> str:
        """Gera token seguro para verificação."""
        return secrets.token_urlsafe(length)

    def generate_otp(self, length: int = 6) -> str:
        """Gera código OTP numérico."""
        return ''.join(secrets.choice('0123456789') for _ in range(length))


# Instância global
security_manager = SecurityManager()


# Funções de conveniência
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return security_manager.verify_password(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return security_manager.get_password_hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    return security_manager.create_access_token(data, expires_delta)


def create_refresh_token(data: Dict[str, Any]) -> str:
    return security_manager.create_refresh_token(data)


def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    return security_manager.verify_token(token, token_type)


def validate_password_strength(password: str) -> Dict[str, Any]:
    return security_manager.validate_password_strength(password)