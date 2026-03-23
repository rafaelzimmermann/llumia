import os
import time
import pytest
from providers import ProviderResult
from providers import jetbrains


def _write_xml(path, used, maximum, expiration=None):
    """Write a minimal AIAssistantQuotaManager2.xml to path."""
    import json, html
    info = {"usedTokens": used, "maximumTokens": maximum}
    if expiration:
        info["expiration"] = expiration
    encoded = html.escape(json.dumps(info), quote=True)
    path.write_text(
        f'<?xml version="1.0"?>'
        f'<application>'
        f'  <component name="AIAssistantQuotaManager2">'
        f'    <option name="quotaInfo" value="{encoded}"/>'
        f'  </component>'
        f'</application>'
    )


def test_jetbrains_has_required_constants():
    assert jetbrains.NAME == "JetBrains AI"
    assert isinstance(jetbrains.SHORT, str) and jetbrains.SHORT


def test_fetch_returns_none_without_xml_file(monkeypatch):
    """fetch() returns None when no IDE config file is found."""
    monkeypatch.setattr(jetbrains, "_find_xml", lambda: None)
    jetbrains._cache["data"] = None
    jetbrains._cache["ts"] = 0
    assert jetbrains.fetch() is None


def test_fetch_returns_none_when_quota_info_element_absent(tmp_path, monkeypatch):
    """XML file exists but has no quotaInfo option → None."""
    xml_file = tmp_path / "AIAssistantQuotaManager2.xml"
    xml_file.write_text(
        '<?xml version="1.0"?>'
        '<application>'
        '  <component name="AIAssistantQuotaManager2">'
        '    <option name="someOtherOption" value="{}"/>'
        '  </component>'
        '</application>'
    )
    monkeypatch.setattr(jetbrains, "_find_xml", lambda: str(xml_file))
    jetbrains._cache["data"] = None
    jetbrains._cache["ts"] = 0
    assert jetbrains.fetch() is None


def test_fetch_reads_quota_from_xml(tmp_path, monkeypatch):
    """used=5000, max=10000 → pct=50."""
    xml_file = tmp_path / "AIAssistantQuotaManager2.xml"
    _write_xml(xml_file, used=5000, maximum=10000)
    monkeypatch.setattr(jetbrains, "_find_xml", lambda: str(xml_file))
    jetbrains._cache["data"] = None
    jetbrains._cache["ts"] = 0
    result = jetbrains.fetch()
    assert result is not None
    assert result.pct == 50
    assert result.name == "JetBrains AI"


def test_fetch_caps_pct_at_100(tmp_path, monkeypatch):
    """used > maximum → pct capped at 100."""
    xml_file = tmp_path / "AIAssistantQuotaManager2.xml"
    _write_xml(xml_file, used=12000, maximum=10000)
    monkeypatch.setattr(jetbrains, "_find_xml", lambda: str(xml_file))
    jetbrains._cache["data"] = None
    jetbrains._cache["ts"] = 0
    result = jetbrains.fetch()
    assert result.pct == 100


def test_fetch_calculates_reset_secs_from_expiration(tmp_path, monkeypatch):
    """Future expiration date → positive reset_secs."""
    xml_file = tmp_path / "AIAssistantQuotaManager2.xml"
    _write_xml(xml_file, used=1000, maximum=10000, expiration="2099-12-31")
    monkeypatch.setattr(jetbrains, "_find_xml", lambda: str(xml_file))
    jetbrains._cache["data"] = None
    jetbrains._cache["ts"] = 0
    result = jetbrains.fetch()
    assert result.reset_secs > 0


def test_fetch_returns_zero_reset_when_expiration_absent(tmp_path, monkeypatch):
    """No expiration field → reset_secs=0."""
    xml_file = tmp_path / "AIAssistantQuotaManager2.xml"
    _write_xml(xml_file, used=3000, maximum=10000)  # no expiration
    monkeypatch.setattr(jetbrains, "_find_xml", lambda: str(xml_file))
    jetbrains._cache["data"] = None
    jetbrains._cache["ts"] = 0
    result = jetbrains.fetch()
    assert result.reset_secs == 0


def test_fetch_picks_newest_ide_by_mtime(tmp_path, monkeypatch):
    """When multiple IDE dirs exist, the one with the newest mtime is used."""
    old_dir = tmp_path / "JetBrains" / "PyCharm2023.1" / "options"
    new_dir = tmp_path / "JetBrains" / "PyCharm2024.1" / "options"
    old_dir.mkdir(parents=True)
    new_dir.mkdir(parents=True)

    old_file = old_dir / "AIAssistantQuotaManager2.xml"
    new_file = new_dir / "AIAssistantQuotaManager2.xml"
    _write_xml(old_file, used=1000, maximum=10000)  # pct=10
    _write_xml(new_file, used=7000, maximum=10000)  # pct=70

    # Make old_file older
    os.utime(old_file, (0, 0))

    # Patch _find_xml to use our tmp paths
    import glob as glob_mod
    pattern = str(tmp_path / "JetBrains" / "*" / "options" / "AIAssistantQuotaManager2.xml")
    monkeypatch.setattr(
        jetbrains, "_find_xml",
        lambda: max(glob_mod.glob(pattern), key=os.path.getmtime)
    )

    jetbrains._cache["data"] = None
    jetbrains._cache["ts"] = 0
    result = jetbrains.fetch()
    assert result.pct == 70  # picked newest (PyCharm2024.1)


def test_fetch_returns_provider_result_type():
    jetbrains._cache["data"] = ProviderResult(name="JetBrains AI", pct=55, reset_secs=0)
    jetbrains._cache["ts"] = 9_999_999_999
    result = jetbrains.fetch()
    assert isinstance(result, ProviderResult)


def test_fetch_cache_ttl_respected():
    sentinel = ProviderResult(name="JetBrains AI", pct=20, reset_secs=0)
    jetbrains._cache["data"] = sentinel
    jetbrains._cache["ts"] = 9_999_999_999
    ts_before = jetbrains._cache["ts"]
    result = jetbrains.fetch()
    assert result is sentinel
    assert jetbrains._cache["ts"] == ts_before
