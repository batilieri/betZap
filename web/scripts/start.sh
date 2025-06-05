echo "Starting WhatsApp Atendimento..."

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Create default admin user if not exists
echo "Creating default admin user..."
python -c "
import asyncio
from app.core.database import AsyncSessionLocal
from app.crud.user import user
from app.schemas.user import UserCreate

async def create_admin():
    async with AsyncSessionLocal() as db:
        admin_user = await user.get_by_email(db, email='admin@admin.com')
        if not admin_user:
            user_in = UserCreate(
                email='admin@admin.com',
                name='Administrador',
                password='admin123',
                is_admin=True
            )
            await user.create(db, obj_in=user_in)
            print('Admin user created: admin@admin.com / admin123')
        else:
            print('Admin user already exists')

asyncio.run(create_admin())
"

# Start the application
echo "Starting FastAPI application..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload