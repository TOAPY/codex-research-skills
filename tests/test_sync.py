"""Hermetic tests: tiny skill fixtures only; no scientific experiments or network."""
import argparse
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location('manage', Path(__file__).resolve().parents[1]/'scripts'/'manage.py')
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)

class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.repo, self.dest, self.remote = base/'repo', base/'user'/'.agents'/'skills', base/'remote.git'
        self.repo.mkdir()
        self.run_git(self.repo, 'init', '-b', 'main')
        self.run_git(self.repo, 'config', 'user.name', 'Fixture')
        self.run_git(self.repo, 'config', 'user.email', 'fixture@example.invalid')
        self.skill = self.repo/'.agents'/'skills'/'demo'
        self.skill.mkdir(parents=True)
        (self.skill/'SKILL.md').write_text('---\nname: demo\ndescription: Fixture skill for copy testing\n---\n')
        (self.skill/'data.txt').write_text('one\n')
        self.commit()
        self.run_git(base, 'init', '--bare', str(self.remote))
        self.run_git(self.repo, 'remote', 'add', 'origin', str(self.remote))
        self.run_git(self.repo, 'push', '-u', 'origin', 'main')
        self.args = argparse.Namespace(repo=self.repo, dest=self.dest, offline=False, push=False, remote_url=None)

    def run_git(self, root, *args):
        subprocess.run(['git', '-C', str(root), *args], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    def commit(self):
        self.run_git(self.repo, 'add', '--', '.agents/skills')
        self.run_git(self.repo, 'commit', '-m', 'Fixture change')

    def test_initial_install_and_idempotence(self):
        M.sync(self.args)
        first = M.snapshot(self.dest/'demo')
        M.sync(self.args)
        self.assertEqual(first, M.snapshot(self.dest/'demo'))
        self.assertFalse((self.dest/'demo'/'demo').exists())

    def test_dirty_repository_stops_before_install(self):
        (self.skill/'data.txt').write_text('dirty')
        with self.assertRaisesRegex(RuntimeError, 'uncommitted'):
            M.sync(self.args)
        self.assertFalse(self.dest.exists())

    def test_installed_drift_is_preserved(self):
        M.sync(self.args)
        (self.dest/'demo'/'data.txt').write_text('personal change')
        with self.assertRaisesRegex(RuntimeError, 'changed'):
            M.sync(self.args)
        self.assertEqual('personal change', (self.dest/'demo'/'data.txt').read_text())

    def test_existing_skill_and_unrelated_files_are_preserved(self):
        self.dest.mkdir(parents=True)
        (self.dest/'unrelated.txt').write_text('keep')
        M.copy_skill(self.skill, self.dest/'demo')
        with self.assertRaisesRegex(RuntimeError, 'Unmanaged'):
            M.sync(self.args)
        self.assertEqual('keep', (self.dest/'unrelated.txt').read_text())
        self.assertEqual('one\n', (self.dest/'demo'/'data.txt').read_text())

    def test_capture_customization_then_push(self):
        M.sync(self.args)
        (self.dest/'demo'/'data.txt').write_text('custom')
        M.capture(argparse.Namespace(repo=self.repo, dest=self.dest, skill='demo'))
        self.assertEqual('custom', (self.skill/'data.txt').read_text())
        self.commit()
        self.args.push = True
        M.sync(self.args)
        self.assertEqual('custom', (self.dest/'demo'/'data.txt').read_text())

    def test_fast_forward_downloads_remote_skill_change(self):
        M.sync(self.args)
        peer = self.repo.parent/'peer'
        self.run_git(self.repo.parent, 'clone', '-b', 'main', str(self.remote), str(peer))
        self.run_git(peer, 'config', 'user.name', 'Fixture Peer')
        self.run_git(peer, 'config', 'user.email', 'peer@example.invalid')
        (peer/'.agents'/'skills'/'demo'/'data.txt').write_text('remote update')
        self.run_git(peer, 'add', '--', '.agents/skills')
        self.run_git(peer, 'commit', '-m', 'Peer update')
        self.run_git(peer, 'push', 'origin', 'main')
        M.sync(self.args)
        self.assertEqual('remote update', (self.dest/'demo'/'data.txt').read_text())

    def test_deploy_failure_rolls_back_copies(self):
        M.sync(self.args)
        state = M.read_state(self.dest)
        (self.skill/'data.txt').write_text('new')
        with mock.patch.object(M, 'save_state', side_effect=OSError('fixture failure')):
            with self.assertRaises(OSError):
                M.deploy(self.repo, self.dest, M.skills(self.repo), state)
        self.assertEqual('one\n', (self.dest/'demo'/'data.txt').read_text())

    def test_named_branch_divergence_stops(self):
        M.sync(self.args)
        peer = self.repo.parent/'peer'
        self.run_git(self.repo.parent, 'clone', '-b', 'main', str(self.remote), str(peer))
        self.run_git(peer, 'config', 'user.name', 'Peer')
        self.run_git(peer, 'config', 'user.email', 'peer@example.invalid')
        (peer/'.agents'/'skills'/'demo'/'peer.txt').write_text('peer')
        self.run_git(peer, 'add', '--', '.agents/skills')
        self.run_git(peer, 'commit', '-m', 'Peer update')
        self.run_git(peer, 'push', 'origin', 'main')
        (self.skill/'data.txt').write_text('local commit')
        self.commit()
        with self.assertRaisesRegex(RuntimeError, 'diverged'):
            M.sync(self.args)
        self.assertEqual('one\n', (self.dest/'demo'/'data.txt').read_text())

if __name__ == '__main__':
    unittest.main()
