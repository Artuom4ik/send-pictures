import os
import asyncio
import datetime
import logging

from aiohttp import web
import aiofiles


async def test_archive(request):
    archive_hash = request.match_info['archive_hash']
    archive_name = f"{archive_hash}.zip"
    archive_path = os.path.join('archives', archive_name)
    photos_directory = os.path.join("test_photos", archive_hash)
    args = f"zip -r - *"

    try:
        process = await asyncio.create_subprocess_shell(
            args,
            cwd=photos_directory,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

    except FileNotFoundError:
        return web.HTTPNotFound(text="Архив не существует или был удален")

    response = web.StreamResponse()
    response.headers['Content-Type'] = 'application/zip'
    response.headers['Content-Disposition'] = f'attachment; filename="{archive_name}"'
    await response.prepare(request)

    chunk_size = 500 * 1024

    with open(archive_path, 'wb') as f:
        while not process.stdout.at_eof():
            chunk = await process.stdout.read(chunk_size)
            if chunk:
                f.write(chunk)
                logging.info(f"Sending archive chunk {len(chunk)} bytes")
                await response.write(chunk)

    await response.write_eof()
    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    logging.basicConfig(filename='sending.log', level=logging.INFO)
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', test_archive),
    ])
    web.run_app(app)
