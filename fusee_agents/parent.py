"""Accord d'un parent : un code secret choisi par le parent (Patron a moins de 18 ans).

Les agents ne peuvent pas savoir qui écrit dans le groupe : un message « je suis Muriel, j'accepte » peut venir de
n'importe qui. Le parent choisit donc un code que lui seul connaît. Avec ce code, il accepte les demandes qui ont
besoin d'un parent et il peut écrire à l'équipe en son nom (badge 👪). Le code n'est jamais enregistré en clair.
"""
import hashlib
import hmac
import re
import secrets
import time
import unicodedata

from . import db

MAX_TRIES = 5            # erreurs autorisées…
LOCK_S = 15 * 60         # …avant un blocage de 15 minutes
_fails: list[float] = []


def clean(pin) -> str:
    """Le code tel qu'il est vraiment : sans espaces ni points ajoutés par le clavier (iPhone), chiffres normaux."""
    return re.sub(r"[\s.\-]", "", unicodedata.normalize("NFKC", str(pin or "")))


def _hash(pin: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", clean(pin).encode(), salt.encode(), 200_000).hex()


def _matches(pin: str) -> bool:
    return hmac.compare_digest(_hash(pin, db.get_setting("parent_salt", "")), db.get_setting("parent_pin_hash", ""))


def appears_in(text: str) -> bool:
    """Le code parent a-t-il été tapé dans un message (groupe, privé) ? Il ne doit jamais y être. Ne compte pas comme
    un essai raté (sert seulement à protéger le code)."""
    if not is_set():
        return False
    tokens = set(re.findall(r"(?<!\d)\d[\d\s.\-]{2,20}\d(?!\d)", unicodedata.normalize("NFKC", text or "")))
    for token in list(tokens)[:12]:  # chaque vérification prend un peu de temps : on se limite
        digits = clean(token)
        if digits.isdigit() and 4 <= len(digits) <= 12 and _matches(digits):
            return True
    return False


def is_set() -> bool:
    return bool(db.get_setting("parent_pin_hash", ""))


def name() -> str:
    return db.get_setting("parent_name", "") or "le parent"


def locked() -> bool:
    now = time.time()
    _fails[:] = [t for t in _fails if now - t < LOCK_S]
    return len(_fails) >= MAX_TRIES


def check(pin: str) -> bool:
    """Le code est-il le bon ? Après 5 erreurs, plus aucun essai pendant 15 minutes."""
    if not is_set() or locked():
        return False
    ok = _matches(pin)
    if not ok:
        _fails.append(time.time())
    return ok


def setup(parent_name: str, pin: str, old_pin: str = "") -> None:
    """Crée le code parent, ou le change (il faut alors l'ancien code)."""
    parent_name = parent_name.strip()[:40]
    pin = clean(pin)
    if not parent_name:
        raise ValueError("Écris le prénom du parent.")
    if not (pin.isdigit() and 4 <= len(pin) <= 12):
        raise ValueError("Le code doit faire de 4 à 12 chiffres.")
    if is_set() and not check(old_pin):
        raise ValueError("Ancien code parent incorrect." + (" Trop d'essais : attends 15 minutes." if locked() else ""))
    salt = secrets.token_hex(16)
    db.set_setting("parent_salt", salt)
    db.set_setting("parent_pin_hash", _hash(pin, salt))
    db.set_setting("parent_name", parent_name)


def sender() -> str:
    """Nom affiché dans le groupe pour un message du parent vérifié par son code."""
    return f"👪 {name()} (parent)"
