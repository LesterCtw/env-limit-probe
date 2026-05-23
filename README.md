# env-limit-probe

A conservative Python script for checking coarse development-environment capabilities.

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
222145232011034101311010000000000000000000000000000
```

## Low-noise behavior

Default mode is intentionally low-noise:

- local command checks use `PATH` lookup or short subprocess checks
- Python package checks use `importlib.util.find_spec`, not full imports, except the explicit PyTorch accelerator check
- network checks touch only public endpoints with DNS/TCP/HTTPS HEAD
- no internal/private network scanning
- no package installation
- no package artifact download by default
- no environment variable values are printed

There is one opt-in check for whether `pip install --dry-run` can resolve a public package:

```bash
ENV_PROBE_PIP_DRY_RUN=1 python3 env_probe.py
```

That opt-in check still does not install packages, but it may contact PyPI and resolve package metadata. Leave it off if you want the lowest-noise run.

## What the digits mean

Positions are 1-indexed from left to right. Schema version `2` outputs 50 digits.

- 1: schema version, currently `2`
- 2: OS — `1` Windows, `2` macOS, `3` Linux, `0` unknown
- 3: CPU architecture — `1` x86_64/amd64, `2` arm64/aarch64, `3` other x86, `0` unknown
- 4: privilege — `1` regular user, `2` root/admin-ish on Unix, `0` unknown
- 5: Python version — `1` < py3, `2` py3.0–3.7, `3` py3.8–3.9, `4` py3.10–3.11, `5` py3.12+
- 6: shell/terminal command count, 0–9; bash/zsh/sh/pwsh/powershell/cmd
- 7: VCS command count, 0–3; git/svn/hg
- 8: scripting/runtime command count, 0–9; python/python3/node/npm/npx/pnpm/yarn/uv/uvx
- 9: compiler/build command count, 0–9; gcc/g++/clang/clang++/make/cmake/go/rustc/cargo
- 10: container/Kubernetes command count, 0–4; docker/podman/kubectl/helm
- 11: network CLI command count, 0–5; curl/wget/ssh/scp/rsync
- 12: editor command count, 0–5; code/vim/nvim/emacs/nano
- 13: Java/JVM tool count, 0–4; java/javac/mvn/gradle
- 14: scientific language tool count, 0–4; R/Rscript/julia/matlab
- 15: pip exists, `0/1`; checks pip/pip3/python -m pip
- 16: conda-like command exists, `0/1`; conda/mamba/micromamba
- 17: npm exists, `0/1`
- 18: Docker runtime — `0` no docker command, `1` client exists, `2` daemon reachable
- 19: external connectivity — `0` no DNS, `1` DNS only, `2` TCP 443 only, `3` HTTPS HEAD works
- 20: public development endpoint reachability count, 0–8; PyPI, files.pythonhosted, npm registry, GitHub, raw GitHub, Hugging Face, conda-forge host, Docker Hub
- 21: PyPI common-package simple-index reachability count, 0–9; numpy/pandas/scipy/matplotlib/jupyterlab/torch/transformers/opencv-python/scikit-learn
- 22: pip dry-run result — `0` not requested, `1` pip unavailable, `2` dry-run failed, `3` dry-run succeeded
- 23: proxy environment variable presence, `0/1`; presence only, values are not read out
- 24: no_proxy environment variable presence, `0/1`; presence only, values are not read out
- 25: pip index/config environment variable presence, `0/1`; presence only
- 26: conda channel/CUDA override environment variable presence, `0/1`; presence only
- 27: writable filesystem locations count, 0–3; temp/current/home
- 28: temporary Python script execution works, `0/1`
- 29: git status — `0` no git, `1` git exists but not inside repo, `2` inside git repo
- 30: container-like environment detected, `0/1`
- 31: CI environment variable presence, `0/1`
- 32: virtual environment / conda / nvm / pyenv presence, `0/1`
- 33: custom CA/certificate environment variable presence, `0/1`
- 34: GPU runtime — `0` none observed, `1` NVIDIA driver CLI works, `2` CUDA toolkit works, `3` both NVIDIA driver CLI and CUDA toolkit work, `4` Apple Silicon MPS likely
- 35: CUDA path exists, `0/1`; checks CUDA_HOME/CUDA_PATH and common CUDA paths
- 36: CUDA/NVIDIA environment variable presence, `0/1`; presence only
- 37: PyTorch accelerator — `0` torch absent, `1` torch import failed, `2` torch imports but CUDA/MPS unavailable, `3` torch CUDA available, `4` torch MPS available
- 38: core data package count, 0–5; numpy/scipy/pandas/pyarrow/polars
- 39: visualization package count, 0–5; matplotlib/seaborn/plotly/bokeh/altair
- 40: classical ML package count, 0–5; sklearn/statsmodels/xgboost/lightgbm/catboost
- 41: image/vision package count, 0–5; cv2/PIL/skimage/imageio/tifffile
- 42: deep learning / LLM package count, 0–9; torch/tensorflow/jax/keras/transformers/datasets/accelerate/diffusers/sentence_transformers
- 43: notebook package count, 0–5; jupyter/jupyterlab/IPython/ipykernel/notebook
- 44: Python dev/test package count, 0–6; pytest/hypothesis/ruff/black/mypy/pre_commit
- 45: web/API package count, 0–7; requests/httpx/aiohttp/fastapi/flask/uvicorn/pydantic
- 46: database package count, 0–5; sqlalchemy/psycopg2/pymysql/duckdb/sqlite3
- 47: office/document package count, 0–7; openpyxl/xlrd/xlsxwriter/docx/pptx/fitz/pdfplumber
- 48: GPU command presence, `0/1`; any of nvidia-smi/nvcc/rocm-smi/rocminfo
- 49: GPU/OpenCL command count, 0–5; nvidia-smi/nvcc/rocm-smi/rocminfo/clinfo
- 50: scheduler/HPC command count, 0–5; slurm/srun/sbatch/qsub/bsub

## Design constraints

The script is deliberately coarse. It is meant to answer questions like:

- Is Python usable?
- Are common development tools installed?
- Is `pip` present, and optionally can it dry-run against PyPI?
- Are common data science / image / ML / notebook / dev packages already import-discoverable?
- Are CUDA/NVIDIA/PyTorch accelerator paths available?
- Are common public package registries reachable?
- Is the filesystem writable?
- Does this look like a container, CI, Docker, or HPC environment?

It is **not** meant to fingerprint a company environment, enumerate internal systems, bypass security controls, discover secrets, or scan networks.

## Safety notes

- The only default network checks are public endpoints via DNS/TCP/HTTPS HEAD.
- Internal/private IP ranges are not scanned.
- Environment variable values are never printed.
- File contents are never read except a Linux cgroup marker used only to return a single container-like bit.
- Temporary files are created only for write/execute checks and then removed.
- `ENV_PROBE_PIP_DRY_RUN=1` is opt-in and uses `pip install --dry-run --no-deps --only-binary=:all:` against a harmless public package.

## License

MIT
