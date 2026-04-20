# AI-RISA v40 Chat Command Inventory (Release-Hardening)

| Command / Alias | Action | Handler | Notes |
|-----------------|--------|---------|-------|
| show response matrix | show_response_matrix | handle_chat_action | Stable |
| operator playbook | operator_playbook | handle_chat_action | Stable |
| what should i inspect | what_should_i_inspect | handle_chat_action | Stable |
| where do i look first | where_do_i_look_first | handle_chat_action | Stable |
| what is the best inspection path | best_inspection_path | handle_chat_action | Stable |
| what should i check next | what_should_i_check_next | handle_chat_action | Stable |
| show forecast | show_forecast | handle_chat_action | Stable |
| operator forecast | operator_forecast | handle_chat_action | Stable |
| show early warning | show_early_warning | handle_chat_action | Stable |
| what is likely next | what_is_likely_next | handle_chat_action | Stable |
| what should i watch next | what_should_i_watch_next | handle_chat_action | Stable |
| what could go wrong soon | what_could_go_wrong_soon | handle_chat_action | Stable |
| show drift | show_drift | handle_chat_action | Stable |
| operator drift | operator_drift | handle_chat_action | Stable |
| what changed | what_changed | handle_chat_action | Stable |
| what moved | what_moved | handle_chat_action | Stable |
| what changed since last state | what_changed_since_last_state | handle_chat_action | Stable |
| do i need to react | do_i_need_to_react | handle_chat_action | Stable |
| show portfolio | show_portfolio | handle_chat_action | Stable |
| operator portfolio | show_portfolio | handle_chat_action | Stable |
| show pressure bands | show_portfolio | handle_chat_action | Stable |
| what is urgent right now | show_portfolio | handle_chat_action | Stable |
| show control summary | show_control_summary | handle_chat_action | Stable |
| operator summary | show_control_summary | handle_chat_action | Stable |
| show command summary | show_control_summary | handle_chat_action | Stable |
| what is the system picture now | show_control_summary | handle_chat_action | Stable |
| what changed recently | show_control_summary | handle_chat_action | Stable |
| what should i look at first | show_control_summary | handle_chat_action | Stable |
| show integrity | show_integrity | handle_chat_action | Stable |
| operator integrity | operator_integrity | handle_chat_action | Stable |
| show readiness | show_readiness | handle_chat_action | Stable |
| is dashboard healthy | is_dashboard_healthy | handle_chat_action | Stable |
| what is broken | what_is_broken | handle_chat_action | Stable |
| what is unsafe right now | what_is_unsafe_right_now | handle_chat_action | Stable |
| show briefing | show_briefing | handle_chat_action | Stable |
| briefing view | show_briefing | handle_chat_action | Stable |
| show top briefing | show_briefing | handle_chat_action | Stable |
| what do i need to know now | show_briefing | handle_chat_action | Stable |
| help | help | handle_chat_action | Stable |
| validate system | validate_system | handle_chat_action | Stable |
| validate | validate_system | handle_chat_action | Stable |
| system check | validate_system | handle_chat_action | Stable |
| run validation | validate_system | handle_chat_action | Stable |
| run system validation | validate_system | handle_chat_action | Stable |
| run <event> | run_event | handle_chat_action | Stable |
| clarify | clarify | handle_chat_action | Stable |

- All aliases map to unique actions; no shadowing or stale commands found.
- All handlers return standard contract envelope.
- No mutation/execution commands present.
