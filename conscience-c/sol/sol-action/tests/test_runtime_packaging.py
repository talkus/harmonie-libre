"""Regression: Python execution files, CDN files and platform config have different scopes."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

APP = Path(__file__).resolve().parents[1] / 'app'
sys.path.insert(0, str(APP))
import bridge_runtime
spec = importlib.util.spec_from_file_location('packaging_mcp', APP / 'api/mcp.py')
mcp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcp)


class RuntimePackagingTests(unittest.TestCase):
    def test_real_python_files_pass_with_cdn_excluded_and_config_transformed(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = Path(temp) / 'bundle'
            shutil.copytree(APP, bundle, ignore=shutil.ignore_patterns('public','__pycache__'))
            (bundle/'vercel.json').write_text('{"platform_normalized":true}')
            release = bridge_runtime.load_release(bundle)
            self.assertEqual(set(release['files']), {'api/job.py','api/mcp.py','bridge_runtime.py'})
            self.assertTrue(mcp.release_manifest(bundle)['available'])
            (bundle/'api/job.py').write_text((bundle/'api/job.py').read_text()+'\n')
            with self.assertRaises(bridge_runtime.ReleaseCheckError):
                bridge_runtime.load_release(bundle)
            with self.assertRaises(ValueError):
                mcp.release_manifest(bundle)

    def test_failure_diagnostics_read_only_fixed_public_source_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'private-secret.txt').write_text('SYNTHETIC_SECRET_NOT_PUBLIC')
            observed = mcp.bundle_diagnostics(root)
            self.assertEqual(set(observed), {'release-source.json','build-info.json','api/job.py','api/mcp.py','bridge_runtime.py','vercel.json'})
            self.assertTrue(all(v == {'readable': False} for v in observed.values()))
            self.assertNotIn('SYNTHETIC_SECRET_NOT_PUBLIC',json.dumps(observed))


if __name__ == '__main__':
    unittest.main()
