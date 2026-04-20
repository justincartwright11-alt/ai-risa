"""
Chat contract tests for escalation commands (Build 14).
"""
import unittest
import operator_dashboard.app as app

ESCALATION_COMMANDS = [
    "show escalations",
    "escalation view",
    "show top escalations",
    "what needs review now",
    "show escalation for TEST_EVENT",
    "why is TEST_EVENT escalated"
]

class TestChatEscalation(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()

    def test_escalation_chat_commands(self):
        # Use a real event id if available
        esc = self.client.get('/api/escalations').get_json()
        event_id = None
        if esc['escalations']:
            event_id = esc['escalations'][0]['event_id']
        for cmd in ESCALATION_COMMANDS:
            msg = cmd.replace('TEST_EVENT', event_id or 'NO_SUCH_EVENT')
            resp = self.client.post('/chat/send', json={'message': msg})
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertIn('ok', data)
            self.assertIn('action', data)
            self.assertIn('response', data)
            # Should not mutate or error fatally
            self.assertNotIn('error', data.get('response','').lower())

if __name__ == '__main__':
    unittest.main()
