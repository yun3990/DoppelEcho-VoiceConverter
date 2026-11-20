# Doppel Echo Voice Model Converter Guide

Convert an RVC inference `.pth` voice model to the w-okada-compatible ONNX format used by Doppel Echo. Start with the original `.pth`; this tool cannot repair or re-export an ONNX file from another exporter. The converter is for model creators, not ordinary players.

## Requirements

**RVC v1 is recommended for Doppel Echo.** v2 can also be exported, but slight audio distortion may occur with whispering or certain vocal pitch ranges in the game. Listen to these conditions as well as normal speech. Export validation alone cannot establish in-game audio quality.

- Windows 10 or 11, 64-bit. Conversion runs on the CPU; NVIDIA hardware and CUDA are not required.
- **Python 3.10, 3.11 or 3.12, Windows installer 64-bit**, from [python.org](https://www.python.org/downloads/windows/). Include pip and the Python Launcher when installing. Python 3.13 and newer are not supported by this package.
- Internet access for initial setup and several GB of free space for dependencies and conversion. Setup downloads packages from the official PyPI and PyTorch servers.
- A standard **RVC v1 inference `.pth` with f0 enabled is recommended**. v2 can also be exported; see the audio quality note above. The converter accepts models at 32,000, 40,000 or 48,000 Hz.

Training checkpoints such as `G_*.pth` and `D_*.pth`, non-f0 models, alternate `params` checkpoints and existing `.onnx` files are not supported. An `.index` file is not used in conversion. No voice models or training data are included.

## First setup

1. Extract the entire ZIP to a writable folder. Do not run it inside the ZIP.
2. Double-click `ONNX Export.bat` and choose `Yes` when asked to set up the converter. You may also run `Setup.bat` separately.
3. If Python is not detected, select the `python.exe` of a supported installation. If Python is not installed, cancel, install it, and try again.
4. Wait for `Setup complete`. Packages are installed in this tool's `.venv` folder; the game's voice server environment is not changed.

After setup, conversion works offline. Do not distribute or move an installed `.venv`. On another PC or in a new location, extract the original ZIP and run setup again.

## Convert a model

1. Run `ONNX Export.bat`.
2. Select your `.pth` in the input dialog.
3. Choose the output `.onnx` name and location. Replacing an existing file requires confirmation.
4. Keep the console open until `Export and validation succeeded` appears. Processing time depends on your model and PC.

The original `.pth` is never edited. An existing output is replaced only after export and validation succeed. Conversion logs are saved under `logs/export-*.log`.

## Output and validation

The output is a single CPU FP32, ONNX opset 17 file. Inputs are `feats`, `p_len`, `pitch`, `pitchf` and `sid`; the output is `audio`. Model version and sample rate metadata are included.

The converter checks the graph, input names and types, and inference at 32/64/97 frames for expected audio length, finite values and non-silent output. These checks do not replace listening tests in the game or GPU-specific validation. The FP32 file can be larger than the source checkpoint.

## Workshop preparation

This package **only converts files**. It does not log in to Steam, upload content, subscribe to items or register a model in the game. Use the resulting `.onnx` when the game's Workshop upload feature is available. Upload UI instructions will accompany that feature.

Only share models you have permission to distribute and retain the model author's required credits and terms. The converter's code licenses do not grant rights to a voice model.

## Troubleshooting

| Problem | Action |
|---|---|
| Python not found | Install a supported 64-bit Python and select its `python.exe`. Use a full installation, not an embedded game runtime |
| Package download failed | Check the connection, rerun `Setup.bat`, and read `logs/setup-*.log` |
| DLL load failed | Check Python architecture and the Microsoft Visual C++ x64 runtime. See [Microsoft's instructions](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist) |
| Runtime not ready | Run `Setup.bat` to install the required versions |
| Slight distortion with whispering or certain pitch ranges in a v2 model | Test those vocal conditions in the game. If the distortion is distracting, use a model trained and exported as RVC v1. Renaming a file or changing its version label does not convert v2 to v1 |
| Missing weight or config | Export an inference model from RVC instead of using a training checkpoint |
| Non-f0 or Unsupported | Use a standard RVC v1/v2 model with f0 enabled |
| weights_only error | Re-export a standard inference checkpoint from the original tool; do not bypass safe loading |
| Permission denied | Extract to a writable folder and choose a writable output location |
| Export succeeds but model is not listed in game | This tool does not register models; follow the game's model import procedure |

For support, provide the tool version (`VERSION.txt`), error message and relevant log. Review logs before sharing because they can contain local file paths. You do not need to send the model itself.

## Command line

After setup, run from the converter folder in PowerShell:

```powershell
& '.\.venv\Scripts\python.exe' -I '.\export_rvc.py' 'D:\Models\voice.pth' 'D:\Models\voice.onnx'
```

Add `--overwrite` to replace an existing output. `--voice-root` is an optional legacy developer setting; normal use does not require it.
