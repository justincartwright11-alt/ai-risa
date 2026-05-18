import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(r'C:\ai_risa_data')
import operator_dashboard.chat_actions as chat_actions

test_cases = [
    "run Song vs Figueiredo tonight",
    "please run Prochazka vs Ulberg now",
    "can you run Nikita Tszyu vs Oscar Diaz for me",
    "would you run Song vs Figueiredo",
    "just run Prochazka vs Ulberg quickly",
    "validate system",
    "help",
    "run Something Unclear"
]

for msg in test_cases:
    parsed = chat_actions.parse_chat_command(msg)
    print(f"Input: {msg}")
    print(f"Action: {parsed.get('action')}")
    if 'event_name' in parsed:
        print(f"Event: {parsed.get('event_name')}")
    print("-" * 20)
