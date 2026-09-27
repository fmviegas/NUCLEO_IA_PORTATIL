#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NUCLEO IA PORTATIL - smoke-test de execucao de modelo (§25.1)

Sobe o llama-server local com um GGUF, espera carregar, manda UMA pergunta
e mede tokens/s. NAO altera engine/perfis. Uso tipico:

    tools\\smoke_modelo.py --file models\\Qwen3-30B-A3B-Instruct-2507-IQ3_XXS.gguf
    tools\\smoke_modelo.py --file models\\Qwen3-30B-A3B-Instruct-2507-IQ3_XXS.gguf --ngl 12 --backend cuda

Serve para promover um modelo de 'unverified' -> 'validated' no registry:
carregou + respondeu coerente + t/s aceitavel = OK.
"""
import argparse
import json
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _server_exe(backend: str) -> Path:
    return ROOT / "engine" / "windows" / backend / "llama-server.exe"


def _http_json(url: str, api_key: str, payload: dict | None, timeout: float):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET")
    req.add_header("Authorization", f"Bearer {api_key}")
    if data:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _strip_think(text: str) -> str:
    # remove blocos <think>...</think> se o modelo emitir
    import re
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="smoke-test de modelo GGUF")
    ap.add_argument("--file", required=True, help="caminho do .gguf (relativo a raiz ok)")
    ap.add_argument("--backend", default="cpu", choices=["cpu", "cuda"])
    ap.add_argument("--ctx", type=int, default=4096)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--ngl", type=int, default=0, help="n-gpu-layers (so backend cuda)")
    ap.add_argument("--max-tokens", type=int, default=256)
    ap.add_argument("--load-timeout", type=int, default=600,
                    help="segundos para o modelo carregar (modelos grandes = maior)")
    ap.add_argument("--prompt", default=(
        "Explique, em ate 6 frases e em portugues, por que um modelo MoE "
        "(mistura de especialistas) com 30B de parametros totais mas so 3B "
        "ativos por token roda mais rapido que um modelo denso de 30B. "
        "Depois de uma dica pratica de quando usa-lo."))
    args = ap.parse_args()

    exe = _server_exe(args.backend)
    if not exe.exists():
        print(f"[ERRO] llama-server nao encontrado: {exe}")
        return 2

    model = Path(args.file)
    if not model.is_absolute():
        model = (ROOT / model).resolve()
    if not model.exists():
        print(f"[ERRO] modelo nao encontrado: {model}")
        return 2

    api_key = "smoke-" + secrets.token_hex(8)
    port = _free_port()
    ngl = args.ngl if args.backend == "cuda" else 0

    cmd = [
        str(exe),
        "--model", str(model),
        "--threads", str(args.threads),
        "--n-gpu-layers", str(ngl),
        "--ctx-size", str(args.ctx),
        "--host", "127.0.0.1",
        "--port", str(port),
        "--api-key", api_key,
        "--reasoning", "off",
        "--parallel", "1",
        "--no-webui",
    ]

    log_dir = ROOT / "logs" / "smoke"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "smoke-llama-server.log"

    print("=" * 72)
    print("        NUCLEO IA PORTATIL - SMOKE-TEST DE MODELO (execucao real)")
    print("=" * 72)
    print(f"modelo   : {model.name}")
    print(f"backend  : {args.backend} | threads={args.threads} | ngl={ngl} | ctx={args.ctx}")
    print(f"log      : {log_path}")
    print("-" * 72)

    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    proc = None
    t_load0 = time.time()
    try:
        with open(log_path, "w", encoding="utf-8", errors="replace") as logf:
            proc = subprocess.Popen(
                cmd, stdout=logf, stderr=subprocess.STDOUT,
                creationflags=creationflags,
            )

            # espera /health
            health = f"http://127.0.0.1:{port}/health"
            ready = False
            deadline = time.time() + args.load_timeout
            print(f"[..] carregando modelo (timeout {args.load_timeout}s)...", flush=True)
            while time.time() < deadline:
                if proc.poll() is not None:
                    print(f"[ERRO] llama-server encerrou (cod {proc.returncode}). Veja o log.")
                    return 3
                try:
                    _http_json(health, api_key, None, timeout=3)
                    ready = True
                    break
                except Exception:
                    time.sleep(1.5)
            if not ready:
                print("[ERRO] modelo nao ficou pronto no tempo. Veja o log (thrash de RAM?).")
                return 3

            t_load = time.time() - t_load0
            print(f"[OK] carregado em {t_load:.1f}s", flush=True)

            # uma inferencia
            print("[..] enviando pergunta unica...", flush=True)
            payload = {
                "model": "local",
                "messages": [{"role": "user", "content": args.prompt}],
                "max_tokens": args.max_tokens,
                "temperature": 0.7,
                "stream": False,
            }
            t0 = time.time()
            out = _http_json(f"http://127.0.0.1:{port}/v1/chat/completions",
                             api_key, payload, timeout=args.load_timeout)
            dt = time.time() - t0

            text = out.get("choices", [{}])[0].get("message", {}).get("content", "")
            text = _strip_think(text)
            usage = out.get("usage", {}) or {}
            ctoks = usage.get("completion_tokens") or 0
            ptoks = usage.get("prompt_tokens") or 0
            tps = (ctoks / dt) if dt > 0 and ctoks else 0.0

            print("-" * 72)
            print("RESPOSTA:")
            print(text if text else "(vazia)")
            print("-" * 72)
            print(f"carga         : {t_load:.1f}s")
            print(f"geracao       : {dt:.1f}s")
            print(f"prompt tokens : {ptoks}")
            print(f"output tokens : {ctoks}")
            print(f"velocidade    : {tps:.2f} tokens/s")
            print("-" * 72)
            print("Se a resposta ficou coerente e a velocidade aceitavel,")
            print("pode-se promover o modelo para status=validated no registry.")
            return 0
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", "replace")
        except Exception:
            pass
        print(f"[ERRO] HTTP {exc.code}: {body}")
        return 4
    except Exception as exc:  # noqa
        print(f"[ERRO] {type(exc).__name__}: {exc}")
        return 4
    finally:
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=15)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            print("[..] llama-server encerrado.")


if __name__ == "__main__":
    raise SystemExit(main())
