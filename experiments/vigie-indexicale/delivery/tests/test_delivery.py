import io
import sys
import unittest
import zipfile
from pathlib import Path
from hashlib import sha256
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from check_delivery import verify_delivery, PUBLIC, GuardFailure, _open_zip

def make_zip(files, compression=zipfile.ZIP_DEFLATED):
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w',compression=compression) as z:
        for name, content in files.items():
            z.writestr(name,content)
    return b.getvalue()

def fixture():
    src={
        'web/src/core.mjs':b'core', 'web/src/anchor.mjs':b'anchor',
        'web/tests/indexical.test.mjs':b'test', 'git_witness/witness/verify.mjs':b'witness',
    }
    public={name: (b'core' if name=='core.mjs' else b'anchor' if name=='anchor-core.mjs' else b'content:'+name.encode()) for name in PUBLIC}
    src.update({'web/public/'+name: value for name, value in public.items()})
    return src,public

def run(src=None,pub=None,expected_source=None,expected_public=None):
    a,b=fixture()
    a=src if src is not None else a
    b=pub if pub is not None else b
    sa,pb=make_zip(a),make_zip(b)
    return verify_delivery(sa,pb,expected_source_sha=expected_source or sha256(sa).hexdigest(),
                           expected_public_sha=expected_public or sha256(pb).hexdigest())

class DeliveryTests(unittest.TestCase):
    def test_valid(self):
        r=run();self.assertTrue(r['ok']);self.assertEqual(r['fileCount'],8)
    def test_not_authenticated(self):
        r=run();self.assertEqual(r['epistemic'],'E0');self.assertEqual(r['authorization'],'NOT_ASSESSED');self.assertEqual(r['authentication'],'NOT_ESTABLISHED')
    def test_deploy_not_assessed(self):
        self.assertEqual(run()['deployState'],'NOT_ASSESSED')
    def test_source_pin_fake(self):
        self.assertEqual(run(expected_source='0'*64)['code'],'SOURCE_EMPREINTE_DIFFERENTE')
    def test_public_pin_fake(self):
        self.assertEqual(run(expected_public='1'*64)['code'],'DEPLOIEMENT_ARCHIVE_EMPREINTE_DIFFERENTE')
    def test_invalid_pin(self):
        self.assertEqual(run(expected_public='ZZ')['code'],'PINS_INVALIDES')
    def test_public_modified_rehashed(self):
        s,p=fixture();p['app.js']=b'modified';self.assertEqual(run(pub=p)['code'],'OCTETS_PUBLIES_NON_LIES_A_SOURCE:app.js')
    def test_source_modified_rehashed(self):
        s,p=fixture();s['web/public/index.html']=b'fake';self.assertEqual(run(src=s)['code'],'OCTETS_PUBLIES_NON_LIES_A_SOURCE:index.html')
    def test_extra_file_private_exposure(self):
        s,p=fixture();p['archives-secret.json']=b'secret';self.assertEqual(run(pub=p)['code'],'PUBLICATION_FICHIERS_MANQUANTS_OU_SUPPLEMENTAIRES')
    def test_missing_file(self):
        s,p=fixture();p.pop('styles.css');self.assertEqual(run(pub=p)['code'],'PUBLICATION_FICHIERS_MANQUANTS_OU_SUPPLEMENTAIRES')
    def test_missing_source_file(self):
        s,p=fixture();s.pop('git_witness/witness/verify.mjs');self.assertEqual(run(src=s)['code'],'ARCHIVE_SOURCE_INCOMPLETE')
    def test_missing_public_source(self):
        s,p=fixture();s.pop('web/public/index.html');self.assertEqual(run(src=s)['code'],'SOURCE_PUBLIQUE_MANQUANTE')
    def test_core_publish_mismatch(self):
        s,p=fixture();s['web/src/core.mjs']=b'other';self.assertEqual(run(src=s)['code'],'MOTEUR_SOURCE_PUBLIE_DIFFERENT')
    def test_anchor_publish_mismatch(self):
        s,p=fixture();s['web/src/anchor.mjs']=b'other';self.assertEqual(run(src=s)['code'],'ANCRAGE_SOURCE_PUBLIE_DIFFERENT')
    def test_relative_parent_refused(self):
        with self.assertRaises(GuardFailure): _open_zip(make_zip({'../escape':b'x'}))
    def test_absolute_refused(self):
        with self.assertRaises(GuardFailure): _open_zip(make_zip({'/absolute':b'x'}))
    def test_backslash_refused(self):
        with self.assertRaises(GuardFailure): _open_zip(make_zip({'a\\b':b'x'}))
    def test_duplicate_refused(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore');z.writestr('a',b'x');z.writestr('a',b'x')
        with self.assertRaises(GuardFailure): _open_zip(b.getvalue())
    def test_nonzip_refused(self):
        self.assertEqual(verify_delivery(b'not zip',b'not zip',expected_source_sha=sha256(b'not zip').hexdigest(),expected_public_sha=sha256(b'not zip').hexdigest())['code'],'ZIP_INVALIDE')
    def test_missing_raw_bytes(self):
        self.assertEqual(verify_delivery('notbytes',b'',expected_source_sha='0'*64,expected_public_sha='0'*64)['code'],'ARCHIVES_ILLISIBLES')

if __name__=='__main__':unittest.main()
