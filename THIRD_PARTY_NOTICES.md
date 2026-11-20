# Third party notices

The `ThirdParty/wokada` directory contains a minimal source subset from the existing project's copy of [w-okada/voice-changer](https://github.com/w-okada/voice-changer). It includes the two RVC ONNX synthesizer definitions and their five `infer_pack` dependencies. These files are copied without modification. The exact upstream commit of the local snapshot is not recorded; `SOURCE_MANIFEST.json` records SHA-256 hashes for this distribution.

The original MIT copyright and permission notices are preserved in `ThirdParty/wokada/LICENSE`. The original `LICENSE-NOTICE` is also retained. Other model families mentioned in that notice are not included in this distribution. No pretrained models, voice weights, HuBERT weights, RMVPE weights, sample audio or training data are bundled.

Python, PyTorch, NumPy, ONNX, ONNX Runtime and their transitive dependencies are installed separately. Their licenses remain with their installed packages. The release ZIP does not redistribute their binaries or the developer's Python environment.

Do not remove the included third-party license files when redistributing the converter. Voice model redistribution permissions are separate from these code licenses.
