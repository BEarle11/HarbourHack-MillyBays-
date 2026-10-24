class MillyBaysError(Exception):
    """A stage failed. The command-line tool prints this and exits 1."""

    def __init__(self, stage: str, message: str) -> None:
        self.stage = stage
        self.message = message
        super().__init__(f"{stage}: {message}")


class InputError(Exception):
    """The invocation or the image is unusable. The command-line tool exits 2."""
