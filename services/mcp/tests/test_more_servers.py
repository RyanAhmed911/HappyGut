"""The guidelines, evals and journal MCP servers: read-only tools with structured output."""

import json
from pathlib import Path

import anyio
import httpx

from happygut_mcp import evals, guidelines, journal
from mcp import Client

FIXTURES = Path(__file__).parent / "fixtures" / "journal"


def tools_of(server):
    async def go():
        async with Client(server) as client:
            return {t.name: t for t in (await client.list_tools()).tools}
    return anyio.run(go)


def call(server, tool, args=None):
    async def go():
        async with Client(server) as client:
            return await client.call_tool(tool, args or {})
    return anyio.run(go)


def assert_read_only(tools, names):
    assert set(tools) == names
    for t in tools.values():
        assert t.annotations.read_only_hint is True and t.annotations.destructive_hint is False
        assert t.output_schema is not None


# ---------------------------------------------------------------- guidelines

RULES = guidelines.load_rules()
GUIDE = guidelines.build_server(RULES)


def test_guidelines_tools_and_every_approved_card_is_served():
    assert_read_only(tools_of(GUIDE), {"search_rules", "get_rule", "list_sources"})
    assert len(RULES) == 25 and all(r.sources for r in RULES)


def test_search_puts_hard_safety_rules_first_and_filters():
    r = call(GUIDE, "search_rules", {"query": "fibre", "diagnosis": "CD", "phenotype": "stricturing"}).structured_content
    assert r["rules"][0]["hard"] is True and r["rules"][0]["component"] in ("insoluble_fibre", "skins_seeds_nuts")
    uc = call(GUIDE, "search_rules", {"component": "insoluble_fibre", "diagnosis": "UC"}).structured_content["rules"]
    assert all("UC" in x["diagnoses"] for x in uc)
    assert "safe" not in r["note"].replace("'safe'", "")


def test_get_rule_quotes_its_source_exactly_and_unknown_is_an_error():
    rule = call(GUIDE, "get_rule", {"rule_id": "RC-ALCOHOL"}).structured_content
    assert any(s["pmid"] == "30209778" and s["quote"].startswith("Patients often modify their diet") for s in rule["sources"])
    assert call(GUIDE, "get_rule", {"rule_id": "RC-NOPE"}).is_error


def test_list_sources_counts_rules_per_paper():
    sources = call(GUIDE, "list_sources").structured_content["sources"]
    assert sources and all(s["rules"] for s in sources)
    assert sum(1 for s in sources if s["has_quote"]) >= 5


# ---------------------------------------------------------------- evals

EVALS = evals.build_server(evals.load_summary())


def test_evals_tools_results_carry_their_limits():
    assert_read_only(tools_of(EVALS), {"get_results", "pattern_recovery", "check_red_flags"})
    r = call(EVALS, "get_results").structured_content
    assert r["simulated_cohort"] is True and "simulated" in r["limits"]
    assert r["red_flags"]["caught"] == r["red_flags"]["phrases"]


def test_pattern_recovery_by_diary_length():
    r = call(EVALS, "pattern_recovery", {"days": 120}).structured_content
    assert r["simulated"] is True and 0 < r["found"] <= r["true_contributors"]
    assert call(EVALS, "pattern_recovery", {"days": 45}).is_error


def test_check_red_flags_in_bangla_and_english():
    bleeding = call(EVALS, "check_red_flags", {"text": "পায়খানার সাথে অনেক রক্ত যাচ্ছে"}).structured_content
    assert bleeding["triggered"] and bleeding["categories"] == ["heavy_bleeding"] and "doctor" in bleeding["action"]
    fine = call(EVALS, "check_red_flags", {"text": "I had dal and rice"}).structured_content
    assert fine["triggered"] is False


# ---------------------------------------------------------------- journal

def fake_api(seen: list):
    responses = {"/v1/reports/previsit": "previsit.json", "/v1/diary/days": "days.json", "/v1/insights/patterns": "patterns.json"}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.headers.get("authorization") != "Bearer patient-token":
            return httpx.Response(401, json={"detail": "unauthorized"})
        return httpx.Response(200, json=json.loads((FIXTURES / responses[request.url.path]).read_text(encoding="utf-8")))

    return handler


def journal_server(token="patient-token", seen=None):
    seen = [] if seen is None else seen
    transport = httpx.MockTransport(fake_api(seen))
    return journal.build_server(lambda: httpx.Client(transport=transport, base_url="http://api", headers={"Authorization": f"Bearer {token}"}))


def test_journal_tools_are_read_only():
    assert_read_only(tools_of(journal_server()), {"get_overview", "get_recent_days", "get_patterns"})


def test_overview_leaves_out_the_name_and_keeps_the_summary():
    seen = []
    o = call(journal_server(seen=seen), "get_overview", {"days": 60}).structured_content
    assert seen[0].url.params["days"] == "60" and seen[0].method == "GET"
    assert "Nusrat" not in json.dumps(o, ensure_ascii=False)
    assert o["diagnosis"] == "CD" and o["index"]["name"] == "HBI" and o["sample_data"] is True
    assert o["likely_contributors"] and o["medicines"] and o["upcoming_tests"] and o["weight"]["latest"]
    assert "caused" not in o["note"].replace("never 'caused'", "")


def test_recent_days_and_patterns_never_include_notes():
    days = call(journal_server(), "get_recent_days", {"days": 14}).structured_content
    assert len(days["days"]) == 14 and all("notes" not in d for d in days["days"])
    pats = call(journal_server(), "get_patterns", {"scope": "all"}).structured_content
    assert pats["enough_data"] and any(p["label"] == "likely_contributor" for p in pats["results"])


def test_a_withdrawn_sign_in_is_reported_not_guessed():
    r = call(journal_server(token="expired"), "get_overview")
    assert r.is_error and "sign-in" in r.content[0].text
