import subprocess
import tempfile
import json
import tarfile
import shutil

def run_guarddog_on_tarball(tar_path, rules="auto"):
    tmpdir = tempfile.mkdtemp()
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(tmpdir)

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