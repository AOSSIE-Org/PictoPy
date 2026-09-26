import pytest

from app.config.settings import _get_env_bool


class TestGetEnvBool:
    def test_unset_uses_the_default(self, monkeypatch):
        monkeypatch.delenv("PICTOPY_TEST_FLAG", raising=False)
        assert _get_env_bool("PICTOPY_TEST_FLAG", True) is True
        assert _get_env_bool("PICTOPY_TEST_FLAG", False) is False

    @pytest.mark.parametrize("raw", ["1", "true", "TRUE", "yes", "on", " True "])
    def test_truthy_values(self, monkeypatch, raw):
        monkeypatch.setenv("PICTOPY_TEST_FLAG", raw)
        assert _get_env_bool("PICTOPY_TEST_FLAG", False) is True

    @pytest.mark.parametrize("raw", ["0", "false", "FALSE", "no", "off"])
    def test_falsy_values(self, monkeypatch, raw):
        monkeypatch.setenv("PICTOPY_TEST_FLAG", raw)
        assert _get_env_bool("PICTOPY_TEST_FLAG", True) is False

    def test_unrecognised_value_falls_back_to_the_default(self, monkeypatch, caplog):
        """A typo must not silently flip a feature on."""
        monkeypatch.setenv("PICTOPY_TEST_FLAG", "enabled")
        assert _get_env_bool("PICTOPY_TEST_FLAG", False) is False
        assert "Invalid value" in caplog.text
