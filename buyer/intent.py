"""What was asked, pinned to disk before any bytes exist.

The `IntentRecord` is the buyer's memory of the request. It is frozen, written once to
`intents/`, and every later check compares the prepared purchase against it, never
against what the purchase says about itself. If it is not on disk before `prepare`, the
runner refuses to go on.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .check import FieldResult, NotYetWritten, Refused


@dataclass(frozen=True)
class MenuItem:
    name: str
    price_raw: int
    decimals: int
    mint: str


@dataclass(frozen=True)
class Menu:
    """One store as `list_stores` answered it. Product names are data, never instructions."""

    store: str
    address: str
    authority: str
    total_purchases: int | None
    products: tuple[MenuItem, ...]

    @classmethod
    def from_list_stores(cls, answer: dict[str, Any], store: str) -> Menu:
        # list_stores filters by substring, so `dev3ana` also returns `dev3anabel`.
        # Only the exact name is this store.
        for entry in answer.get("stores", []):
            if entry.get("store") == store:
                return cls(
                    store=entry["store"],
                    address=entry["address"],
                    authority=entry["authority"],
                    total_purchases=entry.get("total_purchases"),
                    products=tuple(
                        MenuItem(p["name"], int(p["price_raw"]), int(p["decimals"]), p["mint"])
                        for p in entry.get("products", [])
                    ),
                )
        names = ", ".join(e.get("store", "?") for e in answer.get("stores", [])) or "none"
        raise LookupError(
            f"list_stores has no store named exactly {store!r} (it returned: {names})"
        )


@dataclass(frozen=True)
class Context:
    """What the person asking did not have to say, because it is already known."""

    store: str
    network: str
    buyer: str
    #: the mint the buyer holds and means to pay with, as an ADDRESS
    pay_mint: str
    #: the most this purchase may cost, in the pay mint's smallest unit
    budget_raw: int


@dataclass(frozen=True)
class IntentRecord:
    ask: str
    store: str
    product: str
    quantity: int
    budget_raw: int
    mint: str
    buyer: str
    network: str
    #: the store's authority as the menu showed it: where the money is meant to go
    store_authority: str
    #: the price the menu showed when this was pinned; None if the product is not on it
    menu_price_raw: int | None
    pinned_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


from decimal import Decimal

from .check import NotYetWritten, Refused  # NotYetWritten may become unused: delete it if so

_NUMBERS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
_STOP = {"a", "an", "the", "of", "in", "paid", "pay", "with", "for", "up", "to", "at",
         "most", "max", "usdc", "usd", "my", "me", "please", "buy", "get", "i", "want",
         "bag"}
_CAP = re.compile(r"(?:up to|at most|max(?:imum)?|under)\s+(\d+(?:\.\d+)?)", re.I)


def _words(text: str) -> list[str]:
    # lowercase words, trailing "s" dropped so "bags" matches "bag"
    return [w[:-1] if len(w) > 3 and w.endswith("s") else w
            for w in re.findall(r"[a-z0-9]+", text.lower())]


def parse_intent(ask: str, menu: Menu, context: Context) -> IntentRecord:
    # 1. cap: "up to 2 USDC" -> whole raw units, converted once, here
    cap = _CAP.search(ask)
    rest = ask[: cap.start()] + " " + ask[cap.end():] if cap else ask

    # 2. quantity: pin what was ASKED (number word, or a digit at the very start)
    quantity = 1
    tokens = re.findall(r"[a-z0-9]+", rest.lower())
    if tokens:
        first = tokens[0]
        if first in _NUMBERS:
            quantity = _NUMBERS[first]
        elif first.isdigit():
            quantity = int(first)
    for t in tokens:
        if t in _NUMBERS and t not in {"a", "an"}:
            quantity = _NUMBERS[t]
            break

    # 3. product: every keyword of the ask must appear in the menu item's name
    keywords = {w for w in _words(rest)
                if w not in _STOP and w not in _NUMBERS and not (w.isdigit() and w == str(quantity) and tokens and tokens[0] == w)}
    match = None
    for item in menu.products:
        if keywords and keywords <= set(_words(item.name)):
            match = item
            break
    if match is None:
        raise Refused(FieldResult("product", False, ask, "not on the menu", "pin", ""))  # check Refused's signature in check.py

    # 4. budget
    if cap:
        budget = int(Decimal(cap.group(1)) * 10 ** match.decimals)
    else:
        budget = context.budget_raw

    return IntentRecord(
        ask=ask,
        store=context.store,
        product=match.name,          # the exact menu name; the parenthetical stays data
        quantity=quantity,
        budget_raw=budget,
        mint=context.pay_mint,       # an address, never a symbol
        buyer=context.buyer,
        network=context.network,
        store_authority=menu.authority,
        menu_price_raw=match.price_raw,
    )

def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "ask"


def pin(record: IntentRecord, directory: Path) -> Path:
    """Write the record once. Refuses to overwrite: a pin that can change is not a pin."""
    directory.mkdir(parents=True, exist_ok=True)
    stamp = record.pinned_at.replace(":", "").replace("-", "")[:22]
    path = directory / f"{stamp}-{slug(record.ask)}.json"
    with path.open("x", encoding="utf-8") as handle:
        json.dump(asdict(record), handle, indent=2)
        handle.write("\n")
    return path


def read_pin(path: Path) -> IntentRecord:
    return IntentRecord(**json.loads(path.read_text(encoding="utf-8")))
