import datetime

from django.test import TestCase

from accounts.tests.helpers import make_admin, make_member
from audit.models import ActionLog
from audit.services import log_action
from common.clock import fixed_now

T0 = datetime.datetime(2026, 7, 10, 18, 0, tzinfo=datetime.timezone.utc)


class LogActionTests(TestCase):
    def test_rnf07_log_action_records_actor_object_values_and_time(self):
        admin = make_admin()
        member = make_member()
        with fixed_now(T0):
            log_action(
                admin,
                "user_updated",
                member,
                before={"card_expiry": datetime.date(2027, 12, 31)},
                after={"card_expiry": datetime.date(2028, 12, 31)},
            )
        log = ActionLog.objects.get()
        self.assertEqual(log.actor, admin)
        self.assertEqual(log.action, "user_updated")
        self.assertEqual((log.object_type, log.object_id), ("accounts.user", member.pk))
        # Dates are stored as ISO text inside the JSON.
        self.assertEqual(log.before, {"card_expiry": "2027-12-31"})
        self.assertEqual(log.after, {"card_expiry": "2028-12-31"})
        self.assertEqual(log.created_at, T0)
