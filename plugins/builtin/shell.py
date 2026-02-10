"""
Shell Plugin: Execute system commands.
"""
import subprocess
import asyncio

async def run(command: str):
    print(f"[Shell] Running: {command}")
    # Use asyncio.create_subprocess_shell for true async execution
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    if process.returncode == 0:
        return stdout.decode().strip()
    return f"Error: {stderr.decode().strip()}"
