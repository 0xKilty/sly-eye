import subprocess
import tempfile
import json
import zipfile
import shutil

def run_semgrep_on_wheel(tar_path, rules="auto"):
    tmpdir = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(tar_path, "r") as zipf:
            zipf.extractall(tmpdir)
        proc = subprocess.run(
            ["semgrep", "scan", tmpdir, "--config", rules, "--json", "--quiet"],
            capture_output=True,
            text=True,
            check=False
        )
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
