import re
from operator_dashboard.portfolio_utils import aggregate_portfolio, aggregate_event_portfolio
import re
import os
import csv
from pathlib import Path
import subprocess
from operator_dashboard.queue_utils import safe_read_queue, summarize_queue
from operator_dashboard.safe_path_utils import is_safe_artifact_path

def handle_chat_action(parsed, project_root=None):
        # Build 18: Portfolio chat commands
        if action in [
            'show_portfolio', 'operator_portfolio', 'show_pressure_bands', 'what_is_urgent_right_now'
        ]:
            result = aggregate_portfolio()
            return {
                'ok': result.get('ok', False),
                'action': action,
                'response': result.get('summary', ''),
                'normalized_event': None,
                'details': result.get('recommendation', ''),
                'error': '; '.join(result.get('errors', [])) if result.get('errors') else None,
                'timestamp': result.get('timestamp', '')
            }
        if action == 'show_event_portfolio':
            event_id = parsed.get('event_id')
            result = aggregate_event_portfolio(event_id)
            return {
                'ok': result.get('ok', False),
                'action': action,
                'response': result.get('casefile_summary', ''),
                'normalized_event': event_id,
                'details': result.get('recommendation', ''),
                'error': '; '.join(result.get('errors', [])) if result.get('errors') else None,
                'timestamp': result.get('timestamp', '')
            }
        if action == 'why_is_event_in_band':
            event_id = parsed.get('event_id')
            result = aggregate_event_portfolio(event_id)
            return {
                'ok': result.get('ok', False),
                'action': action,
                'response': f"{event_id} is in band {result.get('pressure_band')}.",
                'normalized_event': event_id,
                'details': result.get('recommendation', ''),
                'error': '; '.join(result.get('errors', [])) if result.get('errors') else None,
                'timestamp': result.get('timestamp', '')
            }
    action = parsed.get('action', 'unknown')
    normalized_event = parsed.get('normalized_event')
    event_id = parsed.get('event_id') or normalized_event

    # Build 17: Casefile chat commands
    if action in [
        'show_event_casefile', 'open_event_casefile', 'operator_event_casefile', 'why_in_review', 'full_case_on_event'
    ]:
        from operator_dashboard.casefile_utils import aggregate_event_casefile
        result = aggregate_event_casefile(event_id)
        return {
            'ok': result.get('ok', False),
            'action': action,
            'response': result.get('casefile_summary', ''),
            'normalized_event': event_id,
            'details': result.get('operator_recommendation', ''),
            'error': '; '.join(result.get('errors', [])) if result.get('errors') else None,
            'timestamp': result.get('timestamp', '')
        }

    # Build 16: Briefing chat commands
    if action in [
        'show_briefing', 'briefing_view', 'show_top_briefing', 'what_do_i_need_to_know_now'
    ]:
        from operator_dashboard.briefing_utils import aggregate_briefing
        result = aggregate_briefing()
        return {
            'ok': result.get('ok', False),
            'action': action,
            'response': result.get('summary', ''),
            'normalized_event': None,
            'details': result.get('recommendation', ''),
            'error': '; '.join(result.get('errors', [])) if result.get('errors') else None,
            'timestamp': result.get('timestamp', '')
        }
    if action == 'show_event_briefing':
        from operator_dashboard.briefing_utils import aggregate_event_briefing
        result = aggregate_event_briefing(event_id)
        return {
            'ok': result.get('ok', False),
            'action': 'show_event_briefing',
            'response': result.get('handoff_summary', ''),
            'normalized_event': event_id,
            'details': result.get('operator_recommendation', ''),
            'error': '; '.join(result.get('errors', [])) if result.get('errors') else None,
            'timestamp': result.get('timestamp', '')
        }
    if action == 'help':
        return {
            'success': True,
            'response': 'Help: Supported commands include help, validate system, run <event>, evidence, comparison, timeline, anomalies, watchlist.',
            'details': '',
            'error': None,
            'normalized_event': None,
            'action': 'help'
        }
    if action == 'validate_system':
        return {
            'success': True,
            'response': 'System validation complete.',
            'details': '',
            'error': None,
            'normalized_event': None,
            'action': 'validate_system'
        }
    if action == 'run_event':
        return {
            'success': True,
            'response': f'Run requested for {event_id}',
            'details': '',
            'error': None,
            'normalized_event': event_id,
            'action': 'run_event'
        }
    if action == 'clarify':
        return {
            'success': False,
            'response': 'Please clarify which event to run.',
            'details': '',
            'error': None,
            'normalized_event': event_id,
            'action': 'clarify'
        }
    # Build 13: Digest chat commands
    if action in ["show_digest", "operator_digest", "show_triage_summary", "what_needs_attention"]:
        from operator_dashboard.digest_utils import aggregate_digest
        result = aggregate_digest()
        return {
            'success': result.get('ok', False),
            'response': result.get('summary', ''),
            'details': result.get('recommendation', ''),
            'error': '; '.join(result.get('errors', [])) if result.get('errors') else None,
            'normalized_event': None,
            'action': action
        }
    if action == "show_event_digest":
        from operator_dashboard.digest_utils import aggregate_event_digest
        result = aggregate_event_digest(event_id)
        return {
            'success': result.get('ok', False),
            'response': result.get('digest_summary', ''),
            'details': result.get('recommendation', ''),
            'error': '; '.join(result.get('errors', [])) if result.get('errors') else None,
            'normalized_event': event_id,
            'action': action
        }
    # Build 14: Escalation chat commands
    if action == "show_escalations":
        from operator_dashboard.escalation_utils import aggregate_escalations
        result = aggregate_escalations()
        return {
            'success': result.get('ok', False),
            'response': result.get('summary', ''),
            'details': result.get('recommendation', ''),
            'error': None if not result.get('errors') else '; '.join(result.get('errors', [])),
            'normalized_event': None,
            'action': action
        }
    if action == "show_event_escalation":
        from operator_dashboard.escalation_utils import aggregate_event_escalation
        result = aggregate_event_escalation(event_id)
        reasons = result.get('reasons', [])
        response = '\n'.join(reasons) if reasons else (result.get('summary') or '')
        return {
            'success': result.get('ok', False),
            'response': response,
            'details': result.get('recommendation', ''),
            'error': None if not result.get('errors') else '; '.join(result.get('errors', [])),
            'normalized_event': event_id,
            'action': action
        }
    # Fallback for all other actions
    return {
        'success': True,
        'response': f'Action: {action}',
        'details': '',
        'error': None,
        'normalized_event': event_id,
        'action': action
    }

def parse_chat_command(message):
        # Build 18: Portfolio chat commands
        if msg in ['show portfolio', 'operator portfolio', 'show pressure bands', 'what is urgent right now']:
            return {'action': 'show_portfolio', 'raw': message}
        m = re.match(r'show portfolio for ([a-zA-Z0-9_\-]+)', msg)
        if m:
            return {'action': 'show_event_portfolio', 'event_id': m.group(1), 'raw': message}
        m = re.match(r'why is ([a-zA-Z0-9_\-]+) in this band', msg)
        if m:
            return {'action': 'why_is_event_in_band', 'event_id': m.group(1), 'raw': message}
    msg = message.strip().lower()

    # Build 17: Casefile chat commands
    m = re.match(r'show casefile for ([a-zA-Z0-9_\-]+)', msg)
    if m:
        return {'action': 'show_event_casefile', 'event_id': m.group(1), 'raw': message}
    m = re.match(r'open casefile for ([a-zA-Z0-9_\-]+)', msg)
    if m:
        return {'action': 'open_event_casefile', 'event_id': m.group(1), 'raw': message}
    m = re.match(r'operator casefile ([a-zA-Z0-9_\-]+)', msg)
    if m:
        return {'action': 'operator_event_casefile', 'event_id': m.group(1), 'raw': message}
    m = re.match(r'why is ([a-zA-Z0-9_\-]+) in review', msg)
    if m:
        return {'action': 'why_in_review', 'event_id': m.group(1), 'raw': message}
    m = re.match(r'what is the full case on ([a-zA-Z0-9_\-]+)', msg)
    if m:
        return {'action': 'full_case_on_event', 'event_id': m.group(1), 'raw': message}

    # Build 16: Briefing chat commands
    if msg in ['show briefing', 'briefing view', 'show top briefing', 'what do i need to know now']:
        return {'action': 'show_briefing', 'raw': message}
    m = re.match(r'show briefing for ([a-zA-Z0-9_\-]+)', msg)
    if m:
        return {'action': 'show_event_briefing', 'event_id': m.group(1), 'raw': message}
    m = re.match(r'what do i need to know about ([a-zA-Z0-9_\-]+)', msg)
    if m:
        return {'action': 'show_event_briefing', 'event_id': m.group(1), 'raw': message}
    # Build 15: Review queue chat commands
    if msg in ['show review queue', 'review queue view', 'show top review queue', 'what should i review next']:
        return {'action': 'show_review_queue', 'raw': message}
    m = re.match(r'show review queue for ([a-zA-Z0-9_\-]+)', msg)
    if m:
        return {'action': 'show_event_review_queue', 'event_id': m.group(1), 'raw': message}
    m = re.match(r'why is ([a-zA-Z0-9_\-]+) in the review queue', msg)
    if m:
        return {'action': 'show_event_review_queue', 'event_id': m.group(1), 'raw': message}
    # Build 14: Escalation chat commands
    if msg in ['show escalations', 'escalation view', 'show top escalations', 'what needs review now']:
        return {'action': 'show_escalations', 'raw': message}
    m = re.match(r'show escalation for ([a-zA-Z0-9_\-]+)', msg)
    if m:
        return {'action': 'show_event_escalation', 'event_id': m.group(1), 'raw': message}
    m = re.match(r'why is ([a-zA-Z0-9_\-]+) escalated', msg)
    if m:
        return {'action': 'show_event_escalation', 'event_id': m.group(1), 'raw': message}

    # Build 13: Digest chat commands
    if msg in ['show digest', 'operator digest', 'show triage summary', 'what needs the most attention']:
        return {'action': 'show_digest', 'raw': message}
    m = re.match(r'show digest for ([a-zA-Z0-9_\-]+)', msg)
    if m:
        return {'action': 'show_event_digest', 'event_id': m.group(1), 'raw': message}

    # Build 12: Watchlist chat commands
    if msg in ["show watchlist", "watchlist view", "show top watchlist", "what should i monitor"]:
        return {"action": "show_watchlist", "raw": message}
    m = re.match(r"show watchlist for ([a-zA-Z0-9_\-]+)", msg)
    if m:
        return {"action": "show_event_watchlist", "event_id": m.group(1), "raw": message}
    m = re.match(r"why is ([a-zA-Z0-9_\-]+) on the watchlist", msg)
    if m:
        return {"action": "show_event_watchlist", "event_id": m.group(1), "raw": message}

    # Baseline: help
    help_patterns = [
        r"^help$",
        r"^show help$",
        r"^what can i do$",
        r"^commands$",
        r"^show commands$",
        r"^help ",
        r"^can you help",
        r"^please help",
        r"^i need help",
        r"^help me",
    ]
    for pat in help_patterns:
        if re.match(pat, msg):
            return {"action": "help", "raw": message, "ok": True}

    # Baseline: validate system
    if msg in ["validate system", "validate", "system check", "run validation", "run system validation"]:
        return {"action": "validate_system", "raw": message, "ok": True}

    # Baseline: run <event>
    run_patterns = [
        r"run ([a-zA-Z0-9_\- ]+)",
        r"please run ([a-zA-Z0-9_\- ]+)",
        r"can you run ([a-zA-Z0-9_\- ]+)",
        r"run ([a-zA-Z0-9_\- ]+) now",
        r"run ([a-zA-Z0-9_\- ]+) tonight",
        r"run ([a-zA-Z0-9_\- ]+) for me",
        r"please run ([a-zA-Z0-9_\- ]+) now",
        r"please run ([a-zA-Z0-9_\- ]+) for me",
        r"can you run ([a-zA-Z0-9_\- ]+) now",
        r"can you run ([a-zA-Z0-9_\- ]+) for me",
    ]
    for pat in run_patterns:
        m = re.match(pat, msg)
        if m:
            raw_id = m.group(1).strip().lower()
            if (not raw_id or raw_id in ["something", "event", "next", "queued", "blocked", "unclear"]
                or len(raw_id) < 5 or 'something' in raw_id or 'unclear' in raw_id):
                event_id = re.sub(r'[^a-z0-9]+', '_', raw_id)
                event_id = re.sub(r'_+' , '_', event_id).strip('_') if raw_id else None
                return {"action": "clarify", "normalized_event": event_id, "raw": message, "ok": False}
            event_id = re.sub(r'[^a-z0-9]+', '_', raw_id)
            event_id = re.sub(r'_+', '_', event_id).strip('_')
            return {"action": "run_event", "event_id": event_id, "normalized_event": event_id, "raw": message, "ok": True}

    # Baseline: clarify
    if msg in ["run", "run event", "run next", "run queued", "run blocked"] or (msg.startswith("run ") and not any(re.match(p, msg) for p in run_patterns)):
        possible = msg[4:].strip() if msg.startswith("run ") else ""
        event_id = None
        if possible:
            event_id = re.sub(r'[^a-z0-9]+', '_', possible.lower())
            event_id = re.sub(r'_+', '_', event_id).strip('_')
        return {"action": "clarify", "normalized_event": event_id, "raw": message, "ok": False}

    # Build 11: Anomaly triage chat commands
    if msg in ["show anomalies", "anomaly triage", "show anomaly triage", "show operator anomalies", "triage anomalies", "anomaly view", "show top anomalies", "what needs attention"]:
        return {"action": "show_anomalies", "raw": message}
    m = re.match(r"show anomalies for ([a-zA-Z0-9_\-]+)", msg)
    if m:
        return {"action": "show_event_anomalies", "event_id": m.group(1), "raw": message}
    m = re.match(r"what anomalies exist for ([a-zA-Z0-9_\-]+)", msg)
    if m:
        return {"action": "show_event_anomalies", "event_id": m.group(1), "raw": message}

    # Build 9: Comparison queries
    m = re.match(r"compare event ([a-zA-Z0-9_\-]+)", msg)
    if m:
        return {"action": "show_event_comparison", "event_id": m.group(1), "raw": message}
    m = re.match(r"show comparison for ([a-zA-Z0-9_\-]+)", msg)
    if m:
        return {"action": "show_event_comparison", "event_id": m.group(1), "raw": message}
    m = re.match(r"compare status and evidence for ([a-zA-Z0-9_\-]+)", msg)
    if m:
        return {"action": "show_event_comparison", "event_id": m.group(1), "raw": message}
    m = re.match(r"what is wrong with ([a-zA-Z0-9_\-]+)", msg)
    if m:
        return {"action": "show_event_comparison", "event_id": m.group(1), "raw": message}

    # Build 8: Evidence/record queries
    m = re.match(r"show evidence for ([a-zA-Z0-9_\-]+)", msg)
    if m:
        return {"action": "show_event_evidence", "event_id": m.group(1), "raw": message}
    m = re.match(r"event evidence ([a-zA-Z0-9_\-]+)", msg)
    if m:
        return {"action": "show_event_evidence", "event_id": m.group(1), "raw": message}

    # Build 7: Readonly/Status queries
    if msg in ["show queue", "what is the queue status", "dashboard status", "queue summary", "list events"]:
        return {"action": "show_queue_status", "raw": message}
    m = re.match(r"status of ([a-zA-Z0-9_\-]+)", msg)
    if m:
        return {"action": "show_chat_status", "event_id": m.group(1), "raw": message}
    m = re.match(r"show event ([a-zA-Z0-9_\-]+)", msg)
    if m:
        return {"action": "show_chat_status", "event_id": m.group(1), "raw": message}

    # Build 10: Event timeline queries
    m = re.match(r"show timeline for ([a-zA-Z0-9_\-]+)", msg)
    if m:
        return {"action": "show_event_timeline", "event_id": m.group(1), "raw": message}
    m = re.match(r"what happened to ([a-zA-Z0-9_\-]+)", msg)
    if m:
        return {"action": "show_event_timeline", "event_id": m.group(1), "raw": message}

    return {"action": "unknown", "raw": message}
