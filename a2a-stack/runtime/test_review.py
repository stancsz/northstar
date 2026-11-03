import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('review', Path(__file__).with_name('review.py'))
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class CandidateAcceptance(unittest.TestCase):
    def test_rejection_repair_and_stale_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            previous = review.ROOT
            review.ROOT = Path(directory)
            try:
                file = review.ROOT / 'candidate.txt'
                file.write_text('initial')
                first = review.candidate(['candidate.txt'])
                report = {'candidate': first['candidate'], 'author': 'builder',
                          'reviewer': 'independent-qa', 'verdict': 'NOT READY', 'evidence': ['defect']}
                with self.assertRaisesRegex(ValueError, 'Only READY'):
                    review.accept(first, report)
                file.write_text('repair')
                with self.assertRaisesRegex(ValueError, 'STALE'):
                    review.accept(first, {**report, 'verdict': 'READY'})
                second = review.candidate(['candidate.txt'])
                passed = {**report, 'candidate': second['candidate'], 'verdict': 'READY'}
                self.assertTrue(review.accept(second, passed)['accepted'])
                with self.assertRaisesRegex(ValueError, 'Independent'):
                    review.accept(second, {**passed, 'reviewer': 'builder'})
                with self.assertRaisesRegex(ValueError, 'another candidate'):
                    review.accept(second, {**passed, 'candidate': first['candidate']})
                with self.assertRaisesRegex(ValueError, 'project file'):
                    review.candidate(['../outside.txt'])
            finally:
                review.ROOT = previous


if __name__ == '__main__':
    unittest.main()
