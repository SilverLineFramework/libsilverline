"""Profiling mixins for SilverLine Client."""

import json
import uuid


class ProfileMixin:
    """Profiler API mixins."""

    def reset(self, metadata):
        """Reset profiler state."""
        self.publish(
            "{}/proc/profile/control".format(self.realm), json.dumps({
                "object_id": str(uuid.uuid4()),
                "action": "reset",
                "data": metadata}), qos=2)
