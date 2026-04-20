import unittest
import json
from app import app

class ChatContractTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def send(self, msg):
        resp = self.client.post('/chat/send', json={'message': msg})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        # Contract fields
        for field in ['ok', 'action', 'response', 'normalized_event', 'details', 'error', 'timestamp']:
            self.assertIn(field, data)
        return data

    def test_help(self):
        data = self.send('help')
        self.assertEqual(data['action'], 'help')
        self.assertTrue(data['ok'])

    def test_validate(self):
        data = self.send('validate system')
        self.assertEqual(data['action'], 'validate_system')

    def test_run_event(self):
        data = self.send('run Song vs Figueiredo tonight')
        self.assertEqual(data['action'], 'run_event')
        self.assertIn('song_vs_figueiredo', data['normalized_event'])

    def test_polite_run(self):
        data = self.send('please run Prochazka vs Ulberg now')
        self.assertEqual(data['action'], 'run_event')
        self.assertIn('prochazka_vs_ulberg', data['normalized_event'])

    def test_can_you_run(self):
        data = self.send('can you run Nikita Tszyu vs Oscar Diaz for me')
        self.assertEqual(data['action'], 'run_event')
        self.assertIn('nikita_tszyu_vs_oscar_diaz', data['normalized_event'])

    def test_unclear(self):
        data = self.send('run something unclear')
        self.assertEqual(data['action'], 'clarify')
        self.assertFalse(data['ok'])

    def test_history_truncation(self):
        # Send 210 messages, history should cap at 200
        for i in range(210):
            self.send(f'help {i}')
        resp = self.client.get('/chat/history')
        self.assertEqual(resp.status_code, 200)
        history = resp.get_json()
        self.assertLessEqual(len(history), 200)

    def test_malformed_history(self):
        # Overwrite history file with bad data
        with open('operator_dashboard/chat_history.json', 'w', encoding='utf-8') as f:
            f.write('not a json')
        # Should not crash
        resp = self.client.get('/chat/history')
        self.assertEqual(resp.status_code, 200)
        history = resp.get_json()
        self.assertIsInstance(history, list)

if __name__ == '__main__':
    unittest.main()
