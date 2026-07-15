"""Reply (push notification) verification handlers.

Mirrors the PHP SDK ``Handlers/Reply/`` folder. Pick the strategy that
matches the wire format of the incoming Buckaroo push:

* :class:`buckaroo.services.reply.http_post.HttpPost` — form-encoded pushes
  (SHA-1 over ``brq_signature``).
* :class:`buckaroo.services.reply.json_reply.Json` — JSON pushes (HMAC-SHA256
  over the ``Authorization`` header).
"""

from .http_post import HttpPost
from .json_reply import Json

__all__ = ["HttpPost", "Json"]
