import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp.server.mcpserver import MCPServer

from buyer.check import check_all
from buyer.intent import IntentRecord
from buyer.prepared import GeckoRefused, Prepared
from server.guard import is_public_url

mcp = MCPServer("check-purchase")


def _no(field: str, asked, found) -> dict:
    return {"passed": False, "field": field, "asked": asked, "found": found}


@mcp.tool()
def check_purchase(intent: dict, prepared_answer: dict, rpc_url: str | None = None) -> dict:
    """Should I sign this? Compares prepared bytes with a pinned intent. Holds no key."""
    if rpc_url is not None and not is_public_url(rpc_url):
        return _no("rpc_url", "a public https address", rpc_url)
    try:
        record = IntentRecord(**intent)
        prepared = Prepared.from_answer(prepared_answer)
    except GeckoRefused as e:
        return _no("gecko", "a prepared purchase", e.code)
    except (TypeError, ValueError, KeyError) as e:
        return _no("input", "a well-formed intent and prepared answer", str(e)[:200])
    verdict = check_all(record, prepared)
    if verdict.unwritten is not None:
        return _no("check", "all checks written", verdict.unwritten.what)
    if verdict.refusal is not None:
        r = verdict.refusal
        return _no(r.field, r.asked, r.found)
    return {"passed": True, "field": None, "asked": None, "found": None}


if __name__ == "__main__":
    mcp.run()