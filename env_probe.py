#!/usr/bin/env python3
"""Safe coarse development-environment capability probe.

The script intentionally prints digits only. It does not print or store secrets,
hostnames, usernames, internal IPs, environment variable values, file contents,
repository names, or paths.

Use only in environments where you are allowed to run local diagnostic scripts
and allowed to retain the resulting coarse capability code.
"""

from __future__ import annotations

import os
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

TIMEOUT_SECONDS = 3


def bit(value: object) -> int:
    return 1 if value else 0


def has_cmd(cmd: str) -> int:
    return bit(shutil.which(cmd))


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


def http_head_ok(url: str, timeout: int = TIMEOUT_SECONDS) -> int:
    try:
        request = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(request, timeout=timeout) as response:
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


def env_present(names: list[str]) -> int:
    # Presence only. Values are never printed or stored.
    return bit(any(os.environ.get(name) for name in names))


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
    return min(9, sum(has_cmd(command) for command in commands))


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
        "https://registry.npmjs.org/",
        "https://github.com/",
        "https://registry-1.docker.io/v2/",
    ]
    return min(9, sum(http_head_ok(endpoint) for endpoint in endpoints))


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


def collect_digits() -> list[int]:
    return [
        1,  # schema version
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
        bit(has_cmd("pip") or has_cmd("pip3")),
        bit(has_cmd("conda") or has_cmd("mamba")),
        has_cmd("npm"),
        has_cmd("docker"),
        network_digit(),
        registry_digit(),
        env_present(["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]),
        env_present(["NO_PROXY", "no_proxy"]),
        filesystem_digit(),
        exec_test(),
        git_status_digit(),
        container_digit(),
        env_present(["CI", "GITHUB_ACTIONS", "GITLAB_CI", "JENKINS_URL", "BUILDKITE", "TEAMCITY_VERSION"]),
        env_present(["VIRTUAL_ENV", "CONDA_PREFIX", "PYENV_VERSION", "NVM_DIR"]),
        env_present(["SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "NODE_EXTRA_CA_CERTS"]),
    ]


def main() -> None:
    print("".join(str(int(digit)) for digit in collect_digits()))


if __name__ == "__main__":
    main()
