import asyncio
import logging
import os
from tempfile import NamedTemporaryFile
import urllib.parse
from aiohttp import web

import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger()


async def upload_handler(request):
    reader = await request.multipart()

    content = None
    async for field in reader:
        if field.name == 'file':
            content = field
            break

    if not content:
        return web.json_response(
            {'error': 'Invalid post data'},
            status=web.HTTPBadRequest.status_code
        )

    _, extension = os.path.splitext(content.filename)

    size = 0
    with NamedTemporaryFile(
        'wb',
        dir=config.upload_dir,
        delete=False,
        prefix='h',
        suffix=extension
    ) as f:
        filename = os.path.basename(f.name)
        logger.info('Writing to {}'.format(filename))
        while 1:
            chunk = await content.read_chunk()
            if not chunk:
                break
            size += len(chunk)
            f.write(chunk)

    logger.info('Wrote {} bytes to {}'.format(size, filename))

    return web.json_response({
        'size': size,
        'url': urllib.parse.urljoin(config.http_path, filename)
    })


app = web.Application()
app.router.add_post('/', upload_handler)

if __name__ == '__main__':
    web.run_app(
        app,
        host='127.0.0.1',
        port=config.port
    )