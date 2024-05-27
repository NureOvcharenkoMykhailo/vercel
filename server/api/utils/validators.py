import datetime
import math
from typing import Callable, cast

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http.response import json

VITAMINS = [
    "vitamin_a",
    "vitamin_b6",
    "vitamin_b12",
    "vitamin_c",
    "vitamin_d",
    "vitamin_e",
    "vitamin_k1",
    "betaine",
    "choline",
    "folate",
    "thiamin",
    "riboflavin",
    "pantothenic_acid",
    "niacin",
]

MINERALS = [
    "calcium",
    "copper",
    "fluoride",
    "iron",
    "magnesium",
    "manganese",
    "phosphorus",
    "potassium",
    "selenium",
    "sodium",
    "zinc",
]

AMINO_ACIDS = [
    "alanine",
    "arginine",
    "aspartic_acid",
    "cystine",
    "glutamic_acid",
    "glycine",
    "histidine",
    "isoleucine",
    "leucine",
    "lysine",
    "methionine",
    "phenylalanine",
    "proline",
    "serine",
    "threonine",
    "tyrosine",
    "valine",
]


class ValidValue:
    def __init__(self, is_optional: bool = False):
        self.value = None
        self.is_optional = is_optional

    def __str__(self) -> str:
        return f"<{self.__class__.__name__[5:].lower()}>"

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def variables(self):
        return {
            k: v
            for k, v in self.__dict__.items()
            if k not in ["value", "is_optional", "keys"]
        }

    def validate(self, value: str) -> bool:
        return True

    def get_valid_value(
        self, add_error: Callable, data: dict, name: str, parent: str = ""
    ):
        error_name = ".".join([i for i in [parent, name] if i])
        if data.get(name) is None:
            if not self.is_optional:
                add_error(error_name, "arg.not_found")
            return None
        if not self.validate(data.get(name) or ""):
            add_error(
                error_name,
                "arg.invalid_value",
                self.__class__.__name__[5:],
                "; ".join(
                    [
                        "=".join((key, str(value)))
                        for key, value in self.variables.items()
                    ]
                ),
            )
        return self.value


class ValidId(ValidValue):
    def __init__(self, model, key: str, key_type: type, is_optional: bool = False):
        self.model = model
        self.key = key
        self.key_type = key_type
        super().__init__(is_optional)

    def validate(self, value: str):
        instance = self.model.secure_get(**{self.key: self.key_type(value)})
        if not instance:
            return False
        self.value = instance
        return True


class ValidString(ValidValue):
    def __init__(self, max_length: int = 2147483648, is_optional: bool = False):
        self.max_length = max_length
        super().__init__(is_optional=is_optional)

    def validate(self, value: str) -> bool:
        self.value = value
        return len(value) <= self.max_length


class ValidInteger(ValidValue):
    def validate(self, value: str) -> bool:
        try:
            self.value = int(value or "0")
        except ValueError:
            return False
        return True


class ValidFloat(ValidValue):
    def validate(self, value: str) -> bool:
        try:
            self.value = float(value or "0.0")
        except ValueError:
            return False
        return True


class ValidUrl(ValidValue):
    def validate(self, value: str) -> bool:
        self.value = value
        return value.startswith("https://")


class ValidPassword(ValidValue):
    @staticmethod
    def _get_entropy(password: str):
        return math.log2(len(set(password)) ** len(password))

    def validate(self, value: str) -> bool:
        self.value = value
        return self._get_entropy(value) >= 50


class ValidEmail(ValidValue):
    def validate(self, value: str) -> bool:
        try:
            validate_email(value)
        except ValidationError:
            return False
        else:
            self.value = value
            return True


class ValidPhone(ValidValue):
    def validate(self, value: str) -> bool:
        if not value.startswith("+") and value[1:].isnumeric() and len(value[1:]) < 16:
            return False

        self.value = value
        return True


class ValidTime(ValidValue):
    def validate(self, value: str) -> bool:
        split_values = value.split(":")

        if not len(split_values) == 3:
            if len(split_values) == 2:
                self.value = datetime.time(*[int(i) for i in [*split_values, "00"]])  # type: ignore
                return True
            return False

        if False in [i.isnumeric() for i in split_values]:
            return False

        self.value = datetime.time(*[int(i) for i in split_values])  # type: ignore
        return True


class ValidDate(ValidValue):
    def validate(self, value: str) -> bool:
        parts = value.split("-")
        if len(parts) != 3:
            return False

        self.value = value
        return (
            ValidInteger().validate(parts[0])
            and ValidInteger().validate(parts[1])
            and ValidInteger().validate(parts[2])
        )


class ValidJson(ValidValue):
    def __init__(
        self, schema: dict[str, ValidValue], is_optional=False, arbitrary=False
    ):
        self.schema = schema
        self.keys = list(schema.keys())
        self.arbitrary = arbitrary
        super().__init__(is_optional)

    def validate(self, value: str) -> bool:
        try:
            if type(value) is str:
                self.value = json.loads(value)
            else:
                self.value = value
            if self.arbitrary:
                return True
            for key, value in cast(dict, self.value).items():
                if key not in self.keys:
                    return False
                if not self.schema[key].validate(value):
                    return False
        except Exception as e:
            print(e)
            return False
        return True


class ValidBoolean(ValidValue):
    def validate(self, value: str) -> bool:
        if type(value) is bool:
            self.value = value
            return True
        if value.lower() == "true":
            self.value = True
            return True
        if value.lower() == "false":
            self.value = False
            return True
        return False


class ValidMealTime(ValidValue):
    def validate(self, value: str) -> bool:
        self.value = value or 0
        return self.value in [0, 1, 2, 3]


class ValidList(ValidValue):
    def validate(self, value: str) -> bool:
        try:
            self.value = [int(i) for i in value.split(",") if i]
        except:
            return False
        return True
