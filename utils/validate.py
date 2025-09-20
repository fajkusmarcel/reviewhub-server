import re
import unicodedata
from typing import Dict, Tuple, Any

# Jednoduché schéma: klíč -> pravidla
VALIDATION_SCHEMA = {
    "jmeno": {
        "required": True,
        "type": "str",
        # písmena vč. diakritiky + mezera/-,'  (max 64)
        "pattern": r"^[A-Za-zÀ-ž' -]{1,64}$",
        "normalize_spaces": True,
    },
    "prijmeni": {
        "required": True,
        "type": "str",
        "pattern": r"^[A-Za-zÀ-ž' -]{1,64}$",
        "normalize_spaces": True,
    },
    "login": {
        "required": True,
        "type": "str",
        # konzervativní login (3–32), jen ASCII bezpečné znaky
        "pattern": r"^[a-zA-Z0-9._-]{3,32}$",
        "lower": True,  # loginy sjednotíme na lowercase
    },
    "role": {
        "required": True,
        "type": "str",
        "choices": {"admin", "autor"},
    },
    "heslo": {
        "required": True,
        "type": "str",
        # heslo neomezuj regexem na znaky; validuj pravidly níže
        "min_length": 12,
        "max_length": 256,
        "password_policy": True,  # aspoň 3 z 4 tříd znaků
    },
    # pro login form použij jen 'username' a 'password'
    "username": {
        "required": True,
        "type": "str",
        "pattern": r"^[a-zA-Z0-9._-]{3,64}$",
        "lower": True,
    },
    "password": {
        "required": True,
        "type": "str",
        "min_length": 1,  # povolíme prázdné až validátor hesel v DB rozhodne
        "max_length": 256,
    },
}

# Pomocné regexy pro politiku hesla (neaplikujeme na login.password – jen při tvorbě účtu)
_RE_LOWER = re.compile(r"[a-z]")
_RE_UPPER = re.compile(r"[A-Z]")
_RE_DIGIT = re.compile(r"[0-9]")
_RE_SYMBOL = re.compile(r"[^A-Za-z0-9]")

def _normalize(value: Any) -> str:
    if value is None:
        return ""
    # převedeme na text, ořízneme a normalizujeme Unicode (střední Evropa + české znaky)
    s = str(value).strip()
    s = unicodedata.normalize("NFC", s)
    # zamezíme embedded NUL apod.
    s = s.replace("\x00", "")
    return s

def _collapse_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", s)

def _password_policy_ok(pw: str) -> bool:
    classes = sum([
        1 if _RE_LOWER.search(pw) else 0,
        1 if _RE_UPPER.search(pw) else 0,
        1 if _RE_DIGIT.search(pw) else 0,
        1 if _RE_SYMBOL.search(pw) else 0,
    ])
    return classes >= 3

def validate_payload(payload: Dict[str, Any], fields: Tuple[str, ...]) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    payload ... request.form / dict
    fields  ... jaké klíče validovat dle VALIDATION_SCHEMA
    return: (clean, errors)
    """
    clean: Dict[str, str] = {}
    errors: Dict[str, str] = {}

    for f in fields:
        rules = VALIDATION_SCHEMA.get(f, {})
        raw = payload.get(f, None)
        s = _normalize(raw)

        if not s and rules.get("required", False):
            errors[f] = "Povinné pole."
            continue

        if not s:
            clean[f] = s
            continue

        if rules.get("normalize_spaces"):
            s = _collapse_spaces(s)

        if rules.get("lower"):
            s = s.lower()

        # délky
        min_len = rules.get("min_length")
        max_len = rules.get("max_length")
        if min_len is not None and len(s) < min_len:
            errors[f] = f"Minimální délka je {min_len} znaků."
        if max_len is not None and len(s) > max_len:
            errors[f] = f"Maksimální délka je {max_len} znaků."

        # typ = str (zde už máme string), případně by šly čísla
        pat = rules.get("pattern")
        if pat and not re.fullmatch(pat, s):
            errors[f] = "Neplatný formát."

        choices = rules.get("choices")
        if choices and s not in choices:
            errors[f] = "Neplatná hodnota."

        if rules.get("password_policy"):
            # aplikovat jen při zakládání/změně hesla
            if not _password_policy_ok(s):
                errors[f] = "Heslo musí obsahovat min. 3 z 4: malé, velké, číslo, symbol."

        clean[f] = s

    return clean, errors
