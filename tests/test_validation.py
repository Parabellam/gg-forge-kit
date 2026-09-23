from __future__ import annotations

import pytest

from gg_forge_kit.validation import (
    ConfigError, check_keys, choice, discord_id, discord_ids, positive_int, positive_number, string_list,
)


def test_check_keys_suggests_closest():
    with pytest.raises(ConfigError, match="¿Quisiste decir «fundadores»?"):
        check_keys({"fundadore": 1}, {"fundadores"}, "raíz")


def test_check_keys_allows_underscore_comments():
    assert check_keys({"_nota": "x", "a": 1}, {"a"}, "raíz") == {"_nota": "x", "a": 1}


def test_check_keys_requires_object():
    with pytest.raises(ConfigError, match="objeto"):
        check_keys([1], {"a"}, "raíz")


def test_discord_id():
    assert discord_id("123", "x") == 123
    for bad in (0, -1, True, "abc", None, 1.5):
        with pytest.raises(ConfigError, match="rellenar el ID real"):
            discord_id(bad, "x")


def test_discord_ids():
    assert discord_ids(None, "x") == frozenset()
    assert discord_ids([1, "2"], "x") == {1, 2}
    with pytest.raises(ConfigError, match=r"x\[1\]"):
        discord_ids([1, 0], "x")


def test_choice_and_numbers():
    assert choice("a", ("a", "b"), "x") == "a"
    with pytest.raises(ConfigError, match="a, b"):
        choice("c", ("a", "b"), "x")
    assert positive_int(3, "x") == 3
    with pytest.raises(ConfigError):
        positive_int(2.5, "x")
    assert positive_number(3.5, "x") == 3.5
    with pytest.raises(ConfigError):
        positive_number(0, "x")


def test_string_list():
    assert string_list(None, "x") == ()
    assert string_list(["a"], "x") == ("a",)
    with pytest.raises(ConfigError):
        string_list([1], "x")
