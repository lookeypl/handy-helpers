# -*- mode: python ; coding: utf-8 -*-


InfoWriterToEDL = Analysis(
    ['InfoWriterToEDL.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
InfoWriterToEDL_pyz = PYZ(InfoWriterToEDL.pure)

InfoWriterToEDL_exe = EXE(
    InfoWriterToEDL_pyz,
    InfoWriterToEDL.scripts,
    [],
    exclude_binaries=True,
    name='InfoWriterToEDL',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

EDLToYouTubeTimestamp = Analysis(
    ['EDLToYouTubeTimestamp.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
EDLToYouTubeTimestamp_pyz = PYZ(EDLToYouTubeTimestamp.pure)

EDLToYouTubeTimestamp_exe = EXE(
    EDLToYouTubeTimestamp_pyz,
    EDLToYouTubeTimestamp.scripts,
    [],
    exclude_binaries=True,
    name='EDLToYouTubeTimestamp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    InfoWriterToEDL_exe,
    EDLToYouTubeTimestamp_exe,
    InfoWriterToEDL.binaries,
    InfoWriterToEDL.datas,
    EDLToYouTubeTimestamp.binaries,
    EDLToYouTubeTimestamp.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='handy-helpers',
)
