# utils/responsive.py
from __future__ import annotations
from flask import request, render_template

# Klíčová slova pro rychlou UA detekci (bez knihoven, plně server-side)
MOBILE_KEYWORDS: tuple[str, ...] = (
    "mobile", "iphone", "ipad", "android", "opera mini", "mobi", "silk",
    "kindle", "blackberry", "bb10", "windows phone", "phone", "tablet"
)


def wants_mobile() -> bool:
    """
    Rozhodne, zda renderovat mobilní layout.
    1) Volitelný override přes query ?mobile=1/0 (hodí se na testy).
    2) Jinak heuristika nad User-Agent.
    """

    q = request.args.get("mobile")
    if q == "1":
        return True
    if q == "0":
        return False

    ua = (request.user_agent.string or "").lower()

    # iPadOS někdy hlásí desktopový UA ("Macintosh"), ale přesto je to tablet.
    if "macintosh" in ua and "ipad" in ua:
        return True

    return any(k in ua for k in MOBILE_KEYWORDS)

def render_responsive(desktop_template: str, mobile_template: str, **ctx):
    """
    Vybere desktopovou nebo mobilní šablonu dle wants_mobile() a předá kontext.
    """
    if wants_mobile():
        return render_template(mobile_template, **ctx)
    return render_template(desktop_template, **ctx)
