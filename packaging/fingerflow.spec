# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

try:
    spec_dir = Path(__file__).resolve().parent
except NameError:
    spec_dir = Path.cwd().resolve()
    if (spec_dir / "packaging").is_dir():
        spec_dir = spec_dir / "packaging"
project_dir = spec_dir.parent if spec_dir.name == "packaging" else spec_dir

datas = [
    (os.path.join(project_dir, "fingerflow", "ui"), "fingerflow/ui"),
    (os.path.join(project_dir, "model"), "model"),
]
datas += collect_data_files("mediapipe")

hiddenimports = collect_submodules("mediapipe")

block_cipher = None

a = Analysis(
    [os.path.join(project_dir, "packaging", "entrypoint.py")],
    pathex=[project_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "torch",
        "mediapipe.tasks.python.genai.converter",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="FingerFlow",
    icon=os.path.join(project_dir, "fingerflow", "ui", "Logo_fingerflow_V2.ico"),
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="FingerFlow",
)
