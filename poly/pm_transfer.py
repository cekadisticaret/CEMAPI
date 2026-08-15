"""
Polymarket para transferi — Bridge (yatır/çek) + Relayer ERC-20 gönderim.

CLI:
  python3 pm_transfer.py balance
  python3 pm_transfer.py deposit
  python3 pm_transfer.py withdraw --to 0x... --chain 1 --token USDC
  python3 pm_transfer.py status <bridge_addr>
  python3 pm_transfer.py send --to 0x... --amount 10 --confirm

Ortam:
  POLY_PRIVATE_KEY, POLY_FUNDER  (zorunlu)
  POLY_DRY_RUN=true              (send için; confirm + dry_run=false gerekir)
  POLY_BUILDER_API_KEY / SECRET / PASSPHRASE  (send/relayer için)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any

_DIR = os.path.dirname(os.path.abspath(__file__))
_ENV = os.path.join(_DIR, "..", ".env")
_BRIDGE = "https://bridge.polymarket.com"
_RELAYER = "https://relayer-v2.polymarket.com"
_PUSD = "0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB"
_USDC_E = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
# Yaygın çekim hedefleri (Ethereum native USDC)
_TOKEN_PRESETS = {
    "PUSD": _PUSD,
    "USDC.E": _USDC_E,
    "USDC_E": _USDC_E,
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # Ethereum
    "USDC_POLY": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",  # Polygon native USDC
}

_ERC20_TRANSFER_ABI = [
    {
        "name": "transfer",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "outputs": [{"name": "", "type": "bool"}],
    }
]


def _load_env() -> None:
    if not os.path.exists(_ENV):
        return
    with open(_ENV) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _funder() -> str:
    return (os.getenv("POLY_FUNDER") or "").strip()


def _dry_run() -> bool:
    return os.getenv("POLY_DRY_RUN", "true").lower() in ("1", "true", "yes")


def _builder_ready() -> bool:
    return bool(
        os.getenv("POLY_BUILDER_API_KEY")
        and os.getenv("POLY_BUILDER_SECRET")
        and os.getenv("POLY_BUILDER_PASSPHRASE")
    )


def _relayer_key_ready() -> bool:
    return bool(
        (os.getenv("RELAYER_API_KEY") or "").strip()
        and (os.getenv("RELAYER_API_KEY_ADDRESS") or "").strip()
    )


def _relayer_auth_ready() -> bool:
    """Kişisel hesap: RELAYER_API_KEY. Builder programı: POLY_BUILDER trio."""
    return _relayer_key_ready() or _builder_ready()


def _signature_type() -> int:
    try:
        return int(os.getenv("POLY_SIGNATURE_TYPE", "3") or "3")
    except ValueError:
        return 3


def _use_deposit_wallet() -> bool:
    return _signature_type() == 3


def _relay_client(*, with_builder: bool = False):
    pk = os.getenv("POLY_PRIVATE_KEY", "")
    if not pk:
        raise RuntimeError("POLY_PRIVATE_KEY yok")
    from py_builder_relayer_client.client import RelayClient
    from py_builder_relayer_client.models import RelayerTxType

    builder_config = None
    if with_builder:
        if not _builder_ready():
            raise RuntimeError(
                "Relayer için POLY_BUILDER_API_KEY / POLY_BUILDER_SECRET / POLY_BUILDER_PASSPHRASE gerekli"
            )
        from py_builder_signing_sdk.config import BuilderConfig
        from py_builder_signing_sdk.sdk_types import BuilderApiKeyCreds

        builder_config = BuilderConfig(
            local_builder_creds=BuilderApiKeyCreds(
                key=os.getenv("POLY_BUILDER_API_KEY"),
                secret=os.getenv("POLY_BUILDER_SECRET"),
                passphrase=os.getenv("POLY_BUILDER_PASSPHRASE"),
            )
        )
    return RelayClient(_RELAYER, 137, pk, builder_config, RelayerTxType.PROXY)


def _expected_funder_wallet(client) -> str:
    if _use_deposit_wallet():
        return client.get_expected_deposit_wallet() or ""
    return client.get_expected_proxy_wallet() or ""


def _execute_deposit_wallet_batch(client, *, calls, wallet_address: str, nonce: str, deadline: str):
    """Deposit wallet batch — önce Relayer API key, yoksa Builder HMAC."""
    from py_builder_relayer_client.builder.deposit_wallet import build_deposit_wallet_batch_request
    from py_builder_relayer_client.models import DepositWalletTransactionArgs
    from py_builder_relayer_client.response import ClientRelayerTransactionResponse
    from py_builder_relayer_client.endpoints import SUBMIT_TRANSACTION
    from py_builder_relayer_client.exceptions import RelayerApiException

    args = DepositWalletTransactionArgs(
        from_address=client.signer.address(),
        chain_id=client.chain_id,
        wallet_address=wallet_address,
        nonce=nonce,
        deadline=deadline,
        calls=calls,
    )
    txn_request = build_deposit_wallet_batch_request(
        signer=client.signer,
        args=args,
        config=client.contract_config,
    ).to_dict()

    if _relayer_key_ready():
        import requests

        headers = {
            "Content-Type": "application/json",
            "RELAYER_API_KEY": os.getenv("RELAYER_API_KEY", "").strip(),
            "RELAYER_API_KEY_ADDRESS": os.getenv("RELAYER_API_KEY_ADDRESS", "").strip(),
        }
        r = requests.post(
            f"{_RELAYER}{SUBMIT_TRANSACTION}",
            headers=headers,
            json=txn_request,
            timeout=60,
        )
        if r.status_code != 200:
            raise RelayerApiException(r)
        resp = r.json()
    else:
        if not _builder_ready():
            raise RuntimeError(
                "Relayer auth yok — RELAYER_API_KEY + RELAYER_API_KEY_ADDRESS "
                "veya POLY_BUILDER_API_KEY/SECRET/PASSPHRASE gerekli"
            )
        client.assert_builder_creds_needed()
        resp = client._post_request("POST", SUBMIT_TRANSACTION, txn_request)

    return ClientRelayerTransactionResponse(
        resp.get("transactionID"),
        resp.get("transactionHash"),
        client,
    )


def _http_json(method: str, url: str, body: dict | None = None, timeout: int = 30) -> dict:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "aiProject-pm-transfer"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode(errors="replace")
        try:
            parsed = json.loads(err_body)
        except Exception:
            parsed = {"error": err_body or str(e)}
        parsed["_http_status"] = e.code
        raise RuntimeError(json.dumps(parsed, ensure_ascii=False)) from e


def resolve_token(token: str, *, chain_id: str | None = None) -> str:
    t = (token or "PUSD").strip()
    if t.startswith("0x") and len(t) == 42:
        return t
    key = t.upper().replace("-", "_")
    if key in _TOKEN_PRESETS:
        # Polygon native withdraw hedefi
        if key == "USDC" and chain_id in ("137", "polygon"):
            return _TOKEN_PRESETS["USDC_POLY"]
        return _TOKEN_PRESETS[key]
    raise ValueError(f"bilinmeyen token: {token} (PUSD, USDC, USDC.E veya 0x…)")


# ── Bridge ──────────────────────────────────────────────────────────

def bridge_supported_assets(*, symbol: str | None = None, chain_id: str | None = None) -> list[dict]:
    data = _http_json("GET", f"{_BRIDGE}/supported-assets")
    assets = data.get("supportedAssets") or []
    if symbol:
        s = symbol.upper()
        assets = [a for a in assets if (a.get("token") or {}).get("symbol", "").upper() == s]
    if chain_id:
        assets = [a for a in assets if str(a.get("chainId")) == str(chain_id)]
    return assets


def bridge_deposit_addresses(wallet: str | None = None) -> dict[str, Any]:
    addr = (wallet or _funder()).strip()
    if not addr:
        raise ValueError("POLY_FUNDER / wallet adresi gerekli")
    return _http_json("POST", f"{_BRIDGE}/deposit", {"address": addr})


def bridge_withdraw_addresses(
    *,
    recipient: str,
    to_chain_id: str = "1",
    to_token: str = "USDC",
    wallet: str | None = None,
) -> dict[str, Any]:
    addr = (wallet or _funder()).strip()
    if not addr:
        raise ValueError("POLY_FUNDER / wallet adresi gerekli")
    recipient = recipient.strip()
    if not recipient.startswith("0x") or len(recipient) != 42:
        raise ValueError("recipient 0x… Ethereum adresi olmalı")
    token_addr = resolve_token(to_token, chain_id=str(to_chain_id))
    return _http_json(
        "POST",
        f"{_BRIDGE}/withdraw",
        {
            "address": addr,
            "toChainId": str(to_chain_id),
            "toTokenAddress": token_addr,
            "recipientAddr": recipient,
        },
    )


def bridge_status(deposit_address: str) -> dict[str, Any]:
    return _http_json("GET", f"{_BRIDGE}/status/{deposit_address.strip()}")


def bridge_quote(
    *,
    from_amount_usd: float,
    to_chain_id: str = "1",
    to_token: str = "USDC",
    wallet: str | None = None,
) -> dict[str, Any]:
    """Mümkünse ücret önizlemesi — endpoint şeması değişirse hata döner."""
    addr = (wallet or _funder()).strip()
    body = {
        "address": addr,
        "toChainId": str(to_chain_id),
        "toTokenAddress": resolve_token(to_token, chain_id=str(to_chain_id)),
        "amountUsd": str(from_amount_usd),
    }
    return _http_json("POST", f"{_BRIDGE}/quote", body)


# ── CLOB bakiye / bilgi ─────────────────────────────────────────────

def wallet_info() -> dict[str, Any]:
    from pm_trader_helpers import pm_get_balance

    funder = _funder()
    bal = pm_get_balance()
    eoa = ""
    try:
        from eth_account import Account
        pk = os.getenv("POLY_PRIVATE_KEY", "")
        if pk:
            eoa = Account.from_key(pk).address
    except Exception:
        pass
    expected_wallet = ""
    try:
        if eoa:
            rc = _relay_client(with_builder=False)
            expected_wallet = _expected_funder_wallet(rc)
    except Exception:
        pass
    return {
        "funder": funder,
        "eoa": eoa,
        "expected_proxy": expected_wallet,
        "expected_wallet": expected_wallet,
        "wallet_type": "deposit" if _use_deposit_wallet() else "proxy",
        "proxy_match": bool(
            funder and expected_wallet and funder.lower() == expected_wallet.lower()
        ),
        "balance_usd": round(float(bal), 4) if bal is not None else -1,
        "dry_run": _dry_run(),
        "builder_ready": _relayer_auth_ready(),
        "relayer_key_ready": _relayer_key_ready(),
        "builder_hmac_ready": _builder_ready(),
        "pusd": _PUSD,
        "usdc_e": _USDC_E,
    }


# ── Relayer ERC-20 gönderim ─────────────────────────────────────────

def _encode_erc20_transfer(token: str, to: str, amount_raw: int) -> str:
    from web3 import Web3

    w3 = Web3()
    c = w3.eth.contract(address=Web3.to_checksum_address(token), abi=_ERC20_TRANSFER_ABI)
    return c.encode_abi("transfer", args=[Web3.to_checksum_address(to), int(amount_raw)])


def relay_send_erc20(
    *,
    to: str,
    amount_usd: float,
    token: str = "PUSD",
    confirm: bool = False,
    wait: bool = True,
) -> dict[str, Any]:
    """Deposit/proxy cüzdandan Relayer ile ERC-20 transfer (gasless)."""
    if amount_usd <= 0:
        raise ValueError("amount > 0 olmalı")
    to = to.strip()
    if not to.startswith("0x") or len(to) != 42:
        raise ValueError("to adresi geçersiz")
    if not confirm:
        return {
            "ok": False,
            "dry_run": True,
            "message": "Gerçek gönderim için --confirm ve POLY_DRY_RUN=false gerekli",
            "would_send": {"to": to, "amount_usd": amount_usd, "token": token},
        }
    if _dry_run():
        return {
            "ok": False,
            "dry_run": True,
            "message": "POLY_DRY_RUN=true — gönderim engellendi",
            "would_send": {"to": to, "amount_usd": amount_usd, "token": token},
        }
    if not _relayer_auth_ready():
        raise RuntimeError(
            "Relayer auth yok — polymarket.com/settings → API Keys → Relayer API Keys "
            "(RELAYER_API_KEY + RELAYER_API_KEY_ADDRESS) veya Builder trio gerekli"
        )
    pk = os.getenv("POLY_PRIVATE_KEY", "")
    if not pk:
        raise RuntimeError("POLY_PRIVATE_KEY yok")

    token_addr = resolve_token(token, chain_id="137")
    amount_raw = int(round(float(amount_usd) * 1_000_000))

    client = _relay_client(with_builder=_builder_ready() and not _relayer_key_ready())
    expected = _expected_funder_wallet(client)
    funder = _funder()
    if funder and expected and funder.lower() != expected.lower():
        label = "deposit wallet" if _use_deposit_wallet() else "proxy"
        raise RuntimeError(
            f"Cüzdan uyuşmazlığı ({label}): POLY_FUNDER={funder} expected={expected}"
        )

    data = _encode_erc20_transfer(token_addr, to, amount_raw)
    if _use_deposit_wallet():
        from py_builder_relayer_client.models import DepositWalletCall

        nonce_resp = client.get_nonce(client.signer.address(), "WALLET") or {}
        nonce = str(nonce_resp.get("nonce", "0"))
        deadline = str(int(time.time()) + 240)
        call = DepositWalletCall(target=token_addr, value="0", data=data)
        resp = _execute_deposit_wallet_batch(
            client,
            calls=[call],
            wallet_address=expected,
            nonce=nonce,
            deadline=deadline,
        )
    else:
        from py_builder_relayer_client.models import Transaction

        tx = Transaction(to=token_addr, data=data, value="0")
        resp = client.execute([tx], metadata=f"pm_transfer {amount_usd} -> {to[:10]}")
    out: dict[str, Any] = {
        "ok": True,
        "dry_run": False,
        "transaction_id": getattr(resp, "transaction_id", None) or getattr(resp, "transactionID", None),
        "transaction_hash": getattr(resp, "transaction_hash", None),
        "to": to,
        "amount_usd": amount_usd,
        "token": token_addr,
        "proxy": expected,
    }
    # ClientRelayerTransactionResponse alanları
    if hasattr(resp, "transaction_id"):
        out["transaction_id"] = resp.transaction_id
    elif isinstance(resp, dict):
        out["transaction_id"] = resp.get("transactionID") or resp.get("transaction_id")
        out["transaction_hash"] = resp.get("transactionHash")

    if wait and hasattr(resp, "wait"):
        try:
            result = resp.wait()
            out["result"] = result if isinstance(result, dict) else {"raw": str(result)}
        except Exception as e:
            out["wait_error"] = str(e)
    return out


# ── CLI ─────────────────────────────────────────────────────────────

def _print(obj: Any) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def main(argv: list[str] | None = None) -> int:
    _load_env()
    sys.path.insert(0, _DIR)
    p = argparse.ArgumentParser(description="Polymarket transfer (bridge + relayer)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("balance", help="CLOB bakiye + cüzdan bilgisi")
    sub.add_parser("deposit", help="Yatırma bridge adresleri")

    pw = sub.add_parser("withdraw", help="Çekim bridge adresleri üret")
    pw.add_argument("--to", required=True, help="Alıcı cüzdan")
    pw.add_argument("--chain", default="1", help="Hedef chainId (1=Ethereum, 137=Polygon, 8453=Base)")
    pw.add_argument("--token", default="USDC", help="USDC | PUSD | USDC.E | 0x…")

    ps = sub.add_parser("status", help="Bridge transfer durumu")
    ps.add_argument("address", help="Bridge adresi")

    pq = sub.add_parser("quote", help="Çekim ücret önizlemesi")
    pq.add_argument("--amount", type=float, required=True)
    pq.add_argument("--chain", default="1")
    pq.add_argument("--token", default="USDC")

    psend = sub.add_parser("send", help="Proxy'den ERC-20 gönder (Relayer)")
    psend.add_argument("--to", required=True)
    psend.add_argument("--amount", type=float, required=True)
    psend.add_argument("--token", default="PUSD")
    psend.add_argument("--confirm", action="store_true")
    psend.add_argument("--no-wait", action="store_true")

    pa = sub.add_parser("assets", help="Desteklenen bridge asset listesi")
    pa.add_argument("--symbol", default=None)
    pa.add_argument("--chain", default=None)

    args = p.parse_args(argv)
    try:
        if args.cmd == "balance":
            _print(wallet_info())
        elif args.cmd == "deposit":
            _print(bridge_deposit_addresses())
        elif args.cmd == "withdraw":
            _print(bridge_withdraw_addresses(
                recipient=args.to, to_chain_id=args.chain, to_token=args.token,
            ))
        elif args.cmd == "status":
            _print(bridge_status(args.address))
        elif args.cmd == "quote":
            _print(bridge_quote(
                from_amount_usd=args.amount, to_chain_id=args.chain, to_token=args.token,
            ))
        elif args.cmd == "send":
            _print(relay_send_erc20(
                to=args.to, amount_usd=args.amount, token=args.token,
                confirm=bool(args.confirm), wait=not args.no_wait,
            ))
        elif args.cmd == "assets":
            assets = bridge_supported_assets(symbol=args.symbol, chain_id=args.chain)
            _print({"count": len(assets), "assets": assets[:40]})
        else:
            p.error("bilinmeyen komut")
            return 2
        return 0
    except Exception as e:
        print(f"HATA: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
