from __future__ import annotations

import json
import os
from pathlib import Path
import sys

try:
    from algosdk import account, mnemonic
    from algosdk.v2client import algod
    _ALGOSDK_IMPORT_ERROR: Exception | None = None
except Exception as exc:  # pragma: no cover - handled at runtime
    account = None  # type: ignore[assignment]
    mnemonic = None  # type: ignore[assignment]
    algod = None  # type: ignore[assignment]
    _ALGOSDK_IMPORT_ERROR = exc


def _runtime_root_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[3]


class AlgorandWallet:
    def __init__(self, wallet_file: Path | None = None) -> None:
        if algod is None or account is None or mnemonic is None:
            detail = str(_ALGOSDK_IMPORT_ERROR) if _ALGOSDK_IMPORT_ERROR else "Unknown import error"
            raise RuntimeError(
                f"py-algorand-sdk unavailable for interpreter {sys.executable}: {detail}"
            )

        self.algod_address = (
            os.environ.get("NUROCHAIN_ALGOD_ADDRESS", "https://testnet-api.algonode.cloud").strip()
            or "https://testnet-api.algonode.cloud"
        )
        self.algod_token = os.environ.get("NUROCHAIN_ALGOD_TOKEN", "").strip()
        self.algod_client = algod.AlgodClient(self.algod_token, self.algod_address)
        default_wallet_file = _runtime_root_dir() / "data" / "keystore.json"
        self.wallet_file = wallet_file if wallet_file is not None else default_wallet_file
        self.address: str | None = None
        self.private_key: str | None = None
        self.last_error: str | None = None

        self._load_or_create_wallet()

    def _load_or_create_wallet(self) -> None:
        self.wallet_file.parent.mkdir(parents=True, exist_ok=True)

        if self.wallet_file.exists():
            try:
                payload = json.loads(self.wallet_file.read_text(encoding="utf-8"))
                address = str(payload.get("address", "")).strip()
                mnemonic_phrase = str(payload.get("mnemonic", "")).strip()
                if address and mnemonic_phrase:
                    self.address = address
                    self.private_key = mnemonic.to_private_key(mnemonic_phrase)
                    return
            except Exception:
                # Regenerate the wallet if file contents are invalid.
                pass

        self.private_key, self.address = account.generate_account()
        passphrase = mnemonic.from_private_key(self.private_key)
        self.wallet_file.write_text(
            json.dumps(
                {
                    "address": self.address,
                    "mnemonic": passphrase,
                },
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )

    def get_balance(self) -> float:
        self.last_error = None
        if not self.address:
            self.last_error = "Wallet address unavailable"
            return 0.0
        try:
            account_info = self.algod_client.account_info(self.address)
            micro_algos = float(account_info.get("amount", 0))
            return micro_algos / 1_000_000.0
        except Exception as exc:
            self.last_error = str(exc)
            return 0.0
