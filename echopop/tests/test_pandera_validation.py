import re

import pandas as pd
import pytest
from pandera.errors import SchemaError

from echopop.tests.conftest import assert_dataframe_equal
from echopop.utils.validate_df import BaseDataFrame, IsobathData


@pytest.mark.parametrize(
    "description",
    ["Assess `BaseDataFrame` pandera model structure"],
    ids=["Assess `BaseDataFrame` pandera model structure"],
)
def test_BaseDataFrame_model_structure(description):

    # -------------------------
    # ASSERT: 'Config' attribute
    # ---- Check existence
    assert "Config" in dir(BaseDataFrame)
    # ---- Check that the attribute comprises the correct entries
    assert set(["metadata", "strict"]).issubset(BaseDataFrame.Config.__dict__)
    # ---- Verify that 'metadata' is a dictionary
    assert isinstance(BaseDataFrame.Config.__dict__["metadata"], dict)
    # ---- Verify that 'strict' is set to 'False'
    assert not BaseDataFrame.Config.__dict__["strict"]

    # -------------------------
    # ASSERT: '_DTYPE_TESTS' and '_DTYPE_COERCION' attributes
    # ---- Check existence
    assert set(["_DTYPE_TESTS", "_DTYPE_COERCION"]).issubset(dir(BaseDataFrame))
    # ---- Verify that both attributes are dictionaries
    assert all(
        [
            isinstance(getattr(BaseDataFrame, attr), dict)
            for attr in ["_DTYPE_TESTS", "_DTYPE_COERCION"]
        ]
    )
    # ---- Check that the dictionary keys comprise the 'int', 'float', and 'str' datatypes
    assert all(
        [
            set(getattr(BaseDataFrame, attr)).issubset(set([int, float, str]))
            for attr in ["_DTYPE_TESTS", "_DTYPE_COERCION"]
        ]
    )

    # -------------------------
    # ASSERT: 'BaseDataFrame' methods
    # ---- Check that all necessary methods exist
    assert set(["get_column_types", "judge", "validate_df"]).issubset(dir(BaseDataFrame))


@pytest.mark.parametrize(
    "input, expected, exception",
    [
        (
            pd.DataFrame(dict(latitude=[0.0], longitude=[0.0])),
            pd.DataFrame(dict(latitude=[0.0], longitude=[0.0])),
            None,
        ),
        (
            pd.DataFrame(dict(latitude=[-1.0, 0.0, 1.0], longitude=[-1.0, 0.0, 1.0])),
            pd.DataFrame(dict(latitude=[-1.0, 0.0, 1.0], longitude=[-1.0, 0.0, 1.0])),
            None,
        ),
        (
            pd.DataFrame(dict(latitude=[-1.0, 0.0, 1.0], longitude=[-181.0, 0.0, 1.0])),
            None,
            "greater_than_or_equal_to(-180.0)",
        ),
        (
            pd.DataFrame(dict(latitude=[-1.0, 0.0, 1.0], longitude=[-1.0, 0.0, 181.0])),
            None,
            "less_than_or_equal_to(180.0)",
        ),
        (
            pd.DataFrame(dict(latitude=[-91.0, 0.0, 1.0], longitude=[-1.0, 0.0, 1.0])),
            None,
            "greater_than_or_equal_to(-90.0)",
        ),
        (
            pd.DataFrame(dict(latitude=[-1.0, 0.0, 91.0], longitude=[1.0, 0.0, 1.0])),
            None,
            "less_than_or_equal_to(90.0)",
        ),
        (
            pd.DataFrame(dict(latitude=[-1.0, 0.0, 1.0])),
            None,
            "'.*longitude.*' did not match any columns in the dataframe",
        ),
        (
            pd.DataFrame(dict(longitude=[1.0, 0.0, 1.0])),
            None,
            "'.*latitude.*' did not match any columns in the dataframe",
        ),
        (
            pd.DataFrame(dict()),
            None,
            [
                "'.*longitude.*' did not match any columns in the dataframe",
                "'.*latitude.*' did not match any columns in the dataframe",
            ],
        ),
    ],
    ids=[
        "Simple DataFrame input [single row]",
        "Simple DataFrame input [multiple rows]",
        "Invalid longitude [lower limit]",
        "Invalid longitude [upper limit]",
        "Invalid latitude [lower limit]",
        "Invalid latitude [upper limit]",
        "Missing column [longitude]",
        "Missing column [latitude]",
        "Missing all columns",
    ],
)
def test_IsobathData_model(input, expected, exception):

    if exception:
        if isinstance(exception, list):
            for e in exception:
                with pytest.raises(SchemaError, match=re.escape(e)):
                    assert IsobathData.validate_df(input)
        else:
            with pytest.raises(SchemaError, match=re.escape(exception)):
                assert IsobathData.validate_df(input)
    else:
        # Test creation with various parameters
        result = IsobathData.validate_df(input)
        assert_dataframe_equal(result, input.dtypes, expected)
