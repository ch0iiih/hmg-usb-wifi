"""Sign and archive built packages using an external HMG-API author key."""
from pathlib import Path
import json
import os
import subprocess
import sys
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parents[1]
classes = os.environ['HMGAPI_ENGINE_CLASSES']
key = Path(sys.argv[1]).resolve()
if key.is_relative_to(root):
    raise SystemExit('Keep your private signing key outside the public repository.')
for ident in ['usb-wifi-rtl8822bu', 'wifi-client-test']:
    folder = root / 'packages' / ident
    for operation, arguments in [('sign', [str(key)]), ('verify', [])]:
        subprocess.run(['java', '-cp', classes, 'hmgapi.engine.Signing',
                        operation, str(folder), *arguments], check=True)
    version = json.loads((folder / 'mod.json').read_text())['version']
    target = root / 'dist' / f'{ident}-{version}.zip'
    target.parent.mkdir(exist_ok=True)
    with ZipFile(target, 'w', ZIP_DEFLATED) as archive:
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(folder))
    print(target.name)
