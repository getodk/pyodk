from unittest import TestCase

from pyodk._utils import validators as v
from pyodk.errors import PyODKError


class TestValidators(TestCase):
    def test_wrap_error__raises_pyodk_error(self):
        """Should raise a PyODK error (from Pydantic) if a validator check fails."""

        def a_func():
            pass

        cases = (
            (v.validate_project_id, False, (None, "a")),
            (v.validate_form_id, False, (None, a_func)),
            (v.validate_table_name, False, (None, a_func)),
            (v.validate_instance_id, False, (None, a_func)),
            (v.validate_entity_list_name, False, (None, a_func)),
            (v.validate_str, True, (None, a_func)),
            (v.validate_bool, True, (None, a_func)),
            (v.validate_int, True, (None, a_func)),
            (v.validate_dict, True, (None, ((("a",),),))),
            (
                v.validate_file_path,
                True,
                (
                    None,
                    "No such file",
                ),
            ),
        )

        for i, (func, has_key, values) in enumerate(cases):
            for j, value in enumerate(values):
                msg = f"Case {i}, Value {j}"
                with self.subTest(msg=msg), self.assertRaises(PyODKError):
                    if has_key:
                        func(value, key=msg)
                    else:
                        func(value)
