from typing import cast

TRANSLATIONS = {
    "us": {
        "arg.not_found": "Argument is required, but not found in POST data.",
        "arg.invalid_value": "Argument of type {}({}) has invalid value.",
        "user.already_exists": "User '@{}' already exists.",
        "user.not_found": "User '@{}' not found.",
        "user.wrong_password": "Wrong password.",
        "user.not_authenticated": "You must be authenticated to access this page.",
        "user.no_permission": "You don't have permissions to access this page.",
        "generic.not_found": "Not found.",
        "role.0": "User",
        "role.1": "Manager",
        "role.2": "Admin",
    },
    "ua": {
        "arg.not_found": "Необхідно вказати аргумент, але його немає в даних POST.",
        "arg.invalid_value": "Аргумент типу {}({}) має недійсне значення.",
        "user.already_exists": "Користувач '@{}' вже існує.",
        "user.not_found": "Користувача '@{}' не знайдено.",
        "user.wrong_password": "Неправильний пароль.",
        "user.not_authenticated": "Вам потрібно автентифікуватися, щоб отримати доступ до цієї сторінки.",
        "user.no_permission": "У вас немає прав доступу до цієї сторінки.",
        "generic.not_found": "Не знайдено.",
        "role.0": "Користувач",
        "role.1": "Керівник",
        "role.2": "Адміністратор",
    },
}


class Lang:
    def __init__(self, lang: str):
        self.table = cast(dict, TRANSLATIONS.get(lang, TRANSLATIONS.get("us")))

    def translate(self, key: str, *args, **kwargs):
        default = TRANSLATIONS["us"].get(key)
        value = self.table.get(key, default)
        if not value:
            return f"<{key}>"
        return value.format(*args, **kwargs)
