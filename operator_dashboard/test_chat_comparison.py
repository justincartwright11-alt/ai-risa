import unittest
from operator_dashboard.chat_actions import parse_chat_command

class TestChatComparisonCommands(unittest.TestCase):
    def test_parse_compare_event(self):
        for msg in [
            "compare event song_vs_figueiredo",
            "show comparison for song_vs_figueiredo",
            "compare status and evidence for song_vs_figueiredo",
            "what is wrong with song_vs_figueiredo"
        ]:
            parsed = parse_chat_command(msg)
            self.assertEqual(parsed['action'], 'show_event_comparison')
            self.assertEqual(parsed['event_id'], 'song_vs_figueiredo')

    def test_parse_evidence_commands(self):
        parsed = parse_chat_command("show evidence for song_vs_figueiredo")
        self.assertEqual(parsed['action'], 'show_event_evidence')
        self.assertEqual(parsed['event_id'], 'song_vs_figueiredo')

if __name__ == '__main__':
    unittest.main()
