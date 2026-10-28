from audit.models import ActionLog


def log_action(actor, action, obj, before=None, after=None):
    """Record an admin action. Call it inside the same transaction as the action itself."""
    return ActionLog.objects.create(
        actor=actor,
        action=action,
        object_type=obj._meta.label_lower,
        object_id=obj.pk,
        before=before,
        after=after,
    )
