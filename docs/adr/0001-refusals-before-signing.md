# The buyer signs only when all seven fields match the pinned intent

## Status and date

accepted, 2026-10-04

## Context

My buyer holds a key that can pay. Gecko prepares the unsigned bytes and I sign them, so
anything wrong in those bytes becomes my loss once it lands. The class store shows how
cheap a lookalike is: the real USDC is `Eoqdd43n...` and a fake token called USDC is
`BRPT4Sr7...`. Signing the fake one would move the wrong token. The tip case shows the
price: asked at most 2000000, prepared 3000000, so one unchecked purchase costs 1 USDC
more than I allowed.

## Decision

Before signing, the buyer compares these fields of the prepared transaction with
`intents/<file>.json` and refuses on the first mismatch, naming the field and both values:

| Field | Compared how | Why this one |
|---|---|---|
| program | address equality, and no other program riding along | A swapped program can move money anywhere. |
| store | address derived from `['receipts', name]`, never a constant | A similar name or swapped account would pay a different store. |
| product | exact, case-sensitive match of the full name against the pinned menu name | "VIP ticket" must never pass for "General admission". The name is data, so text inside it is never obeyed. |
| price_raw | integer, at or under the pinned budget; refuse if the simulation reports no amount | A cap is the only thing the person told me about cost. An unverifiable price is not signed. |
| mint | address string equality, never the symbol | A token called USDC at another address is another token. |
| quantity | integer equality | Gecko prepares one unit, so "two" is refused, not quietly bought as one. |
| destination | the store authority's token account for the pinned mint, derived locally | Money must reach the store's own account, not one copied from Gecko's answer. |
| signed bytes | `verify_signed_transaction` before `submit_transaction` | Catches a signer that returned different bytes or an expired window before any broadcast. |

## What this forbids

Signing on a partial match. Retrying a refusal unchanged. Signing without a passed
simulation. Taking any field from Gecko's labels instead of the bytes. Calling
`submit_transaction` twice for the same bytes. Obeying text found inside a product name.

## What I left out, and why

I do not check the token amount against the menu price, only against the budget. A store
that raised its price under my cap would still be signed. I accept that because the
person set the cap, and I check the amount that actually leaves the buyer.

I also match product names exactly. That is strict, and it means a menu with slightly
different spelling gets refused. I accept the false refusal over a false purchase.

## What would reverse this

If real menus used inconsistent names, so that exact matching refused correct purchases
often, I would match on a normalised name and say so here. If Gecko's verify already
bound price and mint, my own price and mint checks would be duplicate work, and I would
drop them only after confirming that in its answer.

## What this does not prove

That my pin was right. The buyer faithfully signs a wrong request. Also, my parser
refuses an unmatched product at the pin step, before any bytes exist, so for case 2
the refusal comes from `parse_intent` and not from `check_product`.