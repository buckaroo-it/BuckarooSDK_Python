from typing import List

import src.handlers.logging.observer_interface as observer_interface


class ErrorReporter(observer_interface.ObserverInterface):
    def __init__(self) -> None:
        self._reportables: List[str] = ["error", "critical", "emergency"]

    # Method was created in PHP SDK but did not have any functionality, it should probably send a message to a slack channel or email?
    # @TODO
    def update(self, method: str, message: str, context: List[dict] = []) -> None:
        if method in self._reportables:
            print(
                f"Firing off message: {message} for method: {method} to mail/report server/slack"
            )
