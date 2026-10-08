"""Public provenance and non-MP4 frame-count failure boundaries."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from vidrobust.artifacts import source_url
from vidrobust.media import probe, decoded_frame_count


class PublicSourceTests(unittest.TestCase):
    def test_both_providers_preserve_pins_and_reject_ambiguous_urls(self):
        hf = dict(dataset='owner/dataset', revision='a'*40, remote_path='videos/a b.mp4')
        self.assertEqual(source_url(hf), 'https://huggingface.co/datasets/owner/dataset/resolve/'+'a'*40+'/videos/a%20b.mp4')
        public = dict(provider='http', source_url='https://upload.wikimedia.org/example.webm',
                      source_page='https://commons.wikimedia.org/w/index.php?oldid=123', source_revision='123')
        self.assertEqual(source_url(public), public['source_url'])
        for bad in (public | dict(source_revision=''), public | dict(source_page='http://example.org'),
                    public | dict(source_url='https://user:secret@example.org/a.webm'),
                    public | dict(provider='unknown'), hf | dict(revision='main'), hf | dict(remote_path='../escape')):
            with self.assertRaises(ValueError):
                source_url(bad)

    def test_webm_estimate_is_accepted_only_when_an_independent_decode_agrees(self):
        import cv2
        import numpy as np
        def capture():
            cap = unittest.mock.Mock()
            cap.isOpened.return_value=True
            cap.get.side_effect=lambda k: {cv2.CAP_PROP_FRAME_WIDTH: 640, cv2.CAP_PROP_FRAME_HEIGHT: 512,
                cv2.CAP_PROP_FRAME_COUNT: 17, cv2.CAP_PROP_FPS: 24}[k]
            cap.read.side_effect=[(True, np.zeros((1, 1, 3), dtype=np.uint8))]*16+[(False, None)]
            return cap
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'source.mp4'  # container magic, not filename extension
            path.write_bytes(b'\x1a\x45\xdf\xa3fixture')
            with patch('cv2.VideoCapture', return_value=capture()), patch('vidrobust.media.decoded_frame_count', return_value=16):
                self.assertEqual(probe(path, full_decode=True)['frames'], 16)
            with patch('cv2.VideoCapture', return_value=capture()), patch('vidrobust.media.decoded_frame_count', return_value=17):
                with self.assertRaises(ValueError):
                    probe(path, full_decode=True)
            path.write_bytes(b'not-a-webm')
            with patch('cv2.VideoCapture', return_value=capture()), patch('vidrobust.media.decoded_frame_count') as check:
                with self.assertRaises(ValueError):
                    probe(path, full_decode=True)
                check.assert_not_called()

    def test_real_small_webm_decodes_without_adding_frames(self):
        import imageio_ffmpeg
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'source.webm'
            subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-v', 'error', '-f', 'lavfi', '-i',
                'testsrc2=size=64x64:rate=24', '-frames:v', '17', '-c:v', 'libvpx-vp9', str(path)], check=True)
            self.assertEqual(decoded_frame_count(path), 17)
            self.assertEqual(probe(path, full_decode=True)['frames'], 17)
