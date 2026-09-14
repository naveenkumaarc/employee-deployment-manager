from pathlib import Path

root = Path(SPECPATH)
assets = root / "assets"

a = Analysis(
    [str(root / "main.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(assets / "app_icon.png"), "assets"),
        (str(assets / "app_icon.ico"), "assets"),
        (str(assets / "app_icon.svg"), "assets"),
    ],
    hiddenimports=["openpyxl"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="DeploymentDesk",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(assets / "app_icon.ico"),
)
