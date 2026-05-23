#!/usr/bin/env python3
"""Safe coarse development-environment capability probe.

The script intentionally prints digits only. It does not print or store secrets,
hostnames, usernames, internal IPs, environment variable values, file contents,
repository names, or paths.

Default mode is low-noise: local checks plus a bounded set of public DNS/TCP/HEAD
checks. It does not scan internal networks, install packages, or download package
artifacts. Optional pip dry-run checks are opt-in via ENV_PROBE_PIP_DRY_RUN=1.

Use only in environments where you are allowed to run local diagnostic scripts
and allowed to retain the resulting coarse capability code.
"""

from __future__ import annotations

import importlib.util
import os
import platform
import shutil
import socket
import ssl
import subprocess
import sys
import sysconfig
import tempfile
import urllib.request
import venv
from pathlib import Path

TIMEOUT_SECONDS = 3
PIP_TIMEOUT_SECONDS = 8
SCHEMA_VERSION = 3


PIP_DRY_RUN_PROFILES = [
    ("small", "packaging"),
    ("data", "numpy"),
    ("image", "opencv-python-headless"),
    ("notebook", "ipykernel"),
    ("ml", "scikit-learn"),
    ("dl", "torch"),
    ("llm", "transformers"),
]


def bit(value: object) -> int:
    return 1 if value else 0


def clamp_digit(value: int) -> int:
    return max(0, min(9, int(value)))


def has_cmd(cmd: str) -> int:
    return bit(shutil.which(cmd))


def has_any_cmd(commands: list[str]) -> int:
    return bit(any(shutil.which(command) for command in commands))


def run_ok(cmd: list[str], timeout: int = TIMEOUT_SECONDS) -> int:
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            shell=False,
            check=False,
        )
        return bit(result.returncode == 0)
    except Exception:
        return 0


def run_returncode(cmd: list[str], timeout: int = TIMEOUT_SECONDS) -> int:
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            shell=False,
            check=False,
        )
        return int(result.returncode)
    except Exception:
        return 255


def python_snippet_code(code: str, timeout: int = TIMEOUT_SECONDS) -> int:
    return run_returncode([sys.executable, "-c", code], timeout=timeout)


def http_head_ok(url: str, timeout: int = TIMEOUT_SECONDS) -> int:
    try:
        request = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", 0)
            return bit(200 <= status < 500)
    except Exception:
        return 0


def http_get_tiny_ok(url: str, timeout: int = TIMEOUT_SECONDS) -> int:
    try:
        request = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response.read(64)
            status = getattr(response, "status", 0)
            return bit(200 <= status < 500)
    except Exception:
        return 0


def tcp_ok(host: str, port: int, timeout: int = TIMEOUT_SECONDS) -> int:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return 1
    except Exception:
        return 0


def write_test(directory: str) -> int:
    try:
        path = Path(directory)
        if not path.exists() or not path.is_dir():
            return 0
        with tempfile.NamedTemporaryFile(dir=str(path), delete=True) as handle:
            handle.write(b"x")
            handle.flush()
        return 1
    except Exception:
        return 0


def exec_test() -> int:
    try:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "probe_exec_test.py"
            path.write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
            return run_ok([sys.executable, str(path)])
    except Exception:
        return 0


def shell_script_exec_test() -> int:
    if os.name == "nt":
        return 0
    try:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "probe_exec_test.sh"
            path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            path.chmod(0o700)
            return run_ok([str(path)])
    except Exception:
        return 0


def env_present(names: list[str]) -> int:
    # Presence only. Values are never printed or stored.
    return bit(any(os.environ.get(name) for name in names))


def module_present(module_name: str) -> int:
    try:
        return bit(importlib.util.find_spec(module_name) is not None)
    except Exception:
        return 0


def module_group_score(module_names: list[str]) -> int:
    return clamp_digit(sum(module_present(name) for name in module_names))


def os_digit() -> int:
    system = platform.system().lower()
    if "windows" in system:
        return 1
    if "darwin" in system:
        return 2
    if "linux" in system:
        return 3
    return 0


def arch_digit() -> int:
    machine = platform.machine().lower()
    if machine in {"x86_64", "amd64"}:
        return 1
    if machine in {"arm64", "aarch64"}:
        return 2
    if "86" in machine:
        return 3
    return 0


def admin_digit() -> int:
    try:
        if os.name == "nt":
            return 0
        return 2 if os.geteuid() == 0 else 1
    except Exception:
        return 0


def python_digit() -> int:
    if sys.version_info.major < 3:
        return 1
    minor = sys.version_info.minor
    if minor < 8:
        return 2
    if minor < 10:
        return 3
    if minor < 12:
        return 4
    return 5


def tool_score(commands: list[str]) -> int:
    return clamp_digit(sum(has_cmd(command) for command in commands))


def network_digit() -> int:
    # Coarse external connectivity only. No internal endpoints are touched.
    # 0: no DNS; 1: DNS only; 2: TCP 443 only; 3: HTTPS HEAD works.
    try:
        socket.gethostbyname("example.com")
    except Exception:
        return 0

    if not tcp_ok("example.com", 443):
        return 1

    if not http_head_ok("https://example.com/"):
        return 2

    return 3


def registry_digit() -> int:
    # Public development endpoints, HEAD only.
    endpoints = [
        "https://pypi.org/",
        "https://files.pythonhosted.org/",
        "https://registry.npmjs.org/",
        "https://github.com/",
        "https://raw.githubusercontent.com/",
        "https://huggingface.co/",
        "https://conda.anaconda.org/",
        "https://registry-1.docker.io/v2/",
    ]
    return clamp_digit(sum(http_head_ok(endpoint) for endpoint in endpoints))


def pypi_package_head_score() -> int:
    # Checks package index pages only; does not install packages or fetch wheels.
    packages = [
        "numpy",
        "pandas",
        "scipy",
        "matplotlib",
        "jupyterlab",
        "torch",
        "transformers",
        "opencv-python",
        "scikit-learn",
    ]
    return clamp_digit(sum(http_head_ok(f"https://pypi.org/simple/{name}/") for name in packages))


def pip_available() -> int:
    return bit(has_cmd("pip") or has_cmd("pip3") or run_ok([sys.executable, "-m", "pip", "--version"]))


def pip_dry_run_digit(package: str) -> int:
    # Opt-in because this may contact PyPI and resolve package metadata. It uses --dry-run,
    # --no-deps, and --only-binary, so it should not install anything.
    # 0 not requested; 1 pip unavailable; 2 dry-run failed; 3 dry-run succeeded.
    if os.environ.get("ENV_PROBE_PIP_DRY_RUN") != "1":
        return 0
    pip_cmd = [sys.executable, "-m", "pip"]
    if not run_ok(pip_cmd + ["--version"]):
        return 1
    cmd = pip_cmd + [
        "install",
        "--dry-run",
        "--no-deps",
        "--only-binary=:all:",
        "--disable-pip-version-check",
        "--no-input",
        "--retries=0",
        f"--timeout={PIP_TIMEOUT_SECONDS}",
        package,
    ]
    return 3 if run_ok(cmd, timeout=PIP_TIMEOUT_SECONDS + 4) else 2


def pip_index_digit() -> int:
    # Opt-in; contacts package index metadata without installing packages.
    # 0 not requested; 1 pip unavailable; 2 command unsupported/failed; 3 succeeded.
    if os.environ.get("ENV_PROBE_PIP_DRY_RUN") != "1":
        return 0
    pip_cmd = [sys.executable, "-m", "pip"]
    if not run_ok(pip_cmd + ["--version"]):
        return 1
    cmd = pip_cmd + [
        "index",
        "versions",
        "packaging",
        "--disable-pip-version-check",
        "--retries=0",
        f"--timeout={PIP_TIMEOUT_SECONDS}",
    ]
    return 3 if run_ok(cmd, timeout=PIP_TIMEOUT_SECONDS + 4) else 2


def venv_digit() -> int:
    # 0 failed; 1 venv dir created; 2 venv python runs; 3 venv pip runs.
    try:
        with tempfile.TemporaryDirectory() as directory:
            venv_dir = Path(directory) / "v"
            builder = venv.EnvBuilder(with_pip=True, clear=True)
            builder.create(str(venv_dir))
            python_path = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            pip_path = venv_dir / ("Scripts/pip.exe" if os.name == "nt" else "bin/pip")
            if not venv_dir.exists():
                return 0
            if not run_ok([str(python_path), "-c", "import sys; sys.exit(0)"], timeout=8):
                return 1
            if run_ok([str(pip_path), "--version"], timeout=8):
                return 3
            return 2
    except Exception:
        return 0


def user_site_digit() -> int:
    # 0 unknown/not writable; 1 user base writable; 2 user site writable/existing or creatable.
    try:
        import site

        score = 0
        user_base = getattr(site, "USER_BASE", None)
        user_site = site.getusersitepackages() if hasattr(site, "getusersitepackages") else None
        if user_base:
            score += write_test(user_base)
        if user_site:
            Path(user_site).mkdir(parents=True, exist_ok=True)
            score += write_test(user_site)
        return clamp_digit(score)
    except Exception:
        return 0


def site_packages_writable_digit() -> int:
    # Coarse count of writable active install locations; no path is printed.
    keys = ["purelib", "platlib"]
    paths: list[str] = []
    for key in keys:
        try:
            value = sysconfig.get_paths().get(key)
            if value and value not in paths:
                paths.append(value)
        except Exception:
            pass
    return clamp_digit(sum(write_test(path) for path in paths))


def ssl_digit() -> int:
    # 0 context failed; 1 context works; 2 HTTPS tiny GET to PyPI works;
    # 3 HTTPS tiny GET to PyPI and files.pythonhosted works.
    try:
        ssl.create_default_context()
    except Exception:
        return 0
    score = 1
    score += http_get_tiny_ok("https://pypi.org/simple/packaging/")
    score += http_get_tiny_ok("https://files.pythonhosted.org/")
    return clamp_digit(score)


def requests_https_digit() -> int:
    # 0 requests absent; 1 import/check failed; 2 HTTPS GET worked.
    if not module_present("requests"):
        return 0
    code = """
import sys
try:
    import requests
    r = requests.get('https://pypi.org/simple/packaging/', timeout=3, stream=True)
    r.close()
    sys.exit(2 if 200 <= r.status_code < 500 else 1)
except Exception:
    sys.exit(1)
"""
    rc = python_snippet_code(code, timeout=6)
    return rc if rc in {1, 2} else 1


def localhost_digit() -> int:
    # 0 failed; 1 bind works; 2 bind + loopback connect works.
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            port = server.getsockname()[1]
            with socket.create_connection(("127.0.0.1", port), timeout=TIMEOUT_SECONDS):
                pass
            conn, _addr = server.accept()
            conn.close()
            return 2
    except Exception:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                server.bind(("127.0.0.1", 0))
                return 1
        except Exception:
            return 0


def filesystem_digit() -> int:
    score = 0
    score += write_test(tempfile.gettempdir())
    score += write_test(os.getcwd())
    score += write_test(str(Path.home()))
    return score


def git_status_digit() -> int:
    # 0: no git; 1: git exists, not inside repo; 2: inside git repo.
    if not has_cmd("git"):
        return 0
    return 2 if run_ok(["git", "rev-parse", "--is-inside-work-tree"]) else 1


def container_digit() -> int:
    try:
        if Path("/.dockerenv").exists():
            return 1
        cgroup = Path("/proc/1/cgroup")
        if cgroup.exists():
            text = cgroup.read_text(errors="ignore").lower()
            markers = ("docker", "kubepods", "containerd", "podman")
            if any(marker in text for marker in markers):
                return 1
    except Exception:
        pass
    return 0


def cuda_path_digit() -> int:
    candidates = [
        os.environ.get("CUDA_HOME"),
        os.environ.get("CUDA_PATH"),
        "/usr/local/cuda",
        "/opt/cuda",
    ]
    return bit(any(candidate and Path(candidate).exists() for candidate in candidates))


def gpu_runtime_digit() -> int:
    # 0 none observed; 1 NVIDIA CLI only; 2 CUDA toolkit only; 3 both; 4 Apple MPS likely.
    nvidia = run_ok(["nvidia-smi", "-L"]) if has_cmd("nvidia-smi") else 0
    nvcc = run_ok(["nvcc", "--version"]) if has_cmd("nvcc") else 0
    if nvidia and nvcc:
        return 3
    if nvcc:
        return 2
    if nvidia:
        return 1
    if os_digit() == 2 and arch_digit() == 2:
        return 4
    return 0


def nvidia_gpu_count_digit() -> int:
    # 0 no nvidia-smi/count failed; 1 one GPU; 2 two or more GPUs.
    if not has_cmd("nvidia-smi"):
        return 0
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=5,
            shell=False,
            check=False,
            text=True,
        )
        if result.returncode != 0:
            return 0
        count = len([line for line in result.stdout.splitlines() if line.strip()])
        if count >= 2:
            return 2
        if count == 1:
            return 1
        return 0
    except Exception:
        return 0


def torch_cuda_digit() -> int:
    # 0 torch absent; 1 torch import failed; 2 torch imports but CUDA/MPS unavailable;
    # 3 torch CUDA available; 4 torch MPS available.
    if not module_present("torch"):
        return 0
    code = """
import sys
try:
    import torch
    if getattr(torch, 'cuda', None) is not None and torch.cuda.is_available():
        sys.exit(3)
    if hasattr(torch, 'backends') and hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        sys.exit(4)
    sys.exit(2)
except Exception:
    sys.exit(1)
"""
    rc = python_snippet_code(code, timeout=8)
    return rc if rc in {1, 2, 3, 4} else 1


def torch_cuda_count_digit() -> int:
    # 0 torch absent/import failed/no CUDA; 1 one CUDA GPU; 2 two or more CUDA GPUs.
    if not module_present("torch"):
        return 0
    code = """
import sys
try:
    import torch
    if not torch.cuda.is_available():
        sys.exit(0)
    count = torch.cuda.device_count()
    sys.exit(2 if count >= 2 else 1 if count == 1 else 0)
except Exception:
    sys.exit(0)
"""
    rc = python_snippet_code(code, timeout=8)
    return rc if rc in {0, 1, 2} else 0


def tensorflow_gpu_digit() -> int:
    # 0 tensorflow absent; 1 import failed/no GPU; 2 GPU visible.
    if not module_present("tensorflow"):
        return 0
    code = """
import sys
try:
    import tensorflow as tf
    sys.exit(2 if tf.config.list_physical_devices('GPU') else 1)
except Exception:
    sys.exit(1)
"""
    rc = python_snippet_code(code, timeout=10)
    return rc if rc in {1, 2} else 1


def cupy_digit() -> int:
    # 0 cupy absent; 1 import failed or no CUDA device; 2 cupy sees CUDA device.
    if not module_present("cupy"):
        return 0
    code = """
import sys
try:
    import cupy
    sys.exit(2 if cupy.cuda.runtime.getDeviceCount() > 0 else 1)
except Exception:
    sys.exit(1)
"""
    rc = python_snippet_code(code, timeout=8)
    return rc if rc in {1, 2} else 1


def docker_runtime_digit() -> int:
    # 0 no docker cmd; 1 client exists; 2 daemon reachable.
    if not has_cmd("docker"):
        return 0
    return 2 if run_ok(["docker", "info"], timeout=5) else 1


def powershell_exec_digit() -> int:
    # 0 absent/not applicable; 1 pwsh/powershell exists but command failed; 2 command works.
    command = shutil.which("pwsh") or shutil.which("powershell")
    if not command:
        return 0
    return 2 if run_ok([command, "-NoProfile", "-Command", "exit 0"], timeout=5) else 1


def collect_digits() -> list[int]:
    digits = [
        SCHEMA_VERSION,
        os_digit(),
        arch_digit(),
        admin_digit(),
        python_digit(),
        tool_score(["bash", "zsh", "sh", "pwsh", "powershell", "cmd"]),
        tool_score(["git", "svn", "hg"]),
        tool_score(["python", "python3", "node", "npm", "npx", "pnpm", "yarn", "uv", "uvx"]),
        tool_score(["gcc", "g++", "clang", "clang++", "make", "cmake", "go", "rustc", "cargo"]),
        tool_score(["docker", "podman", "kubectl", "helm"]),
        tool_score(["curl", "wget", "ssh", "scp", "rsync"]),
        tool_score(["code", "vim", "nvim", "emacs", "nano"]),
        tool_score(["java", "javac", "mvn", "gradle"]),
        tool_score(["R", "Rscript", "julia", "matlab"]),
        pip_available(),
        bit(has_cmd("conda") or has_cmd("mamba") or has_cmd("micromamba")),
        has_cmd("npm"),
        docker_runtime_digit(),
        network_digit(),
        registry_digit(),
        pypi_package_head_score(),
    ]

    digits.extend(pip_dry_run_digit(package) for _name, package in PIP_DRY_RUN_PROFILES)

    digits.extend(
        [
            pip_index_digit(),
            env_present(["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]),
            env_present(["NO_PROXY", "no_proxy"]),
            env_present(["PIP_INDEX_URL", "PIP_EXTRA_INDEX_URL", "PIP_CONFIG_FILE"]),
            env_present(["CONDA_CHANNELS", "CONDA_OVERRIDE_CUDA"]),
            filesystem_digit(),
            exec_test(),
            shell_script_exec_test(),
            powershell_exec_digit(),
            venv_digit(),
            user_site_digit(),
            site_packages_writable_digit(),
            git_status_digit(),
            container_digit(),
            env_present(["CI", "GITHUB_ACTIONS", "GITLAB_CI", "JENKINS_URL", "BUILDKITE", "TEAMCITY_VERSION"]),
            env_present(["VIRTUAL_ENV", "CONDA_PREFIX", "PYENV_VERSION", "NVM_DIR"]),
            env_present(["SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "NODE_EXTRA_CA_CERTS"]),
            ssl_digit(),
            requests_https_digit(),
            localhost_digit(),
            gpu_runtime_digit(),
            nvidia_gpu_count_digit(),
            cuda_path_digit(),
            env_present(["CUDA_HOME", "CUDA_PATH", "NVIDIA_VISIBLE_DEVICES", "NVIDIA_DRIVER_CAPABILITIES"]),
            torch_cuda_digit(),
            torch_cuda_count_digit(),
            tensorflow_gpu_digit(),
            cupy_digit(),
            module_group_score(["numpy", "scipy", "pandas", "pyarrow", "polars"]),
            module_group_score(["matplotlib", "seaborn", "plotly", "bokeh", "altair"]),
            module_group_score(["sklearn", "statsmodels", "xgboost", "lightgbm", "catboost"]),
            module_group_score(["cv2", "PIL", "skimage", "imageio", "tifffile"]),
            module_group_score(["torch", "tensorflow", "jax", "keras", "transformers", "datasets", "accelerate", "diffusers", "sentence_transformers"]),
            module_group_score(["jupyter", "jupyterlab", "IPython", "ipykernel", "notebook"]),
            module_group_score(["pytest", "hypothesis", "ruff", "black", "mypy", "pre_commit"]),
            module_group_score(["requests", "httpx", "aiohttp", "fastapi", "flask", "uvicorn", "pydantic"]),
            module_group_score(["sqlalchemy", "psycopg2", "pymysql", "duckdb", "sqlite3"]),
            module_group_score(["openpyxl", "xlrd", "xlsxwriter", "docx", "pptx", "fitz", "pdfplumber"]),
            module_group_score(["h5py", "tables", "zarr", "netCDF4", "xarray"]),
            module_group_score(["numba", "cupy", "dask", "joblib", "ray"]),
            module_group_score(["streamlit", "gradio", "dash", "panel"]),
            module_group_score(["pytesseract", "easyocr", "paddleocr", "onnxruntime", "openvino"]),
            has_any_cmd(["nvidia-smi", "nvcc", "rocm-smi", "rocminfo"]),
            tool_score(["nvidia-smi", "nvcc", "rocm-smi", "rocminfo", "clinfo"]),
            tool_score(["slurm", "srun", "sbatch", "qsub", "bsub"]),
        ]
    )
    return digits


def main() -> None:
    print("".join(str(int(digit)) for digit in collect_digits()))


if __name__ == "__main__":
    main()
