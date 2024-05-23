from requests import Response


class PyODKError(Exception):
    """An error raised by pyodk."""

    def is_central_error(self, code: float | str) -> bool:
        """
        Does the PyODK error represent a Central error with the specified code?

        Per central-backend/lib/util/problem.js.
        """
        if len(self.args) >= 2 and isinstance(self.args[1], Response):
            err_detail = self.args[1].json()
            err_code = str(err_detail.get("code", ""))
            if err_code is not None and err_code == str(code):
                return True
        return False
