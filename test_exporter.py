"""Contract/error tests; never use or redistribute a real voice model."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_rvc
import numpy as np
import torch


def checkpoint(dim=768, sr=40000):
    config = [1] * 18
    config[12] = [sr // 100]
    config[-1] = sr
    return {'f0': 1, 'version': 'v1' if dim == 256 else 'v2', 'config': config,
            'weight': {'enc_p.emb_phone.weight': torch.zeros(2, dim), 'emb_g.weight': torch.zeros(1, 2)}}


class Node:
    def __init__(self, name, dtype, shape):
        self.name, self.type, self.shape = name, dtype, shape


class Session:
    def __init__(self, mode='ok'):
        self.mode = mode

    def get_inputs(self):
        names = ['feats', 'p_len', 'pitch', 'pitchf', 'sid']
        if self.mode == 'wrong-name':
            names[0] = 'phone'
        return [Node(name, dtype, shape) for name, dtype, shape in zip(names,
            ['tensor(float)', 'tensor(int64)', 'tensor(int64)', 'tensor(float)', 'tensor(int64)'],
            [[1, 'frames', 768], [1], [1, 'frames'], [1, 'frames'], [1]])]

    def get_outputs(self):
        return [Node('audio', 'tensor(float)', ['samples'])]

    def run(self, names, feeds):
        size = feeds['feats'].shape[1] * 400
        if self.mode == 'wrong-length':
            size -= 1
        value = {'silent': 0, 'nan': float('nan')}.get(self.mode, 0.1)
        return [np.full(size, value, dtype=np.float32)]


class ExportTests(unittest.TestCase):
    def test_supported_model_dimensions_and_sample_rates(self):
        for dim in (256, 768):
            for sr in (32000, 40000, 48000):
                with self.subTest(dim=dim, sr=sr):
                    _, config, actual_dim, version, actual_sr = export_rvc.checkpoint_info(checkpoint(dim, sr))
                    self.assertEqual((actual_dim, actual_sr, config[-3]), (dim, sr, 1))

    def test_training_checkpoint_rejected(self):
        with self.assertRaisesRegex(ValueError, 'inference|training'):
            export_rvc.checkpoint_info({'model': {}})

    def test_non_f0_rejected(self):
        sample = checkpoint()
        sample['f0'] = 0
        with self.assertRaisesRegex(ValueError, 'Non-f0'):
            export_rvc.checkpoint_info(sample)

    def test_mismatched_version_rejected(self):
        sample = checkpoint()
        sample['version'] = 'v1'
        with self.assertRaisesRegex(ValueError, 'version'):
            export_rvc.checkpoint_info(sample)

    def test_bad_upsample_rejected(self):
        sample = checkpoint()
        sample['config'][12] = [2]
        with self.assertRaisesRegex(ValueError, 'upsampling'):
            export_rvc.checkpoint_info(sample)

    def test_valid_runtime_contract(self):
        export_rvc.validate(Session(), 768, 40000)

    def test_invalid_runtime_contracts(self):
        for mode in ('wrong-name', 'wrong-length', 'silent', 'nan'):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                export_rvc.validate(Session(mode), 768, 40000)

    def test_failed_export_preserves_source_and_existing_output(self):
        with tempfile.TemporaryDirectory() as temp:
            source, output = Path(temp) / 'invalid.pth', Path(temp) / 'existing.onnx'
            torch.save({'weight': {}, 'config': [], 'f0': 0}, source)
            original = source.read_bytes()
            output.write_bytes(b'existing output')
            with self.assertRaises(ValueError):
                export_rvc.convert(source, output, overwrite=True)
            self.assertEqual(output.read_bytes(), b'existing output')
            self.assertEqual(source.read_bytes(), original)

    def test_no_overwrite_without_explicit_flag(self):
        with tempfile.TemporaryDirectory() as temp:
            source, output = Path(temp) / 'voice.pth', Path(temp) / 'voice.onnx'
            source.write_bytes(b'not even read')
            output.write_bytes(b'original')
            with self.assertRaises(FileExistsError):
                export_rvc.convert(source, output)
            self.assertEqual(output.read_bytes(), b'original')


if __name__ == '__main__':
    unittest.main(verbosity=2)
