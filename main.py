import subprocess
import asyncio


async def archive():
    args = "zip - catalog/*"
    process = await asyncio.create_subprocess_shell(
        args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    chunk_size = 500 * 1024

    with open('archieve.zip', 'wb') as f:
        while not process.stdout.at_eof():
            chunk = await process.stdout.read(chunk_size)
            if chunk:
                f.write(chunk)
                print(f"Записали кусок размером {len(chunk)} байт")

    await process.wait()


asyncio.run(archive())
