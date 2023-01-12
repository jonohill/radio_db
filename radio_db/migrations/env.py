import asyncio
from logging.config import fileConfig

from alembic import context  # type: ignore
from radio_db.config import from_yaml as config_from_yaml
from radio_db.db import Base, RadioDatabase
from sqlalchemy.engine import Connection

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config # type: ignore

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name) # type: ignore

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata # type: ignore

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """

    db_conf = config_from_yaml().database
    rdb = RadioDatabase(db_conf.connection_string)
    context.configure( # type: ignore
        url=db_conf.connection_string,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction(): # type: ignore
        context.run_migrations() # type: ignore


def do_run_migrations(connection: Connection):
    context.configure(connection=connection, target_metadata=target_metadata) # type: ignore

    with context.begin_transaction(): # type: ignore
        context.run_migrations() # type: ignore


async def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # connectable = AsyncEngine(
    #     engine_from_config(
    #         config.get_section(config.config_ini_section),
    #         prefix="sqlalchemy.",
    #         poolclass=pool.NullPool,
    #         future=True,
    #     )
    # )

    db_conf = config_from_yaml().database
    rdb = RadioDatabase(db_conf.connection_string)
    connectable = rdb.create_engine()

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
