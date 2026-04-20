from chat_actions import parse_chat_command

test_cases = [
    'help',
    'validate system',
    'run Song vs Figueiredo tonight',
    'please run Prochazka vs Ulberg now',
    'can you run Nikita Tszyu vs Oscar Diaz for me',
    'I want to run Song vs Figueiredo',
    'can you please run Song vs Figueiredo right now',
    'run something unclear'
]

print(f"{'INPUT':<50} | {'ACTION':<20} | {'NORMALIZED EVENT'}")
print('-' * 90)
for tc in test_cases:
    res = parse_chat_command(tc)
    action = res.get('action', 'unknown')
    event = res.get('normalized_event', 'N/A')
    print(f"{tc:<50} | {action:<20} | {event}")
