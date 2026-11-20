"""Build a clean, model-free distribution from an explicit file allowlist."""
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parent
FILES = (
    'ONNX Export.bat', 'Run-Exporter.ps1', 'Setup.bat', 'Setup-Exporter.ps1',
    'export_rvc.py', 'check_runtime.py', 'requirements.txt', 'VERSION.txt',
    'README.md', 'GUIDE.ko.md', 'GUIDE.en.md', 'THIRD_PARTY_NOTICES.md',
    'ThirdParty/wokada/SOURCE_MANIFEST.json',
)


def main():
    version = (ROOT / 'VERSION.txt').read_text(encoding='utf-8').strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('VERSION.txt must contain a semantic version, for example 1.0.0.')
    manifest = json.loads((ROOT / 'ThirdParty/wokada/SOURCE_MANIFEST.json').read_text(encoding='utf-8-sig'))
    files = list(FILES)
    for relative, expected in manifest['sha256'].items():
        source = (ROOT / 'ThirdParty/wokada' / relative).resolve()
        source.relative_to((ROOT / 'ThirdParty/wokada').resolve())
        if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
            raise ValueError(f'Bundled source changed: {relative}')
        files.append('ThirdParty/wokada/' + relative)
    # Read all inputs before writing a release, so missing files cannot leave a partial ZIP.
    payload = [(relative, (ROOT / relative).read_bytes()) for relative in files]
    name = f'DoppelEcho-VoiceModelConverter-{version}-Windows'
    destination = ROOT / 'dist'
    destination.mkdir(exist_ok=True)
    archive = destination / (name + '.zip')
    staged = destination / (name + '.zip.tmp')
    with zipfile.ZipFile(staged, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as out:
        for relative, content in sorted(payload):
            info = zipfile.ZipInfo(name + '/' + relative, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            out.writestr(info, content)
    staged.replace(archive)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(f'{digest}  {archive.name}\n', encoding='ascii')
    print(f'{archive}\n{len(payload)} files; {archive.stat().st_size:,} bytes\nSHA256 {digest}')


if __name__ == '__main__':
    main()
