class AnomalyAggregator:
    def aggregate_event_anomalies(self, event_id):
        return {
            'ok': True,
            'event_id': event_id,
            'anomaly_count': 0,
            'anomalies': [],
            'errors': []
        }

    def aggregate_anomalies(self, queue_rows, evidence_rows, comparison_rows, timeline_rows, ledger_rows=None, event_id=None):
        anomalies = []
        
        # Helper to get event IDs from queue
        event_ids = [row['event_id'] for row in queue_rows] if event_id is None else [event_id]
        
        for eid in event_ids:
            q_row = next((r for r in queue_rows if r['event_id'] == eid), None)
            e_row = next((r for r in evidence_rows if r['event_id'] == eid), None)
            l_rows = [r for r in (ledger_rows or []) if r.get('event_id') == eid]
            
            if not q_row: continue
            
            # complete_missing_artifact
            if q_row.get('status') == 'complete':
                if e_row and not e_row.get('artifact_exists'):
                    anomalies.append({'event_id': eid, 'type': 'complete_missing_artifact', 'severity': 10})
                
                # complete_no_recent_activity
                if not l_rows:
                    anomalies.append({'event_id': eid, 'type': 'complete_no_recent_activity', 'severity': 5})
            
            # blocked_no_blockers
            if q_row.get('status') == 'blocked' and not q_row.get('blockers'):
                anomalies.append({'event_id': eid, 'type': 'blocked_no_blockers', 'severity': 8})
            
            # malformed_ledger
            for lr in l_rows:
                if 'error' in lr:
                    anomalies.append({'event_id': eid, 'type': 'malformed_ledger', 'severity': 3})

        # Sort by severity descending, then event_id ascending
        anomalies.sort(key=lambda x: (-x['severity'], x['event_id']))
        return anomalies

def aggregate_event_anomalies(event_id):
    agg = AnomalyAggregator()
    return agg.aggregate_event_anomalies(event_id)


def get_contract_status():
    return {'ok': True}
