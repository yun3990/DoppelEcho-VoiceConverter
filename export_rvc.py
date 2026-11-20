"""Doppel Echo RVC to ONNX exporter using bundled w-okada model definitions."""
import argparse
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import traceback

HERE = Path(__file__).resolve().parent


def checkpoint_info(checkpoint):
    if not isinstance(checkpoint, dict) or 'weight' not in checkpoint or 'config' not in checkpoint:
        raise ValueError('Use an exported RVC voice .pth (weight + config), not a training checkpoint.')
    if checkpoint.get('f0') != 1:
        raise ValueError('This voice server requires a pitch/f0 model. Non-f0 models are not supported.')
    weights = checkpoint['weight']
    config = list(checkpoint['config'])
    if len(config) != 18:
        raise ValueError('Unsupported RVC config length.')
    dim = int(weights['enc_p.emb_phone.weight'].shape[1])
    version = {256: 'v1', 768: 'v2'}.get(dim)
    if version is None or checkpoint.get('version', version) != version:
        raise ValueError('Unsupported or inconsistent RVC version / embedding dimension.')
    config[-3] = int(weights['emb_g.weight'].shape[0])
    sample_rate = config[-1]
    if isinstance(sample_rate, str):
        sample_rate = {'32k': 32000, '40k': 40000, '48k': 48000}.get(sample_rate)
    if sample_rate not in (32000, 40000, 48000):
        raise ValueError('Unsupported sample rate.')
    config[-1] = sample_rate
    if config[-3] < 1 or __import__('math').prod(config[12]) != sample_rate // 100:
        raise ValueError('Invalid speaker count or upsampling configuration.')
    return weights, config, dim, version, sample_rate


def validate(session, dim, sample_rate):
    import numpy as np
    expected = {'feats': ('tensor(float)', 3), 'p_len': ('tensor(int64)', 1),
                'pitch': ('tensor(int64)', 2), 'pitchf': ('tensor(float)', 2),
                'sid': ('tensor(int64)', 1)}
    nodes = session.get_inputs()
    if [n.name for n in nodes] != list(expected):
        raise ValueError('Exported model has incompatible input names/order.')
    for n in nodes:
        if (n.type, len(n.shape)) != expected[n.name]:
            raise ValueError(f'Incompatible input {n.name}: {n.type} {n.shape}')
    if nodes[0].shape[-1] != dim:
        raise ValueError('Embedding dimension was not preserved.')
    if [n.name for n in session.get_outputs()] != ['audio']:
        raise ValueError('Missing audio output.')
    rng = np.random.default_rng(1234)
    for frames in (32, 64, 97):
        output = session.run(['audio'], {
            'feats': rng.normal(0, 0.3, (1, frames, dim)).astype(np.float32),
            'p_len': np.array([frames], dtype=np.int64),
            'pitch': np.full((1, frames), 100, dtype=np.int64),
            'pitchf': np.full((1, frames), 180, dtype=np.float32),
            'sid': np.array([0], dtype=np.int64),
        })[0]
        if output.ndim != 1 or output.size != frames * (sample_rate // 100):
            raise ValueError(f'Unexpected audio shape for {frames} frames: {output.shape}')
        if not np.isfinite(output).all() or np.max(np.abs(output)) <= 1e-8:
            raise ValueError('Inference returned non-finite or silent audio.')
        print(f'[CHECK] {frames} frames -> {output.size} finite audio samples', flush=True)


def convert(source, destination, voice_root=HERE, overwrite=False):
    import torch
    import onnx
    import onnxruntime as ort
    source, destination = source.resolve(), destination.resolve()
    if not source.is_file():
        raise FileNotFoundError(f'Input model not found: {source}')
    if source == destination or source.suffix.lower() != '.pth' or destination.suffix.lower() != '.onnx':
        raise ValueError('Select a .pth input and a separate .onnx output.')
    if destination.exists() and not overwrite:
        raise FileExistsError('Output exists. Select another filename or use --overwrite.')
    wokada = voice_root / 'ThirdParty' / 'wokada'
    if not (wokada / 'voice_changer/RVC/onnxExporter').is_dir():
        raise FileNotFoundError(f'w-okada definitions not found: {wokada}')
    sys.path.insert(0, str(wokada))
    torch.set_num_threads(max(1, min(4, os.cpu_count() or 1)))
    print('[1/4] Reading checkpoint (weights_only=True)', flush=True)
    checkpoint = torch.load(str(source), map_location='cpu', weights_only=True)
    weights, config, dim, version, sr = checkpoint_info(checkpoint)
    class_name = f'SynthesizerTrnMs{dim}NSFsid_ONNX'
    module = importlib.import_module('voice_changer.RVC.onnxExporter.' + class_name)
    model = getattr(module, class_name)(*config, is_half=False).float().eval()
    # Released inference checkpoints normally omit the training-only posterior encoder.
    del model.enc_q
    inference_weights = {k: v for k, v in weights.items() if not k.startswith('enc_q.')}
    model.load_state_dict(inference_weights, strict=True)
    print(f'[2/4] Exporting {version}, {dim} features, {sr} Hz, CPU FP32', flush=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Keep existing output untouched unless every validation step succeeds.
    with tempfile.TemporaryDirectory(prefix='.rvc-export-', dir=str(destination.parent)) as temp:
        staged = Path(temp) / 'voice.onnx'
        torch.manual_seed(1234)
        inputs = (torch.randn(1, 64, dim), torch.tensor([64]),
                  torch.full((1, 64), 100, dtype=torch.int64),
                  torch.full((1, 64), 180.0), torch.tensor([0]))
        with torch.no_grad():
            torch.onnx.export(model, inputs, str(staged), opset_version=17, dynamo=False,
                              input_names=['feats', 'p_len', 'pitch', 'pitchf', 'sid'],
                              output_names=['audio'], do_constant_folding=False,
                              dynamic_axes={'feats': {1: 'frames'}, 'pitch': {1: 'frames'},
                                            'pitchf': {1: 'frames'}, 'audio': {0: 'samples'}})
        graph = onnx.load(str(staged))
        metadata = {'application': 'VC_CLIENT', 'version': '2.1',
                    'modelType': 'pyTorchRVC' if version == 'v1' else 'pyTorchRVCv2',
                    'samplingRate': sr, 'f0': True, 'embChannels': dim,
                    'embedder': 'hubert_base', 'embOutputLayer': 9 if dim == 256 else 12,
                    'useFinalProj': dim == 256}
        onnx.helper.set_model_props(graph, {'metadata': json.dumps(metadata), 'embChannels': str(dim)})
        onnx.checker.check_model(graph)
        onnx.save(graph, str(staged))
        print('[3/4] Checking server input contract and dynamic-length inference', flush=True)
        options = ort.SessionOptions()
        options.intra_op_num_threads = 4
        session = ort.InferenceSession(str(staged), sess_options=options, providers=['CPUExecutionProvider'])
        validate(session, dim, sr)
        del session
        if overwrite:
            os.replace(staged, destination)
        else:
            # Windows rename refuses an existing destination, including one created during export.
            os.rename(staged, destination)
    print(f'[4/4] SUCCESS: {destination}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--voice-root', type=Path, default=HERE,
                        help='Optional legacy source root containing ThirdParty/wokada. Defaults to this tool.')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    convert(args.input, args.output, args.voice_root, args.overwrite)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
