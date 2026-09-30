import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FAKE_AWS = '''#!/usr/bin/env python3
import fcntl, json, os, sys, time
from pathlib import Path
name = sys.argv[4].rsplit('/', 1)[-1]
state = Path(os.environ['UPLOAD_TEST_STATE'])
def change(kind):
 with state.open('a+') as f:
  fcntl.flock(f, fcntl.LOCK_EX); f.seek(0)
  d = json.loads(f.read() or '{"active":0,"maxActive":0,"attempts":{},"events":[]}')
  if kind == 'begin':
   d['active'] += 1; d['maxActive'] = max(d['maxActive'], d['active'])
   d['attempts'][name] = d['attempts'].get(name, 0) + 1
  else: d['active'] -= 1
  d['events'].append([kind, name]); d['retryMode'] = os.environ.get('AWS_RETRY_MODE')
  d['maxAttempts'] = os.environ.get('AWS_MAX_ATTEMPTS')
  f.seek(0); f.truncate(); json.dump(d, f); f.flush()
  return d['attempts'][name]
attempt = change('begin'); time.sleep(0.04)
failed = name == 'artifact.zip' and (os.environ.get('UPLOAD_TEST_FAILURE') == 'always' or (os.environ.get('UPLOAD_TEST_FAILURE') == 'once' and attempt == 1))
change('failure' if failed else 'success')
sys.exit(17 if failed else 0)
'''

class UploadExecutionTests(unittest.TestCase):
    def test_nightly_upload_exits_before_reading_manifest_or_calling_aws(self):
        result = subprocess.run(['bash', str(ROOT / 'scripts/upload_in_order.sh'), '/missing'],
            env={**os.environ, 'RELEASE_CHANNEL': 'nightly'}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('GitHub-only', result.stderr)

    def run_upload(self, failure):
        with tempfile.TemporaryDirectory() as folder:
            temp = Path(folder)
            fake = temp / 'aws'
            fake.write_text(FAKE_AWS)
            fake.chmod(0o755)
            manifest = temp / 'uploads.txt'
            manifest.write_text('one file.zip|artifact.zip\nother.zip|other.zip\nartifact.zip|MultiPost-mac-latest.zip\nlatest-mac.yml|latest-mac.yml\n')
            env = {**os.environ, 'PATH': f'{temp}{os.pathsep}{os.environ["PATH"]}',
                   'UPLOAD_TEST_STATE': str(temp / 'state.json'), 'UPLOAD_TEST_FAILURE': failure,
                   'UPLOAD_RETRY_DELAY': '0', 'UPLOAD_CONCURRENCY': '2',
                   'RELEASE_CHANNEL': 'release', 'S3_BUCKET': 'test', 'S3_PATH': 'latest', 'S3_ENDPOINT': 'https://s3.invalid'}
            result = subprocess.run(['bash', str(ROOT / 'scripts/upload_in_order.sh'), str(manifest)],
                                    env=env, capture_output=True, text=True)
            return result, json.loads((temp / 'state.json').read_text())

    def test_transient_failure_retries_before_promoting_manifest(self):
        result, state = self.run_upload('once')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state['attempts']['artifact.zip'], 2)
        self.assertLessEqual(state['maxActive'], 2)
        self.assertEqual(state['retryMode'], 'adaptive')
        self.assertEqual(state['maxAttempts'], '8')
        events = state['events']
        alias = events.index(['begin', 'MultiPost-mac-latest.zip'])
        self.assertLess(events.index(['success', 'artifact.zip']), alias)
        self.assertLess(events.index(['success', 'other.zip']), alias)
        self.assertLess(events.index(['success', 'MultiPost-mac-latest.zip']), events.index(['begin', 'latest-mac.yml']))

    def test_permanent_failure_keeps_alias_and_manifest_unchanged(self):
        result, state = self.run_upload('always')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(state['attempts']['artifact.zip'], 3)
        self.assertNotIn('MultiPost-mac-latest.zip', state['attempts'])
        self.assertNotIn('latest-mac.yml', state['attempts'])

if __name__ == '__main__':
    unittest.main()
