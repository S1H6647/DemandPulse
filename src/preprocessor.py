from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def create_preprocessor(
    numerical_cols,
    categorical_cols,
    binary_cols=None,
    scale_numeric=False,
):
    numerical_steps = [
        ("imputer", SimpleImputer(strategy="constant", fill_value=-1)),
    ]

    if scale_numeric:
        numerical_steps.append(("scaler", StandardScaler()))  # pyright: ignore[reportArgumentType]

    categorical_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="constant", fill_value="None")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        [
            ("numerical", Pipeline(numerical_steps), numerical_cols),
            ("categorical", categorical_pipeline, categorical_cols),
            (
                "binary",
                SimpleImputer(strategy="constant", fill_value=False),
                binary_cols or [],
            ),
        ]
    )
