import click
import dcrx_kv
import pathlib
import uvicorn
from dcrx_kv.app import app


@click.group(help='Commands to manage the DCRX server.')
def server():
    pass


@server.command(help='Run the DCRX server.')
@click.option(
    '--host',
    default='0.0.0.0',
    help='Host address to run the DCRX server on.'
)
@click.option(
    '--port',
    default=2277,
    help='Port to run the DCRX server on.'
)
@click.option(
    '--reload',
    is_flag=True,
    help='Enable hot reload.'
)
@click.option(
    '--workers',
    default=1,
    help='Number of Uvicorn workers to use'
)
@click.option(
    '--log-level',
    default='info',
    help='Log level to use for Uvicorn'
)
def run(
    host: str,
    port: int,
    reload: bool,
    workers: int,
    log_level: str
):
    if reload:
        uvicorn.run(
            "dcrx_kv.app:app",
            host=host,
            port=port,
            reload=True,
            reload_dirs=[
                str(pathlib.Path(dcrx_kv.__file__).parent)
            ],
            log_level=log_level
        )

    elif workers > 1:
        uvicorn.run(
            "dcrx_kv.app:app",
            host=host,
            port=port,
            workers=workers,
            log_level=log_level
        )


    else:
        uvicorn.run(
            app, 
            host=host,
            port=port,
            log_level=log_level
        )