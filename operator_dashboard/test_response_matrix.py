import unittest
from operator_dashboard.response_matrix_utils import get_operator_response_matrix

class TestResponseMatrix(unittest.TestCase):
    def test_contract_shape(self):
        matrix = get_operator_response_matrix()
        required_fields = [
            'ok', 'timestamp', 'matrix_status', 'top_issue', 'why_it_matters',
            'recommended_paths', 'stabilizing_signals', 'worsening_signals',
            'first_surface', 'second_surface', 'third_surface', 'summary',
            'recommendation', 'errors'
        ]
        for field in required_fields:
            self.assertIn(field, matrix)

    def test_quiet_state(self):
        matrix = get_operator_response_matrix()
        self.assertEqual(matrix['matrix_status'], 'quiet')
        self.assertEqual(matrix['top_issue'], 'none')
        self.assertIn('All core signals stable', matrix['stabilizing_signals'])
        self.assertEqual(matrix['first_surface'], 'portfolio')
        self.assertEqual(matrix['second_surface'], 'control-summary')
        self.assertEqual(matrix['third_surface'], 'drift')
        self.assertTrue(matrix['ok'])

    def test_deterministic_ordering(self):
        matrix1 = get_operator_response_matrix()
        matrix2 = get_operator_response_matrix()
        self.assertEqual(matrix1['recommended_paths'], matrix2['recommended_paths'])
        self.assertEqual(matrix1['stabilizing_signals'], matrix2['stabilizing_signals'])
        self.assertEqual(matrix1['worsening_signals'], matrix2['worsening_signals'])
        self.assertEqual(matrix1['first_surface'], matrix2['first_surface'])
        self.assertEqual(matrix1['second_surface'], matrix2['second_surface'])
        self.assertEqual(matrix1['third_surface'], matrix2['third_surface'])

if __name__ == "__main__":
    unittest.main()
