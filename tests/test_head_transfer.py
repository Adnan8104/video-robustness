import unittest

from scripts.check_head_transfer import check_cohort


class TransferCohortTests(unittest.TestCase):
    def setUp(self):
        self.samples = [
            dict(label=label, source=source, recording_key=f'{source}{i}',
                 remote_path=f'videos/{directory}/{source}/{source}{i}{suffix}.mp4',
                 sha256=f'{source}-{i}')
            for label, source, directory, suffix in [('real', 'MSVD', 'real', '_10_15'),
                                                      ('ai', 'VEO3', 'fake', '')]
            for i in range(12)
        ]

    def test_different_excerpt_of_prior_camera_recording_is_rejected(self):
        check_cohort(self.samples, [])
        with self.assertRaisesRegex(ValueError, 'reused recording'):
            check_cohort(self.samples, [dict(remote_path='videos/real/MSVD/MSVD0_1_5.mp4')])

    def test_repackaged_source_with_matching_hash_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'reused recording'):
            check_cohort(self.samples, [dict(remote_path='other.mp4', sha256='VEO3-1')])
