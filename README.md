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
3221331770422010103690000000000003110320200113224000000000010001110000000
```

Schema version `3` outputs **73 digits**.

## Optional pip dry-run profile

Default mode does **not** ask pip to resolve packages. To test whether pip can resolve common package wheels without installing anything:

```bash
ENV_PROBE_PIP_DRY_RUN=1 python3 env_probe.py
```

The opt-in check uses:

```bash
python -m pip install --dry-run --no-deps --only-binary=:all: --disable-pip-version-check --no-input --retries=0
```

It checks representative packages only; it does not install packages.

## Low-noise behavior

Default mode is intentionally bounded:

- local command checks use `PATH` lookup or short subprocess checks
- Python package checks mostly use `importlib.util.find_spec`, not full imports
- heavier imports are limited to explicit accelerator checks: PyTorch, TensorFlow, CuPy, and optional `requests` HTTPS
- network checks touch only public endpoints with DNS/TCP/HTTPS HEAD or tiny GET
- no internal/private network scanning
- no package installation
- no package artifact download by default
- no environment variable values are printed

## Digit decoder

Positions are 1-indexed from left to right.

- 1: schema version, currently `3`
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
- 20: public development endpoint reachability count, 0–8; PyPI, files.pythonhosted, npm registry, GitHub, raw GitHub, Hugging Face, conda host, Docker Hub
- 21: PyPI common-package simple-index reachability count, 0–9; numpy/pandas/scipy/matplotlib/jupyterlab/torch/transformers/opencv-python/scikit-learn
- 22: opt-in pip dry-run small package, `0` not requested, `1` pip unavailable, `2` failed, `3` succeeded; package: packaging
- 23: opt-in pip dry-run data package; package: numpy
- 24: opt-in pip dry-run image package; package: opencv-python-headless
- 25: opt-in pip dry-run notebook package; package: ipykernel
- 26: opt-in pip dry-run classical ML package; package: scikit-learn
- 27: opt-in pip dry-run deep learning package; package: torch
- 28: opt-in pip dry-run LLM package; package: transformers
- 29: opt-in `pip index versions packaging`, `0` not requested, `1` pip unavailable, `2` failed/unsupported, `3` succeeded
- 30: proxy environment variable presence, `0/1`; presence only, values are not read out
- 31: no_proxy environment variable presence, `0/1`; presence only, values are not read out
- 32: pip index/config environment variable presence, `0/1`; presence only
- 33: conda channel/CUDA override environment variable presence, `0/1`; presence only
- 34: writable filesystem locations count, 0–3; temp/current/home
- 35: temporary Python script execution works, `0/1`
- 36: temporary Unix shell script execution works, `0/1`; `0` on Windows/not applicable
- 37: PowerShell command execution — `0` absent/not applicable, `1` exists but failed, `2` works
- 38: Python venv ability — `0` failed, `1` venv dir created, `2` venv python runs, `3` venv pip runs
- 39: Python user install location writability, 0–2; user base and user site
- 40: active Python site-packages writability count, 0–2; purelib/platlib
- 41: git status — `0` no git, `1` git exists but not inside repo, `2` inside git repo
- 42: container-like environment detected, `0/1`
- 43: CI environment variable presence, `0/1`
- 44: virtual environment / conda / nvm / pyenv presence, `0/1`
- 45: custom CA/certificate environment variable presence, `0/1`
- 46: Python SSL/HTTPS — `0` SSL context failed, `1` context works, `2` PyPI tiny HTTPS GET works, `3` PyPI and files.pythonhosted tiny HTTPS GET work
- 47: requests HTTPS — `0` requests absent, `1` import/check failed, `2` HTTPS GET worked
- 48: localhost loopback dev-server ability — `0` failed, `1` bind works, `2` bind + connect works
- 49: GPU runtime — `0` none observed, `1` NVIDIA driver CLI works, `2` CUDA toolkit works, `3` both NVIDIA driver CLI and CUDA toolkit work, `4` Apple Silicon MPS likely
- 50: NVIDIA GPU count bucket — `0` none/unknown, `1` one GPU, `2` two or more GPUs
- 51: CUDA path exists, `0/1`; checks CUDA_HOME/CUDA_PATH and common CUDA paths
- 52: CUDA/NVIDIA environment variable presence, `0/1`; presence only
- 53: PyTorch accelerator — `0` torch absent, `1` torch import failed, `2` torch imports but CUDA/MPS unavailable, `3` torch CUDA available, `4` torch MPS available
- 54: PyTorch CUDA GPU count bucket — `0` absent/no CUDA/unknown, `1` one GPU, `2` two or more GPUs
- 55: TensorFlow GPU — `0` tensorflow absent, `1` import works/fails but no GPU visible, `2` GPU visible
- 56: CuPy CUDA — `0` cupy absent, `1` import failed or no CUDA device, `2` CUDA device visible
- 57: core data package count, 0–5; numpy/scipy/pandas/pyarrow/polars
- 58: visualization package count, 0–5; matplotlib/seaborn/plotly/bokeh/altair
- 59: classical ML package count, 0–5; sklearn/statsmodels/xgboost/lightgbm/catboost
- 60: image/vision package count, 0–5; cv2/PIL/skimage/imageio/tifffile
- 61: deep learning / LLM package count, 0–9; torch/tensorflow/jax/keras/transformers/datasets/accelerate/diffusers/sentence_transformers
- 62: notebook package count, 0–5; jupyter/jupyterlab/IPython/ipykernel/notebook
- 63: Python dev/test package count, 0–6; pytest/hypothesis/ruff/black/mypy/pre_commit
- 64: web/API package count, 0–7; requests/httpx/aiohttp/fastapi/flask/uvicorn/pydantic
- 65: database package count, 0–5; sqlalchemy/psycopg2/pymysql/duckdb/sqlite3
- 66: office/document package count, 0–7; openpyxl/xlrd/xlsxwriter/docx/pptx/fitz/pdfplumber
- 67: scientific IO package count, 0–5; h5py/tables/zarr/netCDF4/xarray
- 68: accelerated/parallel package count, 0–5; numba/cupy/dask/joblib/ray
- 69: local app UI package count, 0–4; streamlit/gradio/dash/panel
- 70: OCR/inference package count, 0–5; pytesseract/easyocr/paddleocr/onnxruntime/openvino
- 71: GPU command presence, `0/1`; any of nvidia-smi/nvcc/rocm-smi/rocminfo
- 72: GPU/OpenCL command count, 0–5; nvidia-smi/nvcc/rocm-smi/rocminfo/clinfo
- 73: scheduler/HPC command count, 0–5; slurm/srun/sbatch/qsub/bsub

## Quick interpretation for AI / FA automation work

Useful clusters:

- Python/pip viability: positions 15, 21–29, 38–40, 46–47
- CUDA/GPU viability: positions 49–56, 71–72
- image / scientific data workflows: positions 57, 60, 66–68, 70
- local notebook / UI tools: positions 48, 62, 69
- corporate proxy/SSL clues: positions 23–33, 45–47
- container / CI / HPC: positions 18, 42–43, 73

## Design constraints

The script is deliberately coarse. It is meant to answer questions like:

- Is Python usable?
- Are common development tools installed?
- Is `pip` present, and optionally can it dry-run against representative public wheels?
- Can Python create a venv and run venv pip?
- Do Python SSL / requests / pip-style HTTPS checks work?
- Can localhost bind/connect for Jupyter, FastAPI, Streamlit, or Gradio-like tools?
- Are common data science / image / ML / notebook / dev packages already discoverable?
- Are CUDA/NVIDIA/PyTorch/TensorFlow/CuPy accelerator paths available?
- Are common public package registries reachable?
- Is the filesystem writable?
- Does this look like a container, CI, Docker, or HPC environment?

It is **not** meant to fingerprint a company environment, enumerate internal systems, bypass security controls, discover secrets, or scan networks.

## Safety notes

- The only default network checks are public endpoints via DNS/TCP/HTTPS HEAD or tiny GET.
- Internal/private IP ranges are not scanned.
- Environment variable values are never printed.
- File contents are never read except a Linux cgroup marker used only to return a single container-like bit.
- Temporary files are created only for write/execute/venv checks and then removed.
- `ENV_PROBE_PIP_DRY_RUN=1` is opt-in and uses pip dry-run commands without installing packages.

## License

MIT
