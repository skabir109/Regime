from app.services.csrf import (
    extract_origin_from_referer,
    generate_csrf_token,
    validate_csrf_token,
)


def test_generate_and_validate_csrf_token() -> None:
    token = generate_csrf_token()
    assert token
    assert validate_csrf_token(token) is True


def test_rejects_tampered_csrf_token() -> None:
    token = generate_csrf_token()
    tampered = token + "x"
    assert validate_csrf_token(tampered) is False


def test_extract_origin_from_referer() -> None:
    referer = "https://example.com/path?q=1"
    assert extract_origin_from_referer(referer) == "https://example.com"
    assert extract_origin_from_referer("not-a-url") is None
    assert extract_origin_from_referer(None) is None
