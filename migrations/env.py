import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Este es el objeto de configuración de Alembic, que proporciona
# acceso a los valores dentro del archivo alembic.ini en uso.
config = context.config

# Interpretar el archivo de configuración para el registro (logging).
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ----------------------------------------------------------------
# FUNCIÓN PARA LEER DINÁMICAMENTE LA URL DESDE TU ENTORNO
# ----------------------------------------------------------------
def get_url():
    # Toma DATABASE_URL del entorno. Si no existe, usa tu string local por defecto.
    # Usamos mysql+pymysql para que SQLAlchemy sepa qué driver utilizar en Python.
    return os.getenv(
        "DATABASE_URL", 
        "mysql+pymysql://root:secret@127.0.0.1:3306/shipments"
    )

def run_migrations_offline() -> None:
    """Ejecuta migraciones en modo 'offline'."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=None, # Al usar SQL nativo en tus repositorios, se queda en None
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecuta migraciones en modo 'online'."""
    # Extraemos la sección de configuración del archivo ini
    configuration = config.get_section(config.config_ini_section) or {}
    # Sobreescribimos la propiedad sqlalchemy.url con nuestra función dinámica
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=None
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()