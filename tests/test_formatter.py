from services.formatter import format_message


def test_format_message_no_wrappers():
    result = format_message("Hello world")
    assert "Hello world" in result
    assert "⏰" in result  # timestamp


def test_format_message_with_prefix():
    result = format_message("Hello world", prefix="[NOTICE]")
    assert result.startswith("[NOTICE]")
    assert "Hello world" in result


def test_format_message_with_suffix():
    result = format_message("Hello world", suffix="— Admin")
    assert "— Admin" in result
    assert "Hello world" in result


def test_format_message_full():
    result = format_message(
        "Hello world",
        prefix="[NOTICE]",
        suffix="— Admin",
        include_timestamp=True,
    )
    assert result.startswith("[NOTICE]")
    assert "Hello world" in result
    assert "— Admin" in result
    assert "⏰" in result


def test_format_message_no_timestamp():
    result = format_message("Hello world", include_timestamp=False)
    assert "⏰" not in result
    assert result.strip() == "Hello world"
