from enum import Enum
from fastapi import HTTPException, status
from models import User


class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"


class Permission:
    """Classe para definir permissões específicas"""

    # Permissões de contatos
    CREATE_CONTACT = "create_contact"
    READ_OWN_CONTACTS = "read_own_contacts"
    READ_ALL_CONTACTS = "read_all_contacts"
    UPDATE_OWN_CONTACTS = "update_own_contacts"
    UPDATE_ALL_CONTACTS = "update_all_contacts"
    DELETE_OWN_CONTACTS = "delete_own_contacts"
    DELETE_ALL_CONTACTS = "delete_all_contacts"

    # Permissões de chats
    CREATE_CHAT = "create_chat"
    READ_OWN_CHATS = "read_own_chats"
    READ_ALL_CHATS = "read_all_chats"
    UPDATE_OWN_CHATS = "update_own_chats"
    UPDATE_ALL_CHATS = "update_all_chats"
    DELETE_OWN_CHATS = "delete_own_chats"
    DELETE_ALL_CHATS = "delete_all_chats"

    # Permissões de mensagens
    CREATE_MESSAGE = "create_message"
    READ_OWN_MESSAGES = "read_own_messages"
    READ_ALL_MESSAGES = "read_all_messages"

    # Permissões administrativas
    MANAGE_USERS = "manage_users"
    VIEW_ADMIN_DASHBOARD = "view_admin_dashboard"
    MANAGE_SYSTEM = "manage_system"


# Mapeamento de roles para permissões
ROLE_PERMISSIONS = {
    UserRole.USER: [
        Permission.CREATE_CONTACT,
        Permission.READ_OWN_CONTACTS,
        Permission.UPDATE_OWN_CONTACTS,
        Permission.DELETE_OWN_CONTACTS,
        Permission.CREATE_CHAT,
        Permission.READ_OWN_CHATS,
        Permission.UPDATE_OWN_CHATS,
        Permission.DELETE_OWN_CHATS,
        Permission.CREATE_MESSAGE,
        Permission.READ_OWN_MESSAGES,
    ],
    UserRole.MANAGER: [
        Permission.CREATE_CONTACT,
        Permission.READ_OWN_CONTACTS,
        Permission.READ_ALL_CONTACTS,
        Permission.UPDATE_OWN_CONTACTS,
        Permission.UPDATE_ALL_CONTACTS,
        Permission.DELETE_OWN_CONTACTS,
        Permission.CREATE_CHAT,
        Permission.READ_OWN_CHATS,
        Permission.READ_ALL_CHATS,
        Permission.UPDATE_OWN_CHATS,
        Permission.UPDATE_ALL_CHATS,
        Permission.DELETE_OWN_CHATS,
        Permission.CREATE_MESSAGE,
        Permission.READ_OWN_MESSAGES,
        Permission.READ_ALL_MESSAGES,
    ],
    UserRole.ADMIN: [
        # Admin tem todas as permissões
        Permission.CREATE_CONTACT,
        Permission.READ_OWN_CONTACTS,
        Permission.READ_ALL_CONTACTS,
        Permission.UPDATE_OWN_CONTACTS,
        Permission.UPDATE_ALL_CONTACTS,
        Permission.DELETE_OWN_CONTACTS,
        Permission.DELETE_ALL_CONTACTS,
        Permission.CREATE_CHAT,
        Permission.READ_OWN_CHATS,
        Permission.READ_ALL_CHATS,
        Permission.UPDATE_OWN_CHATS,
        Permission.UPDATE_ALL_CHATS,
        Permission.DELETE_OWN_CHATS,
        Permission.DELETE_ALL_CHATS,
        Permission.CREATE_MESSAGE,
        Permission.READ_OWN_MESSAGES,
        Permission.READ_ALL_MESSAGES,
        Permission.MANAGE_USERS,
        Permission.VIEW_ADMIN_DASHBOARD,
        Permission.MANAGE_SYSTEM,
    ]
}


def has_permission(user: User, permission: str) -> bool:
    """Verificar se o usuário tem uma permissão específica"""
    user_permissions = ROLE_PERMISSIONS.get(user.role, [])
    return permission in user_permissions


def check_permissions(user: User, required_role: UserRole = None, required_permission: str = None):
    """
    Verificar se o usuário tem o role ou permissão necessária
    Levanta HTTPException se não tiver permissão
    """
    if required_role:
        # Hierarquia de roles: ADMIN > MANAGER > USER
        role_hierarchy = {
            UserRole.USER: 1,
            UserRole.MANAGER: 2,
            UserRole.ADMIN: 3
        }

        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Role necessária: {required_role}"
            )

    if required_permission:
        if not has_permission(user, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Permissão necessária: {required_permission}"
            )


def can_access_resource(user: User, resource_owner_id: int, admin_permission: str = None) -> bool:
    """
    Verificar se o usuário pode acessar um recurso específico
    - Próprio usuário sempre pode acessar seus recursos
    - Admin pode acessar todos os recursos
    - Manager pode acessar com permissão específica
    """
    # Próprio recurso
    if user.id == resource_owner_id:
        return True

    # Admin sempre pode acessar
    if user.role == UserRole.ADMIN:
        return True

    # Manager com permissão específica
    if user.role == UserRole.MANAGER and admin_permission:
        return has_permission(user, admin_permission)

    return False


def require_resource_access(user: User, resource_owner_id: int, admin_permission: str = None):
    """
    Garantir acesso ao recurso ou levantar exceção
    """
    if not can_access_resource(user, resource_owner_id, admin_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado a este recurso"
        )