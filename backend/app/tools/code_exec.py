import asyncio
import sys
import tempfile

from langchain_core.tools import tool

from app.core.config import get_settings


@tool
async def python_repl(code: str) -> str:
    """Run Python code and return stdout/stderr. Use print() to show results. Requires human approval.

    NOTE: runs in a subprocess with a timeout, which is NOT a security sandbox.
    Use a container or a service such as E2B for untrusted production workloads."""
    timeout = get_settings().python_repl_timeout
    with tempfile.TemporaryDirectory() as tmp:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-I", "-c", code,
            cwd=tmp, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
        )
        try:
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except TimeoutError:
            proc.kill()
            return f"Timed out after {timeout}s."
    text = out.decode(errors="replace").strip()
    return (text[:6000] or "(no output)") + ("" if proc.returncode == 0 else f"\n[exit code {proc.returncode}]")
