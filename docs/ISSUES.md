# Issues

Real incidents from my week, newest first.

## 2026-10-04: The test suite wrote a real mainnet wallet into my home folder

- **What I saw:** `uv run pytest` gave `26 failed, 71 passed, 3 xfailed`. Most failures
  printed: `refusing: C:\Users\Huawei\.config\dev3pack\mainnet-wallet.json already
  exists, and it may hold money. Nothing was changed.`
- **What was actually wrong:** the wallet tests redirect the home folder by setting `HOME`.
  Python on Windows reads `USERPROFILE`, so the redirect was ignored. The first test ran
  `mainnet_wallet.py create` against my real `.config\dev3pack` folder. Every later test
  then hit "already exists". My first guess was a bug in my own checks. It wasn't.
- **How I found it:** the failures all came from `tests/test_mainnet_wallet.py` and
  `tests/test_signer.py`, not from `test_your_work.py`. `Get-Item ... | Select Name,
  CreationTime` showed the wallet was created at 11:22 PM local (19:22 UTC), seconds
  before the failing test run.
- **What I changed:** deleted the empty wallet file [confirm: only if you did], and now run
  `uv run pytest --ignore=tests/test_mainnet_wallet.py --ignore=tests/test_signer.py`
  on Windows. Proper fix: run the full suite under WSL2, where `HOME` is honoured.
- **What it cost:** about an hour of confusion. No funds: the wallet was empty, unregistered
  and outside the repository.
- **Would the checks have caught it?** No. The buyer's checks compare a prepared purchase
  with a pin, and nothing in them covers where a test writes a key. The signer refuses a
  key file inside a git repository, but this one was outside it.

## 2026-10-04: The pre-commit key scan broke on Windows

- **What I saw:** `git commit` failed with
  `.githooks/pre-commit: line 3: /c/Users/Huawei/AppData/Local/Microsoft/WindowsApps/python3: Permission denied`.
- **What was actually wrong:** the hook calls `python3`. On my machine that resolves to a
  Microsoft Store stub that cannot run, so the hook errored and git refused the commit.
  Nothing was wrong with the code or the keys.
- **How I found it:** the path in the error pointed at `WindowsApps`, not at the repository.
- **What I changed:** ran the same scan by hand (`uv run python scripts/scan_secrets.py`),
  then committed with `--no-verify`. [confirm: say here whether you also changed line 3 of
  `.githooks/pre-commit` to use `uv run python`.]
- **What it cost:** a few minutes, and one commit that skipped the hook.
- **Would the checks have caught it?** No. The failure is in the tooling around the buyer.
  The danger is that a hook which fails loudly gets bypassed, so the scan has to be run by
  hand every time I use `--no-verify`.

## 2026-10-04: Case 2 passed for the wrong reason

- **What I saw:** `2-ticket` printed `REFUSED on product: asked 'one general-admission
  ticket', pin 'not on the menu'` and `-> MATCH`, with the refusal at the `pin` step.
- **What was actually wrong:** my `parse_intent` raised `Refused` when no menu item matched,
  so the refusal happened before any bytes existed. `check_product` never ran for this
  case. The fixture accepts "not on the menu", so it counted as a match. Case 5 failed the
  same way at first, because "bags" never matched "Beans".
- **How I found it:** the step label in the output was `pin`, not `check`, and the
  expected line allows either.
- **What I changed:** added `bag` to the stop words so case 5 reaches `check_quantity`.
- **What it cost:** nothing signed and no funds. It would have cost me on Friday if a judge
  asked which field decided.
- **Would the checks have caught it?** Partly. The refusal is correct and nothing signs,
  but the field that decided is the parser's, not `check_product`. The fixture's own
  "or: not on the menu" wording hides the difference.