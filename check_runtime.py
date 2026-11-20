"""Verify the distribution runtime without opening or uploading a model."""
from importlib import import_module, metadata
from pathlib import Path
import struct
import sys


def main():
    if not ((3, 10) <= sys.version_info[:2] <= (3, 12)) or struct.calcsize('P') != 8:
        raise RuntimeError('Python 3.10-3.12 x64 is required.')
    expected = {'torch': '2.6.0+cpu', 'numpy': '1.26.4', 'onnx': '1.17.0', 'onnxruntime': '1.23.0'}
    for package, version in expected.items():
        actual = metadata.version(package)
        if actual != version:
            raise RuntimeError(f'{package}: expected {version}, found {actual}. Run Setup.bat.')
        import_module(package)
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'ThirdParty' / 'wokada'))
    for dim in (256, 768):
        import_module(f'voice_changer.RVC.onnxExporter.SynthesizerTrnMs{dim}NSFsid_ONNX')
    print('READY: CPU runtime and bundled RVC v1/v2 definitions loaded.')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'Runtime not ready: {error}', file=sys.stderr)
        sys.exit(1)
