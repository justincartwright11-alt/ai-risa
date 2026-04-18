import unittest
from workflows.system_status_pack import system_status_pack

class TestSystemStatusPack(unittest.TestCase):
    def test_all_ready(self):
        result = system_status_pack({
            'event_name': 'event1',
            'remediation_outcome_status': 'ready',
            'completed_remediations': [0, 1],
            'blocked_remediation_outcomes': [],
            'ready_bout_indices': [0, 1],
            'blocked_bout_indices': [],
            'blocker_summary': {},
            'remediation_outcome_summary': {
                'delivery_key': {0: 'dk0', 1: 'dk1'},
                'publication_label': {0: 'A', 1: 'B'},
                'publication_order': {0: 1, 1: 2},
                'final_resolution': {0: 'ok', 1: 'ok'},
                'remediation_snapshot': {0: {'x': 1}, 1: {'x': 2}}
            }
        })
        self.assertEqual(result['system_status'], 'ready')
        self.assertEqual(result['blocked_bout_count'], 0)
        self.assertEqual(result['completed_bout_count'], 2)
        self.assertEqual(len(result['system_status_entries']), 2)
        for entry in result['system_status_entries']:
            self.assertEqual(entry['system_state'], 'ready')
            self.assertEqual(entry['outcome_state'], 'completed')

    def test_partial(self):
        result = system_status_pack({
            'event_name': 'event2',
            'remediation_outcome_status': 'partial',
            'completed_remediations': [0],
            'blocked_remediation_outcomes': [1],
            'ready_bout_indices': [0],
            'blocked_bout_indices': [1],
            'blocker_summary': {'blocker_reason': {1: 'fail'}},
            'remediation_outcome_summary': {
                'delivery_key': {0: 'dk0'},
                'publication_label': {0: 'A'},
                'publication_order': {0: 1},
                'final_resolution': {0: 'ok'},
                'remediation_snapshot': {0: {'x': 1}, 1: {'x': 2}}
            }
        })
        self.assertEqual(result['system_status'], 'partial')
        self.assertEqual(result['blocked_bout_count'], 1)
        self.assertEqual(result['completed_bout_count'], 1)
        self.assertEqual(len(result['system_status_entries']), 2)
        ready_entry = [e for e in result['system_status_entries'] if e['system_state'] == 'ready'][0]
        blocked_entry = [e for e in result['system_status_entries'] if e['system_state'] == 'blocked'][0]
        self.assertEqual(ready_entry['outcome_state'], 'completed')
        self.assertEqual(blocked_entry['blocker_reason'], 'fail')

    def test_all_blocked(self):
        result = system_status_pack({
            'event_name': 'event3',
            'remediation_outcome_status': 'blocked',
            'completed_remediations': [],
            'blocked_remediation_outcomes': [0, 1],
            'ready_bout_indices': [],
            'blocked_bout_indices': [0, 1],
            'blocker_summary': {'blocker_reason': {0: 'fail0', 1: 'fail1'}},
            'remediation_outcome_summary': {
                'remediation_snapshot': {0: {'x': 1}, 1: {'x': 2}}
            }
        })
        self.assertEqual(result['system_status'], 'blocked')
        self.assertEqual(result['blocked_bout_count'], 2)
        self.assertEqual(result['completed_bout_count'], 0)
        self.assertEqual(len(result['system_status_entries']), 2)
        for entry in result['system_status_entries']:
            self.assertEqual(entry['system_state'], 'blocked')
            self.assertIn(entry['blocker_reason'], ['fail0', 'fail1'])

if __name__ == '__main__':
    unittest.main()
