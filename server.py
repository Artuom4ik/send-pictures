import os
import argparse
import asyncio
import datetime
import logging

from aiohttp import web
import aiofiles


def get_settings():
    parser = argparse.ArgumentParser(
        description='This is an archive server',
    )

    parser.add_argument(
        "-f",
        "--folder",
        type=str,
        default="test_photos",
        help="Folder with photos"
    )
    parser.add_argument("-l", "--log", type=bool, default=False, help="Log")
    parser.add_argument(
        "-d",
        "--delay",
        type=bool,
        default=False,
        help="Delay"
    )

    return parser.parse_args()


async def test_archive(request):
    settings = get_settings()

    photo_folder = settings.folder
    delay = settings.delay
    log = settings.log

    archive_hash = request.match_info['archive_hash']
    archive_name = f"{archive_hash}.zip"
    archive_path = os.path.join('archives', archive_name)
    photos_path = os.path.join(photo_folder, archive_hash)
    args = f"zip -r - *"

    try:
        process = await asyncio.create_subprocess_shell(
            args,
            cwd=photos_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

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
                    logging.info(
                        f"Sending archive chunk {len(chunk)} bytes") if log else None
                    await response.write(chunk)

                    await asyncio.sleep(1) if delay else None

        await response.write_eof()

    except FileNotFoundError:
        return web.HTTPNotFound(text="Архив не существует или был удален")

    except asyncio.CancelledError:
        print("Download was interrupted")
        raise

    finally:
        process.terminate()

    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    settings = get_settings()

    if settings.log:
        logging.basicConfig(filename='sending.log', level=logging.INFO)

    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', test_archive),
    ])
    web.run_app(app)
