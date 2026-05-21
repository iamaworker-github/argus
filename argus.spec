# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Argus standalone binary."""

import os
import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['argus/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('argus/ui/**/*.tcss', 'argus/ui'),
        ('argus/skills/*.md', 'argus/skills'),
        ('argus/prompts/*.txt', 'argus/prompts'),
    ],
    hiddenimports=[
        'argus.core',
        'argus.core.blackboard',
        'argus.core.cvss_scorer',
        'argus.core.llm_deduplicator',
        'argus.core.pr_generator',
        'argus.core.thinking_chain',
        'argus.core.todo_manager',
        'argus.core.events',
        'argus.agents',
        'argus.agents.base_agent',
        'argus.agents.orchestrator',
        'argus.agents.modes',
        'argus.agents.llm_client',
        'argus.toolkit',
        'argus.ui',
        'argus.reporting',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'notebook',
        'ipykernel',
        'jupyter_client',
        'pandas',
        'PIL',
        'cv2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='argus',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='argus/ui/assets/icon.ico' if Path('argus/ui/assets/icon.ico').exists() else None,
)

# Build script: pyinstaller argus.spec --clean --onefile
