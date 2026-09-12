"""Disposable validation model. No password storage or production authentication."""


MAX_ENCODED_PASSWORD_BYTES = 1020

def signin(body):
    for field in ("username", "password"):
        value = body.get(field)
        if not isinstance(value, str) or not 4 <= len(value) <= 255:
            return 400, {field: f"{field} length must be between 4 and 255 characters"}
    return 422, {"message": "Invalid username/password supplied"}


def registration_errors(body):
    password = body.get("password")
    if not isinstance(password, str) or not 8 <= len(password) <= 255:
        return {"password": "Password length must be between 8 and 255 characters"}
    if len(password.encode("utf-8")) > MAX_ENCODED_PASSWORD_BYTES:
        return {"error": f"password cannot be more than {MAX_ENCODED_PASSWORD_BYTES} bytes"}
    username = body.get("username")
    if not isinstance(username, str) or not 4 <= len(username) <= 255:
        return {"username": "Username length must be between 4 and 255 characters"}
    email = body.get("email")
    if not isinstance(email, str) or "@" not in email or email.startswith("@") or email.endswith("@"):
        return {"email": "Use a nonempty email address with a local part and domain"}
    return None
