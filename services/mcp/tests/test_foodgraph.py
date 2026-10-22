import anyio
import httpx
import pytest

from happygut_mcp.foodgraph import BearerAuth, build_server
from happygut_pipelines.graph import MemoryGraph
from mcp import Client

GRAPH = MemoryGraph.from_seeds(include_drafts=True)


def call(tool, args):
    async def go():
        async with Client(build_server(GRAPH)) as client:
            return await client.call_tool(tool, args)
    return anyio.run(go)


def test_three_read_only_tools():
    async def go():
        async with Client(build_server(GRAPH)) as client:
            return (await client.list_tools()).tools
    tools = {t.name: t for t in anyio.run(go)}
    assert set(tools) == {"search_dish", "get_components", "explain_verdict_path"}
    for t in tools.values():
        assert t.annotations.read_only_hint is True
        assert t.annotations.destructive_hint is False
        assert t.output_schema is not None, "tools return structured output"


def test_search_dish_banglish_sentence():
    r = call("search_dish", {"query": "ajke dupure kacchi khabo"})
    assert not r.is_error
    assert r.structured_content["candidates"][0]["dish_id"] == "dish.kacchi_biryani"


def test_search_dish_unknown_explains_not_sure():
    r = call("search_dish", {"query": "pepperoni pizza"})
    assert r.structured_content["candidates"] == []
    assert "Not sure" in r.structured_content["note"]


def test_get_components():
    r = call("get_components", {"dish_id": "dish.shorshe_ilish"})
    data = r.structured_content
    assert data["components"]["fat"] == "high"
    assert data["components"]["skins_seeds_nuts"] == "medium"
    assert "dish.rui_macher_patla_jhol" in data["gentler_alternatives"]


def test_explain_verdict_path_stricture_hard_rule_first():
    r = call("explain_verdict_path", {"dish_id": "dish.shak_bhaji", "diagnosis": "CD", "phenotypes": ["stricturing"]})
    steps = r.structured_content["steps"]
    assert steps[0]["hard"] is True and steps[0]["rule_id"] == "RC-STRICT-001"
    assert steps[0]["sources"][0]["citation"]
    assert "engine" in r.structured_content["note"]


def test_invalid_inputs_are_rejected():
    assert call("get_components", {"dish_id": "'; MATCH (n) DETACH DELETE n //"}).is_error
    assert call("explain_verdict_path", {"dish_id": "dish.dal", "diagnosis": "XX"}).is_error
    assert call("explain_verdict_path", {"dish_id": "dish.plain_rice", "diagnosis": "CD", "phenotypes": ["vegan"]}).is_error
    assert call("search_dish", {"query": "x" * 500}).is_error


def test_unknown_dish_is_an_error_not_a_guess():
    assert call("get_components", {"dish_id": "dish.does_not_exist"}).is_error


@pytest.mark.parametrize("header,status", [(None, 401), ("Bearer wrong-token-xxxxxxxxxxxxxxxxxx", 401)])
def test_http_requires_bearer_token(header, status):
    async def inner(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    app = BearerAuth(inner, "correct-token-xxxxxxxxxxxxxxxxxxxx")

    async def go():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
            headers = {"authorization": header} if header else {}
            bad = await c.post("/mcp", headers=headers)
            good = await c.post("/mcp", headers={"authorization": "Bearer correct-token-xxxxxxxxxxxxxxxxxxxx"})
            return bad.status_code, good.status_code
    assert anyio.run(go) == (status, 200)


def test_short_token_refused():
    with pytest.raises(ValueError):
        BearerAuth(lambda *a: None, "short")
