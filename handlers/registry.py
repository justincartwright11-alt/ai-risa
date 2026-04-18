from . import event_decomposition_handler, event_batch_intake_handler, fighter_gap_real_grounding_handler

HANDLER_REGISTRY = {
    "event_decomposition": event_decomposition_handler,
    "event_batch_intake": event_batch_intake_handler,
    "fighter_gap_real_grounding": fighter_gap_real_grounding_handler,
}

def get_handler(task_type):
    return HANDLER_REGISTRY.get(task_type)
