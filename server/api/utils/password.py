import bcrypt


class Password:
    @staticmethod
    def encrypt(password: str) -> bytes:
        return bcrypt.hashpw(bytes(password, encoding="utf-8"), bcrypt.gensalt())

    @staticmethod
    def compare(hashed: str, password: str) -> bool:
        return bcrypt.checkpw(
            bytes(password, encoding="utf-8"), bytes(hashed, encoding="utf-8")
        )
