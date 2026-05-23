# env-limit-probe

A small, conservative Python script for checking coarse development-environment capabilities.

It prints **digits only**, so the result is easy to copy manually. The code intentionally avoids printing or storing:

- secrets, tokens, keys, passwords, or environment variable values
- hostnames, usernames, internal IPs, repository names, or local paths
- file contents
- internal network scan results

Use it only where you are allowed to run local diagnostic scripts and allowed to retain the resulting coarse capability code.

## Quick start

```bash
python3 env_probe.py
```

Windows:

```powershell
py env_probe.py
```

Example output:

```text
132145232011034101311010
```

## What the digits mean

Positions are 1-indexed from left to right.

- 1: schema version, currently `1`
- 2: OS — `1` Windows, `2` macOS, `3` Linux, `0` unknown
- 3: CPU architecture — `1` x86_64/amd64, `2` arm64/aarch64, `3` other x86, `0` unknown
- 4: privilege — `1` regular user, `2` root/admin-ish on Unix, `0` unknown
- 5: Python version — `1` < py3, `2` py3.0–3.7, `3` py3.8–3.9, `4` py3.10–3.11, `5` py3.12+
- 6: shell/terminal command count, 0–9
- 7: VCS command count, 0–3
- 8: scripting/runtime command count, 0–9
- 9: compiler/build command count, 0–9
- 10: container/Kubernetes command count, 0–4
- 11: network CLI command count, 0–5
- 12: pip/pip3 exists, `0/1`
- 13: conda/mamba exists, `0/1`
- 14: npm exists, `0/1`
- 15: docker exists, `0/1`
- 16: external connectivity — `0` no DNS, `1` DNS only, `2` TCP 443 only, `3` HTTPS HEAD works
- 17: public development endpoint reachability count, 0–4; checks PyPI, npm registry, GitHub, Docker Hub
- 18: proxy environment variable presence, `0/1`; presence only, values are not read out
- 19: no_proxy environment variable presence, `0/1`; presence only, values are not read out
- 20: writable filesystem locations count, 0–3; temp/current/home
- 21: temporary Python script execution works, `0/1`
- 22: git status — `0` no git, `1` git exists but not inside repo, `2` inside git repo
- 23: container-like environment detected, `0/1`
- 24: CI environment variable presence, `0/1`
- 25: virtual environment / conda / nvm / pyenv presence, `0/1`
- 26: custom CA/certificate environment variable presence, `0/1`

## Design constraints

The script is deliberately coarse. It is meant to answer questions like:

- Is Python usable?
- Are common development tools installed?
- Is external HTTPS blocked or allowed?
- Are public package registries reachable?
- Is the filesystem writable?
- Does this look like a container or CI environment?

It is **not** meant to fingerprint a company environment, enumerate internal systems, bypass security controls, discover secrets, or scan networks.

## Safety notes

- The only network checks are public endpoints via DNS/TCP/HTTPS HEAD.
- Internal/private IP ranges are not scanned.
- Environment variable values are never printed.
- File contents are never read except a Linux cgroup marker used only to return a single container-like bit.
- Temporary files are created only for write/execute checks and then removed.

## License

MIT
