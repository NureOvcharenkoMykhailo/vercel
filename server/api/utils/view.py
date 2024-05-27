from typing import Callable

from django.http import HttpResponse

from api.models import User
from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .lang import Lang


def transform_name(name: str):
    if name.startswith("post_"):
        return "POST", name[5:]
    if name.startswith("delete_"):
        return "DELETE", name[7:]
    if name.startswith("get_"):
        return "GET", name[4:]
    return "GET", name


def is_token_valid(token: str):
    return len(token.split(":")) == 2


class GenClass:
    @classmethod
    def _get_locals(cls):
        return {
            k: v
            for k, v in cls.__dict__.items()
            if not k.startswith("__") and k[0].lower() == k[0]
        }.items()


class Args(GenClass):
    def __init__(self, lang: Lang):
        self.is_cancelled = False
        self.error = {}
        self.lang = lang

    def as_dict(self, filters: list[str] = []):
        if not filters:
            filters = []

        return {
            k: v
            for k, v in self.__dict__.items()
            if not k.startswith("__")
            and k not in ["is_cancelled", "error", "lang", *filters]
        }

    def add_error(self, key: str, message: str, *args):
        self.is_cancelled = True
        if "." in key:
            first, second = key.split(".")
            if not self.error.get(first):
                self.error[first] = {}
            self.error[first][second] = self.lang.translate(message, *args)
        else:
            self.error[key] = self.lang.translate(message, *args)

    def validate_all(self, data: dict):
        for name, validator in self.__class__._get_locals():
            if type(validator) is dict:
                updated = {}
                for n, v in validator.items():
                    updated[n] = v.get_valid_value(
                        self.add_error, data.get(name, {}), n, parent=name
                    )
                setattr(self, name, updated)
            else:
                setattr(
                    self, name, validator.get_valid_value(self.add_error, data, name)
                )
        return self


class View(GenClass):
    def __init__(self, name: str, request, lang: str):
        self.name = name
        self.request = request
        self._body = request.data
        self.lang = Lang(lang)

    @classmethod
    def _get_path(cls, fn: Callable, method: str, name: str):
        params = []
        if (
            type(fn).__name__ in ["function"]
            and "query_id" in fn.__annotations__.keys()
        ):
            params.append(f"@<{fn.__annotations__['query_id'].__name__}:query_id>")
        return path(
            "/".join([cls.__name__.lower().replace("view", ""), name, *params]),
            api_view([method])(
                lambda request, lang, *args, **kwargs: cls(
                    name, request, lang
                )._respond(method.lower(), *args, **kwargs)
            ),
            name=name,
        )

    @classmethod
    def get_url_patterns(cls):
        return [
            cls._get_path(fn, *transform_name(name)) for name, fn in cls._get_locals()
        ]

    def _respond(self, method: str, *args, **kwargs):
        fn: Callable = getattr(self, "_".join([method, self.name]))

        # Authenticate
        if fn.__annotations__.get("user"):
            token = self.request.headers.get("Authorization")
            if not token or not is_token_valid(token):
                return Response(
                    {"error": self.lang.translate("user.not_authenticated")},
                    status=401,
                    headers={"Access-Control-Allow-Origin": "*"},
                )
            user_id, password = token.split(":")
            user = User.secure_get(user_id=user_id[1:], password=password)
            if not user:
                return Response(
                    {"error": self.lang.translate("user.not_authenticated")},
                    status=401,
                    headers={"Access-Control-Allow-Origin": "*"},
                )
            args = [user, *args]

        if method == "post":
            view_args: Args = fn.__annotations__["post"](self.lang)
            if view_args.validate_all(self._body).is_cancelled:
                code, response = 400, {"error": view_args.error}
            else:
                code, response = fn(view_args, *args, **kwargs)
        else:
            code, response = fn(*args, **kwargs)
        if code == 201:
            return HttpResponse(response, headers={"Access-Control-Allow-Origin": "*"})  # type: ignore
        return Response(
            response, status=code, headers={"Access-Control-Allow-Origin": "*"}
        )
