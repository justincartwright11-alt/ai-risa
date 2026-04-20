# AI-RISA v40 Endpoint Inventory (Release-Hardening)

| Route | Methods | Handler | Contract Shape | Notes |
|-------|---------|---------|---------------|-------|
| /api/response-matrix | GET | api_response_matrix | {ok, ...matrix fields} | Stable |
| /api/forecast | GET | api_forecast | {ok, ...forecast fields} | Stable |
| /api/drift | GET | api_drift | {ok, ...drift fields} | Stable |
| /api/portfolio | GET | api_portfolio | {ok, ...portfolio fields} | Stable |
| /api/control-summary | GET | api_control_summary | {ok, ...control summary fields} | Stable |
| /api/integrity | GET | api_integrity | {ok, ...integrity fields} | Stable |
| /api/status | GET | api_status | {ok, ...status fields} | Stable |
| /api/watchlist | GET | api_watchlist | {ok, ...watchlist fields} | Stable |
| /api/queue/event/<event_id>/watchlist | GET | api_event_watchlist | {ok, ...event watchlist fields} | Stable |
| /api/queue/event/<event_id>/portfolio | GET | api_event_portfolio | {ok, ...event portfolio fields} | Stable |
| /api/escalations | GET | api_escalations | {ok, ...escalations fields} | Stable |
| /api/queue/event/<event_id>/escalation | GET | api_event_escalation | {ok, ...event escalation fields} | Stable |
| /chat/send | POST | chat_send | {ok, action, response, ...} | Stable |
| /chat/history | GET | chat_history | [chat messages] | Stable |
| / | GET | index | string | Stable |

- All routes attached to single Flask app instance.
- No duplicate or dead routes found.
- All routes return contract-shaped output.
- No mutation/execution endpoints present.
