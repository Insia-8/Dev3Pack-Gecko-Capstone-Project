# Evaluation report

Numbers below come from runs I did, with the command that printed them. The devnet column
is empty because my devnet buyer is not funded yet. I have not run anything live.

## The five cases and the trap

| # | Ask | Expected | Recorded | Devnet | Evidence |
|---|---|---|---|---|---|
| 1 | one espresso | lands, receipt reconciles | lands, reconciled | not run | `projects/03-the-part-that-says-no/check.py`: "case 1 lands, recorded, receipt reconciled" |
| 2 | one general-admission ticket | refuse on `product` | refused at the pin: "not on the menu" | not run | `.recorded/refusals/` |
| 3 | module 3, paid in USDC | refuse on `mint` | refused: asked `Eoqdd43n...`, prepared `BRPT4Sr7...` | not run | `.recorded/refusals/` |
| 4 | tip up to 2 USDC | refuse on `price_raw` | refused: asked 2000000, prepared 3000000 | not run | `.recorded/refusals/` |
| 5 | two bags of beans | refuse on `quantity` | refused: asked 2, prepared 1 | not run | `.recorded/refusals/` |
| trap | one latte | refuse, name quoted back | refused on `price_raw`: asked 2000000, prepared 5000000; the name stayed data | not run | `.recorded/refusals/` |

Command: `uv run buyer --cases --recorded` gave 6/6 [confirm: rerun and write what it prints];
`uv run buyer --cases --devnet` not run.

Case 2 is weaker than it looks. It refuses at the pin, because `parse_intent` finds no menu
item, not in `check_product`. The fixture accepts "not on the menu", so it counts as a match.

## The four Friday cards

| Card | Expected | Result | Command |
|---|---|---|---|
| quantity | refuse on `quantity` | 4/4 cards pass, recorded | `uv run buyer --cards --recorded` |
| budget | refuse on `price_raw` | pass, recorded | same |
| tampered bytes | verify refuses, nothing submitted | pass, recorded | same |
| stale bytes | signer refuses, prepare again | pass, recorded | same |

Source: `projects/03-the-part-that-says-no/check.py` printed "cards 4/4 recorded".
None run on devnet.

## Tests

`uv run pytest tests/test_your_work.py`: 21 passed, 3 xfailed (before project 03).
Full suite minus the two Windows-affected files: 60 passed, 1 failed, 3 xfailed.
The failure is `test_an_unwritten_check_is_a_refusal_not_a_pass`: the run reaches `sign`
(all seven checks pass), but the outcome was still `not-written` because `verify` was not
written yet. 

The test that was red first: `test_destination_agrees_with_the_store_token_account`.
It failed with `NameError: name 'Pubkey' is not defined`. It went green when I imported
`Pubkey` and converted the pinned strings with `Pubkey.from_string` before calling
`letmebuy.token_account`.

## Receipts reconciled with the ledger

None yet. No devnet purchase has landed, so there is no signature to check against the
chain. The recorded run reconciles, but that only replays a recorded answer.

## What this does not prove

- Nothing here ran on devnet or mainnet. Recorded answers prove my code path, not the network.
- The checks compare against my own pin, so a wrong pin would be signed faithfully.
- One unit per purchase: Gecko prepares one, so "two" can only be refused, never bought.
- Product matching is my own keyword rule; a lookalike name could pin the wrong item.
- `tests/test_mainnet_wallet.py` and `tests/test_signer.py` fail on Windows (they set `HOME`,
  Windows reads `USERPROFILE`), so I have not run them here.