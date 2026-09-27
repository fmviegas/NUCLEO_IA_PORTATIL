#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NÚCLEO IA PORTÁTIL — AutoTune V0.2.1

Patch de confiabilidade sobre a V0.2.

Principais correções:
1) Windows AVX/AVX2:
   - usa os IDs oficiais atuais de IsProcessorFeaturePresent:
       AVX=39, AVX2=40, AVX512F=41
   - aplica regra de consistência: AVX2 implica AVX.
2) Secure Boot:
   - consulta Confirm-SecureBootUEFI quando possível;
   - usa o Registro do Windows como fallback;
   - reconcilia as fontes e informa confiança/consistência.
3) Armazenamento:
   - identifica a unidade onde o AutoTune está sendo executado;
   - tenta identificar disco físico, BusType (USB/NVMe/SATA...), filesystem;
   - benchmark maior e explicitamente marcado como "cache-sensitive";
   - separa o resultado do benchmark da identidade do dispositivo.
4) Confiança:
   - CPU features e Secure Boot passam a carregar fonte e confiança.
5) Compatibilidade:
   - mantém a assinatura de Machine ID da V0.1/V0.2.

Sem dependências Python externas.
Não instala drivers, não altera BIOS/UEFI, não formata e não baixa arquivos.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import platform
import re
import shutil
import statistics
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

APP_NAME = "NÚCLEO IA PORTÁTIL"
VERSION = "0.2.1"

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
CONFIG_DIR = ROOT / "state" / "hardware"
PROFILES_DIR = ROOT / "profiles" / "machines"
MODELS_DIR = ROOT / "models"
LOGS_DIR = ROOT / "logs" / "hardware"
ENGINE_DIR = ROOT / "engine"

for d in (CONFIG_DIR, PROFILES_DIR, MODELS_DIR, LOGS_DIR):
    d.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


def gb(n: int | float) -> float:
    return round(float(n) / (1024 ** 3), 2)


def run_command(
    command: List[str],
    timeout: int = 15,
    cwd: Optional[Path] = None
) -> Tuple[int, str, str]:
    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    try:
        p = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            creationflags=creationflags,
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return 1, "", str(exc)


def powershell_json(script: str, timeout: int = 15) -> Optional[Any]:
    ps = shutil.which("powershell") or shutil.which("pwsh")
    if not ps:
        return None

    code, out, _ = run_command(
        [
            ps,
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-Command",
            "$ProgressPreference='SilentlyContinue'; "
            "$ErrorActionPreference='SilentlyContinue'; "
            + script
        ],
        timeout=timeout,
    )
    if code != 0 or not out:
        return None

    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def json_dump(path: Path, obj: Any) -> None:
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def bool_text(v: Optional[bool]) -> str:
    if v is True:
        return "SIM"
    if v is False:
        return "NÃO"
    return "N/D"


# ---------------------------------------------------------------------------
# Estruturas
# ---------------------------------------------------------------------------

@dataclass
class Detection:
    value: Optional[bool]
    source: str
    confidence: str
    status: str = "ok"
    detail: str = ""


@dataclass
class CPUFeatures:
    sse3: Detection
    avx: Detection
    avx2: Detection
    avx512f: Detection


@dataclass
class GPUInfo:
    name: str
    vendor: str
    vram_gb: float
    driver: str = ""
    nvidia_smi: bool = False


@dataclass
class StorageInfo:
    current_path: str
    drive: str
    filesystem: str
    volume_label: str
    disk_number: Optional[int]
    friendly_name: str
    bus_type: str
    media_type: str
    partition_style: str
    size_gb: float
    is_boot: Optional[bool]
    is_system: Optional[bool]
    identification_confidence: str


@dataclass
class StorageBenchmark:
    test_size_mb: int
    write_mb_s_samples: List[float]
    read_mb_s_samples: List[float]
    write_mb_s_median: float
    read_mb_s_median: float
    test_path: str
    cache_sensitive: bool
    note: str


@dataclass
class HardwareInfo:
    os: str
    os_version: str
    architecture: str
    hostname: str
    manufacturer: str
    model: str
    cpu: str
    physical_cores: int
    logical_threads: int
    cpu_features: CPUFeatures
    ram_total_gb: float
    ram_available_gb: float
    gpus: List[GPUInfo]
    nvidia_detected: bool
    nvidia_driver_ok: bool
    secure_boot: Detection
    bios_mode: str
    storage: StorageInfo


@dataclass
class EngineStatus:
    selected_backend: str
    cuda_bundle_present: bool
    cpu_bundle_present: bool
    llama_cuda_ready: bool
    llama_bench: str
    llama_cli: str
    llama_server: str
    details: List[str]


@dataclass
class Recommendation:
    profile: str
    model_class: str
    quantization: str
    context_size: int
    backend: str
    gpu_offload_policy: str
    initial_gpu_layers: int
    gpu_vram_budget_gb: float
    cpu_threads: int
    notes: List[str]


# ---------------------------------------------------------------------------
# Detecção de CPU — Windows
# ---------------------------------------------------------------------------

def _ispfp(feature_id: int) -> Optional[bool]:
    """IsProcessorFeaturePresent; None se a API não puder ser consultada."""
    try:
        fn = ctypes.windll.kernel32.IsProcessorFeaturePresent
        fn.argtypes = [ctypes.c_uint]
        fn.restype = ctypes.c_bool
        return bool(fn(feature_id))
    except Exception:
        return None


def detect_cpu_features_windows() -> CPUFeatures:
    # Microsoft PROCESSOR_FEATURE_ID:
    # SSE3=13, AVX=39, AVX2=40, AVX512F=41.
    sse3_raw = _ispfp(13)
    avx_raw = _ispfp(39)
    avx2_raw = _ispfp(40)
    avx512_raw = _ispfp(41)

    source = "Windows IsProcessorFeaturePresent"

    sse3 = Detection(
        value=sse3_raw,
        source=f"{source} (PF_SSE3=13)",
        confidence="alta" if sse3_raw is not None else "baixa",
    )
    avx = Detection(
        value=avx_raw,
        source=f"{source} (PF_AVX=39)",
        confidence="alta" if avx_raw is not None else "baixa",
    )
    avx2 = Detection(
        value=avx2_raw,
        source=f"{source} (PF_AVX2=40)",
        confidence="alta" if avx2_raw is not None else "baixa",
    )
    avx512 = Detection(
        value=avx512_raw,
        source=f"{source} (PF_AVX512F=41)",
        confidence="alta" if avx512_raw is not None else "baixa",
    )

    # Regra lógica de consistência. AVX2 depende de AVX/estado AVX utilizável.
    if avx2.value is True and avx.value is not True:
        avx = Detection(
            value=True,
            source=avx.source + " + inferência AVX2⇒AVX",
            confidence="alta",
            status="reconciliado",
            detail="AVX2 foi reportado disponível; AVX foi elevado para verdadeiro por consistência.",
        )

    return CPUFeatures(sse3=sse3, avx=avx, avx2=avx2, avx512f=avx512)


def detect_cpu_features_linux() -> CPUFeatures:
    try:
        text = Path("/proc/cpuinfo").read_text(
            encoding="utf-8", errors="replace"
        ).lower()
        flags = set()
        for line in text.splitlines():
            if line.startswith("flags") and ":" in line:
                flags.update(line.split(":", 1)[1].split())

        def d(value: bool, name: str) -> Detection:
            return Detection(
                value=value,
                source=f"/proc/cpuinfo flags ({name})",
                confidence="alta",
            )

        return CPUFeatures(
            sse3=d("pni" in flags or "sse3" in flags, "sse3/pni"),
            avx=d("avx" in flags, "avx"),
            avx2=d("avx2" in flags, "avx2"),
            avx512f=d("avx512f" in flags, "avx512f"),
        )
    except Exception as exc:
        nd = Detection(None, "/proc/cpuinfo", "baixa", "erro", str(exc))
        return CPUFeatures(nd, nd, nd, nd)


# ---------------------------------------------------------------------------
# Secure Boot — Windows
# ---------------------------------------------------------------------------

def secure_boot_registry() -> Optional[bool]:
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\SecureBoot\State",
        )
        value, _ = winreg.QueryValueEx(key, "UEFISecureBootEnabled")
        winreg.CloseKey(key)
        return bool(int(value))
    except Exception:
        return None


def secure_boot_powershell() -> Optional[bool]:
    result = powershell_json(
        """
        $v = $null;
        try { $v = Confirm-SecureBootUEFI } catch {}
        [PSCustomObject]@{ Value = $v } | ConvertTo-Json -Compress
        """
    )
    if isinstance(result, dict) and isinstance(result.get("Value"), bool):
        return result["Value"]
    return None


def reconcile_secure_boot(ps: Optional[bool], reg: Optional[bool]) -> Detection:
    if ps is not None and reg is not None:
        if ps == reg:
            return Detection(
                value=ps,
                source="Confirm-SecureBootUEFI + Registro SecureBoot\\State",
                confidence="alta",
                status="consistente",
            )
        return Detection(
            value=reg,
            source="Confirm-SecureBootUEFI + Registro SecureBoot\\State",
            confidence="baixa",
            status="inconsistente",
            detail=(
                f"Fontes divergentes: PowerShell={ps}, Registro={reg}. "
                "Mantido Registro como valor operacional, mas não usar para decisão destrutiva."
            ),
        )

    if reg is not None:
        return Detection(
            value=reg,
            source=r"Registro HKLM...\SecureBoot\State\UEFISecureBootEnabled",
            confidence="média-alta",
            status="fonte_unica",
            detail="Confirm-SecureBootUEFI não retornou valor; Registro usado como fallback.",
        )

    if ps is not None:
        return Detection(
            value=ps,
            source="Confirm-SecureBootUEFI",
            confidence="média-alta",
            status="fonte_unica",
        )

    return Detection(
        value=None,
        source="Secure Boot não disponível",
        confidence="baixa",
        status="indeterminado",
    )


# ---------------------------------------------------------------------------
# Armazenamento
# ---------------------------------------------------------------------------

def current_drive_windows() -> str:
    drive = Path(ROOT).drive
    if drive:
        return drive.rstrip("\\/")
    return ""


def detect_storage_windows() -> StorageInfo:
    drive = current_drive_windows()
    drive_letter = drive.replace(":", "")
    if not drive_letter:
        return StorageInfo(
            current_path=str(ROOT),
            drive="",
            filesystem="",
            volume_label="",
            disk_number=None,
            friendly_name="",
            bus_type="",
            media_type="",
            partition_style="",
            size_gb=0.0,
            is_boot=None,
            is_system=None,
            identification_confidence="baixa",
        )

    result = powershell_json(
        rf"""
        $letter = '{drive_letter}';
        $vol = Get-Volume -DriveLetter $letter -ErrorAction SilentlyContinue;
        $part = Get-Partition -DriveLetter $letter -ErrorAction SilentlyContinue;
        $disk = $null;
        if ($part) {{ $disk = $part | Get-Disk -ErrorAction SilentlyContinue; }}
        $pd = $null;
        if ($disk) {{
            try {{
                $pd = Get-PhysicalDisk |
                    Where-Object {{ $_.FriendlyName -eq $disk.FriendlyName }} |
                    Select-Object -First 1;
            }} catch {{}}
        }}
        [PSCustomObject]@{{
            Drive = "$letter`:";
            FileSystem = if ($vol) {{ $vol.FileSystem }} else {{ "" }};
            VolumeLabel = if ($vol) {{ $vol.FileSystemLabel }} else {{ "" }};
            DiskNumber = if ($disk) {{ $disk.Number }} else {{ $null }};
            FriendlyName = if ($disk) {{ $disk.FriendlyName }} else {{ "" }};
            BusType = if ($disk) {{ [string]$disk.BusType }} else {{ "" }};
            MediaType = if ($pd) {{ [string]$pd.MediaType }} else {{ "" }};
            PartitionStyle = if ($disk) {{ [string]$disk.PartitionStyle }} else {{ "" }};
            Size = if ($disk) {{ [UInt64]$disk.Size }} else {{ 0 }};
            IsBoot = if ($disk) {{ [bool]$disk.IsBoot }} else {{ $null }};
            IsSystem = if ($disk) {{ [bool]$disk.IsSystem }} else {{ $null }}
        }} | ConvertTo-Json -Compress
        """
    )

    if not isinstance(result, dict):
        return StorageInfo(
            current_path=str(ROOT.resolve()),
            drive=drive,
            filesystem="",
            volume_label="",
            disk_number=None,
            friendly_name="",
            bus_type="",
            media_type="",
            partition_style="",
            size_gb=0.0,
            is_boot=None,
            is_system=None,
            identification_confidence="baixa",
        )

    return StorageInfo(
        current_path=str(ROOT.resolve()),
        drive=str(result.get("Drive") or drive),
        filesystem=str(result.get("FileSystem") or ""),
        volume_label=str(result.get("VolumeLabel") or ""),
        disk_number=(
            safe_int(result.get("DiskNumber"))
            if result.get("DiskNumber") is not None else None
        ),
        friendly_name=str(result.get("FriendlyName") or ""),
        bus_type=str(result.get("BusType") or ""),
        media_type=str(result.get("MediaType") or ""),
        partition_style=str(result.get("PartitionStyle") or ""),
        size_gb=gb(safe_int(result.get("Size"))),
        is_boot=result.get("IsBoot") if isinstance(result.get("IsBoot"), bool) else None,
        is_system=result.get("IsSystem") if isinstance(result.get("IsSystem"), bool) else None,
        identification_confidence="alta" if result.get("FriendlyName") else "média",
    )


def detect_storage_linux() -> StorageInfo:
    # V0.2.1: identificação mínima; aprofundaremos no Linux bootável.
    try:
        st = os.statvfs(ROOT)
        _ = st  # reservado para futura expansão
    except Exception:
        pass

    return StorageInfo(
        current_path=str(ROOT.resolve()),
        drive=str(ROOT.anchor),
        filesystem="",
        volume_label="",
        disk_number=None,
        friendly_name="",
        bus_type="",
        media_type="",
        partition_style="",
        size_gb=0.0,
        is_boot=None,
        is_system=None,
        identification_confidence="baixa",
    )


def benchmark_storage(
    size_mb: int = 256,
    passes: int = 2,
) -> StorageBenchmark:
    """
    Benchmark deliberadamente seguro e não destrutivo.
    Mede a unidade que contém o programa.

    AVISO: o cache do SO pode inflar sobretudo leitura. Por isso o resultado
    é marcado cache_sensitive=True e não é usado sozinho para classificar IA.
    """
    path = ROOT / ".autotune_storage_benchmark.tmp"
    block_mb = 4
    block = os.urandom(block_mb * 1024 * 1024)
    write_samples: List[float] = []
    read_samples: List[float] = []

    total_bytes = size_mb * 1024 * 1024

    try:
        for _pass in range(max(1, passes)):
            start = time.perf_counter()
            with path.open("wb", buffering=0) as f:
                remaining = total_bytes
                while remaining > 0:
                    chunk = block if remaining >= len(block) else block[:remaining]
                    f.write(chunk)
                    remaining -= len(chunk)
                f.flush()
                os.fsync(f.fileno())
            elapsed = max(time.perf_counter() - start, 1e-9)
            write_samples.append(round(size_mb / elapsed, 1))

            start = time.perf_counter()
            with path.open("rb", buffering=0) as f:
                while f.read(len(block)):
                    pass
            elapsed = max(time.perf_counter() - start, 1e-9)
            read_samples.append(round(size_mb / elapsed, 1))

        return StorageBenchmark(
            test_size_mb=size_mb,
            write_mb_s_samples=write_samples,
            read_mb_s_samples=read_samples,
            write_mb_s_median=round(statistics.median(write_samples), 1),
            read_mb_s_median=round(statistics.median(read_samples), 1),
            test_path=str(ROOT.resolve()),
            cache_sensitive=True,
            note=(
                "Indicador de throughput do caminho atual. O cache do sistema operacional "
                "pode inflar a leitura; use BusType/MediaType e, futuramente, benchmark "
                "do llama.cpp para decisões de IA."
            ),
        )
    except Exception as exc:
        return StorageBenchmark(
            test_size_mb=size_mb,
            write_mb_s_samples=[],
            read_mb_s_samples=[],
            write_mb_s_median=0.0,
            read_mb_s_median=0.0,
            test_path=str(ROOT.resolve()),
            cache_sensitive=True,
            note=f"Benchmark falhou: {exc}",
        )
    finally:
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Hardware Windows/Linux
# ---------------------------------------------------------------------------

def detect_windows() -> HardwareInfo:
    info = powershell_json(
        """
        $cs = Get-CimInstance Win32_ComputerSystem;
        $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1;
        $os = Get-CimInstance Win32_OperatingSystem;
        $gpus = Get-CimInstance Win32_VideoController |
            Select-Object Name, AdapterRAM, DriverVersion, PNPDeviceID;
        [PSCustomObject]@{
            Manufacturer = $cs.Manufacturer;
            Model = $cs.Model;
            CPUName = $cpu.Name;
            PhysicalCores = $cpu.NumberOfCores;
            LogicalThreads = $cpu.NumberOfLogicalProcessors;
            RAMTotal = $cs.TotalPhysicalMemory;
            RAMFreeKB = $os.FreePhysicalMemory;
            BIOSMode = if ($env:firmware_type) { $env:firmware_type } else { "não determinado" };
            GPUs = @($gpus)
        } | ConvertTo-Json -Depth 5 -Compress
        """
    )

    manufacturer = ""
    model = ""
    cpu = platform.processor() or "Processador não identificado"
    physical = 0
    logical = os.cpu_count() or 1
    ram_total = 0.0
    ram_available = 0.0
    bios_mode = "não determinado"
    gpus: List[GPUInfo] = []

    if isinstance(info, dict):
        manufacturer = str(info.get("Manufacturer") or "").strip()
        model = str(info.get("Model") or "").strip()
        cpu = str(info.get("CPUName") or cpu).strip()
        physical = safe_int(info.get("PhysicalCores"))
        logical = safe_int(info.get("LogicalThreads"), logical)
        ram_total = gb(safe_int(info.get("RAMTotal")))
        ram_available = round(
            safe_int(info.get("RAMFreeKB")) / (1024 ** 2), 2
        )
        bios_mode = str(info.get("BIOSMode") or "não determinado")

        raw_gpus = info.get("GPUs") or []
        if isinstance(raw_gpus, dict):
            raw_gpus = [raw_gpus]

        for raw in raw_gpus:
            name = str(raw.get("Name") or "GPU desconhecida")
            pnp = str(raw.get("PNPDeviceID") or "")
            sig = f"{name} {pnp}".upper()
            if "NVIDIA" in sig:
                vendor = "NVIDIA"
            elif "AMD" in sig or "RADEON" in sig:
                vendor = "AMD"
            elif "INTEL" in sig:
                vendor = "Intel"
            else:
                vendor = "desconhecido"

            aram = safe_int(raw.get("AdapterRAM"))
            gpus.append(GPUInfo(
                name=name,
                vendor=vendor,
                vram_gb=gb(aram) if aram > 0 else 0.0,
                driver=str(raw.get("DriverVersion") or ""),
            ))

    # Memória: fallback Win32 API.
    if ram_total <= 0:
        try:
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            ram_total = gb(stat.ullTotalPhys)
            ram_available = gb(stat.ullAvailPhys)
        except Exception:
            pass

    # NVIDIA: nvidia-smi corrige VRAM e valida o driver.
    smi = shutil.which("nvidia-smi")
    driver_ok = False
    if smi:
        code, out, _ = run_command([
            smi,
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader,nounits",
        ])
        if code == 0 and out:
            driver_ok = True
            nvidia_gpus: List[GPUInfo] = []
            for line in out.splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 2:
                    nvidia_gpus.append(GPUInfo(
                        name=parts[0],
                        vendor="NVIDIA",
                        vram_gb=round(safe_int(parts[1]) / 1024, 2),
                        driver=parts[2] if len(parts) > 2 else "",
                        nvidia_smi=True,
                    ))
            if nvidia_gpus:
                gpus = [g for g in gpus if g.vendor != "NVIDIA"] + nvidia_gpus

    secure_boot = reconcile_secure_boot(
        secure_boot_powershell(),
        secure_boot_registry(),
    )

    return HardwareInfo(
        os=f"{platform.system()} {platform.release()}",
        os_version=platform.version(),
        architecture=platform.machine(),
        hostname=platform.node(),
        manufacturer=manufacturer,
        model=model,
        cpu=cpu,
        physical_cores=physical,
        logical_threads=logical,
        cpu_features=detect_cpu_features_windows(),
        ram_total_gb=ram_total,
        ram_available_gb=ram_available,
        gpus=gpus,
        nvidia_detected=any(g.vendor == "NVIDIA" for g in gpus),
        nvidia_driver_ok=driver_ok,
        secure_boot=secure_boot,
        bios_mode=bios_mode,
        storage=detect_storage_windows(),
    )


def detect_linux() -> HardwareInfo:
    cpu = platform.processor() or "Processador não identificado"
    physical = 0
    logical = os.cpu_count() or 1
    ram_total = ram_available = 0.0
    manufacturer = model = ""
    gpus: List[GPUInfo] = []

    code, out, _ = run_command(["bash", "-lc", "lscpu"])
    if code == 0:
        vals = {}
        for line in out.splitlines():
            if ":" in line:
                k, v = [x.strip() for x in line.split(":", 1)]
                vals[k] = v
        cpu = vals.get("Model name", cpu)
        sockets = safe_int(vals.get("Socket(s)"), 1)
        cps = safe_int(vals.get("Core(s) per socket"), 0)
        physical = sockets * cps if cps else 0

    try:
        text = Path("/proc/meminfo").read_text(
            encoding="utf-8", errors="replace"
        )
        vals = {}
        for line in text.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                vals[k] = safe_int(v.strip().split()[0])
        ram_total = round(vals.get("MemTotal", 0) / (1024 ** 2), 2)
        ram_available = round(vals.get("MemAvailable", 0) / (1024 ** 2), 2)
    except Exception:
        pass

    try:
        manufacturer = Path("/sys/class/dmi/id/sys_vendor").read_text().strip()
    except Exception:
        pass
    try:
        model = Path("/sys/class/dmi/id/product_name").read_text().strip()
    except Exception:
        pass

    smi = shutil.which("nvidia-smi")
    driver_ok = False
    if smi:
        code, out, _ = run_command([
            smi,
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader,nounits",
        ])
        if code == 0 and out:
            driver_ok = True
            for line in out.splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 2:
                    gpus.append(GPUInfo(
                        name=parts[0],
                        vendor="NVIDIA",
                        vram_gb=round(safe_int(parts[1]) / 1024, 2),
                        driver=parts[2] if len(parts) > 2 else "",
                        nvidia_smi=True,
                    ))

    # Secure Boot em Linux será aprofundado quando migrarmos para boot real.
    secure = Detection(
        value=None,
        source="Linux: não implementado na V0.2.1",
        confidence="baixa",
        status="pendente",
    )

    return HardwareInfo(
        os=f"{platform.system()} {platform.release()}",
        os_version=platform.version(),
        architecture=platform.machine(),
        hostname=platform.node(),
        manufacturer=manufacturer,
        model=model,
        cpu=cpu,
        physical_cores=physical,
        logical_threads=logical,
        cpu_features=detect_cpu_features_linux(),
        ram_total_gb=ram_total,
        ram_available_gb=ram_available,
        gpus=gpus,
        nvidia_detected=any(g.vendor == "NVIDIA" for g in gpus),
        nvidia_driver_ok=driver_ok,
        secure_boot=secure,
        bios_mode="não determinado",
        storage=detect_storage_linux(),
    )


# ---------------------------------------------------------------------------
# Motor llama.cpp
# ---------------------------------------------------------------------------

def first_existing(paths: List[Path]) -> str:
    for p in paths:
        if p.exists() and p.is_file():
            return str(p.resolve())
    return ""


def detect_engine(hw: HardwareInfo) -> EngineStatus:
    import plat  # fonte única de layout do motor por SO
    exe = plat.EXE_SUFFIX
    cuda_dir = plat.engine_dir(ROOT, "cuda")
    cpu_dir = plat.engine_dir(ROOT, "cpu")

    cuda_bench = first_existing([
        cuda_dir / f"llama-bench{exe}",
        cuda_dir / f"llama_bench{exe}",
    ])
    cpu_bench = first_existing([
        cpu_dir / f"llama-bench{exe}",
        cpu_dir / f"llama_bench{exe}",
    ])
    cuda_cli = first_existing([
        cuda_dir / f"llama-cli{exe}",
        cuda_dir / f"main{exe}",
    ])
    cpu_cli = first_existing([
        cpu_dir / f"llama-cli{exe}",
        cpu_dir / f"main{exe}",
    ])
    cuda_server = first_existing([cuda_dir / f"llama-server{exe}"])
    cpu_server = first_existing([cpu_dir / f"llama-server{exe}"])

    cuda_bundle = bool(cuda_bench or cuda_cli or cuda_server)
    cpu_bundle = bool(cpu_bench or cpu_cli or cpu_server)
    cuda_ready = bool(hw.nvidia_driver_ok and cuda_bundle)

    details: List[str] = []
    if hw.nvidia_driver_ok and not cuda_bundle:
        details.append(
            "Driver NVIDIA OK; build CUDA do llama.cpp ainda não está no pacote."
        )
    if not cpu_bundle:
        details.append(
            "Build CPU do llama.cpp ainda não está no pacote."
        )
    if cuda_ready:
        details.append(
            "NVIDIA + driver + pacote CUDA encontrados; pronto para benchmark real."
        )

    if cuda_ready:
        return EngineStatus(
            selected_backend="cuda",
            cuda_bundle_present=cuda_bundle,
            cpu_bundle_present=cpu_bundle,
            llama_cuda_ready=True,
            llama_bench=cuda_bench,
            llama_cli=cuda_cli,
            llama_server=cuda_server,
            details=details,
        )

    return EngineStatus(
        selected_backend="cpu",
        cuda_bundle_present=cuda_bundle,
        cpu_bundle_present=cpu_bundle,
        llama_cuda_ready=False,
        llama_bench=cpu_bench,
        llama_cli=cpu_cli,
        llama_server=cpu_server,
        details=details,
    )


# ---------------------------------------------------------------------------
# Recomendação
# ---------------------------------------------------------------------------

def best_gpu(hw: HardwareInfo) -> Optional[GPUInfo]:
    discrete = [g for g in hw.gpus if g.vendor in ("NVIDIA", "AMD")]
    return max(discrete, key=lambda g: g.vram_gb) if discrete else None


def recommend(hw: HardwareInfo, engine: EngineStatus) -> Recommendation:
    ram = hw.ram_total_gb
    notes: List[str] = []

    if ram < 6:
        profile, model_class, context = "SAFE", "1B–1.5B", 2048
    elif ram < 12:
        profile, model_class, context = "LIGHT", "3B–4B", 4096
    elif ram < 24:
        profile, model_class, context = "STANDARD", "7B–8B", 4096
    else:
        profile, model_class, context = "POWER", "12B–14B", 8192

    gpu = best_gpu(hw)
    vram = gpu.vram_gb if gpu else 0.0
    reserve = 0.75 if vram <= 6 else 1.25
    budget = max(0.0, round(vram - reserve, 2))

    if engine.llama_cuda_ready:
        backend = "cuda"
        offload = "partial_auto"
    else:
        backend = "cpu"
        offload = "disabled"

    # Começamos com núcleos físicos; V0.3 fará benchmark 4/6/8 threads.
    threads = (
        hw.physical_cores
        if hw.physical_cores > 0
        else max(1, hw.logical_threads - 2)
    )
    threads = max(1, min(threads, 12))

    initial_layers = 0  # só será calculado com GGUF real na V0.3

    if hw.cpu_features.avx2.value is True:
        notes.append("AVX2 confirmado com confiança alta.")
    elif hw.cpu_features.avx.value is True:
        notes.append("AVX confirmado; AVX2 não confirmado.")
    else:
        notes.append("AVX não confirmado; preferir build CPU conservadora.")

    if hw.secure_boot.value is True:
        notes.append(
            f"Secure Boot ativo ({hw.secure_boot.confidence})."
        )
    elif hw.secure_boot.value is False:
        notes.append(
            f"Secure Boot desativado ({hw.secure_boot.confidence})."
        )
    else:
        notes.append("Secure Boot indeterminado; não tomar decisão de boot com esse dado.")

    if hw.storage.bus_type:
        notes.append(
            f"AutoTune está rodando em unidade {hw.storage.drive} "
            f"com BusType={hw.storage.bus_type}."
        )

    return Recommendation(
        profile=profile,
        model_class=model_class,
        quantization="Q4_K_M",
        context_size=context,
        backend=backend,
        gpu_offload_policy=offload,
        initial_gpu_layers=initial_layers,
        gpu_vram_budget_gb=budget,
        cpu_threads=threads,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Machine ID compatível
# ---------------------------------------------------------------------------

def machine_id(hw: HardwareInfo) -> str:
    gpu_sig = "|".join(
        sorted(f"{g.vendor}:{g.name}:{g.vram_gb}" for g in hw.gpus)
    )
    raw = "|".join([
        hw.manufacturer,
        hw.model,
        hw.cpu,
        str(hw.ram_total_gb),
        gpu_sig,
        hw.architecture,
    ])
    return hashlib.sha256(
        raw.encode("utf-8", errors="replace")
    ).hexdigest()[:16]


# ---------------------------------------------------------------------------
# V0.7 Fase 1 — identidade estável e detecção defensiva (aditivo)
#
# machine_id() (v1) NÃO é alterado, para não invalidar perfis existentes
# (ex.: Avell b86b439ce669463f). Os itens abaixo são complementares:
#   - machine_fingerprint: sinais normalizados (diagnóstico + base do id v2);
#   - machine_id_v2: id estável a ruído de detecção (RAM/VRAM arredondadas);
#   - detection_confidence: avalia se os sinais-chave foram detectados;
#   - detect_safe / _minimal_hardware: nunca deixam o app sem HardwareInfo.
# ---------------------------------------------------------------------------

def _norm_str(s: Any) -> str:
    return " ".join(str(s or "").split()).strip()


def machine_fingerprint(hw: "HardwareInfo") -> Dict[str, Any]:
    gpus = []
    for g in getattr(hw, "gpus", []) or []:
        gpus.append({
            "vendor": _norm_str(g.vendor),
            "name": _norm_str(g.name),
            "vram_gb_int": int(round(g.vram_gb)) if getattr(g, "vram_gb", 0) else 0,
        })
    gpus.sort(key=lambda x: (x["vendor"], x["name"], x["vram_gb_int"]))
    return {
        "manufacturer": _norm_str(getattr(hw, "manufacturer", "")),
        "model": _norm_str(getattr(hw, "model", "")),
        "cpu": _norm_str(getattr(hw, "cpu", "")),
        "ram_total_gb_int": int(round(getattr(hw, "ram_total_gb", 0) or 0)),
        "architecture": _norm_str(getattr(hw, "architecture", "")),
        "gpus": gpus,
    }


def machine_id_v2(hw: "HardwareInfo") -> str:
    """ID estável a pequenas variações de detecção (RAM/VRAM arredondadas,
    strings normalizadas). Armazenado ao lado do v1; NÃO o substitui ainda."""
    fp = machine_fingerprint(hw)
    gpu_sig = "|".join(
        f"{g['vendor']}:{g['name']}:{g['vram_gb_int']}" for g in fp["gpus"]
    )
    raw = "|".join([
        fp["manufacturer"], fp["model"], fp["cpu"],
        str(fp["ram_total_gb_int"]), gpu_sig, fp["architecture"],
    ])
    return "v2_" + hashlib.sha256(
        raw.encode("utf-8", errors="replace")
    ).hexdigest()[:16]


def detection_confidence(hw: "HardwareInfo") -> Dict[str, Any]:
    """Sinaliza se os campos que compõem o machine_id foram detectados.

    Confiança baixa => o id pode divergir do id 'cheio' da mesma máquina caso
    um detector falhe; útil para evitar recalibração indevida (uso futuro)."""
    reasons = []
    if not _norm_str(getattr(hw, "manufacturer", "")):
        reasons.append("fabricante ausente")
    if not _norm_str(getattr(hw, "model", "")):
        reasons.append("modelo ausente")
    cpu = _norm_str(getattr(hw, "cpu", "")).lower()
    if not cpu or "não identificado" in cpu or "nao identificado" in cpu:
        reasons.append("cpu incerta")
    if not getattr(hw, "physical_cores", 0):
        reasons.append("núcleos ausentes")
    if not getattr(hw, "ram_total_gb", 0):
        reasons.append("ram ausente")
    if not reasons:
        level = "high"
    elif len(reasons) == 1:
        level = "medium"
    else:
        level = "low"
    return {"level": level, "reasons": reasons}


def _minimal_hardware() -> "HardwareInfo":
    """HardwareInfo mínimo, só com stdlib (sem PowerShell/WMI/nvidia-smi).
    Usado como último recurso para nunca deixar o app sem detecção."""
    def d():
        return Detection(value=None, source="fallback",
                         confidence="baixa", status="indisponível", detail="")
    ram_total = 0.0
    ram_avail = 0.0
    if os.name == "nt":
        try:
            class _MS(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            m = _MS()
            m.dwLength = ctypes.sizeof(_MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            ram_total = gb(m.ullTotalPhys)
            ram_avail = gb(m.ullAvailPhys)
        except Exception:
            pass
    storage = StorageInfo(
        current_path=str(Path.cwd()), drive="", filesystem="",
        volume_label="", disk_number=None, friendly_name="",
        bus_type="", media_type="", partition_style="",
        size_gb=0.0, is_boot=None, is_system=None,
        identification_confidence="baixa",
    )
    return HardwareInfo(
        os=f"{platform.system()} {platform.release()}",
        os_version=platform.version(),
        architecture=platform.machine(),
        hostname=platform.node(),
        manufacturer="",
        model="",
        cpu=platform.processor() or "Processador não identificado",
        physical_cores=0,
        logical_threads=os.cpu_count() or 1,
        cpu_features=CPUFeatures(sse3=d(), avx=d(), avx2=d(), avx512f=d()),
        ram_total_gb=ram_total,
        ram_available_gb=ram_avail,
        gpus=[],
        nvidia_detected=False,
        nvidia_driver_ok=False,
        secure_boot=None,
        bios_mode="não determinado",
        storage=storage,
    )


def detect_safe() -> "HardwareInfo":
    """Detecção que nunca lança exceção: escolhe o detector da plataforma e,
    se ele falhar, cai para _minimal_hardware() (CPU-only)."""
    try:
        if os.name == "nt":
            return detect_windows()
        return detect_linux()
    except Exception:
        try:
            return _minimal_hardware()
        except Exception:
            # Último anteparo: nunca propaga.
            return _minimal_hardware()


def continuity_check(machine: str) -> Dict[str, Any]:
    refs = [
        CONFIG_DIR / "autotune_v0_2_reference.json",
        CONFIG_DIR / "hardware_v0_1_reference.json",
    ]
    found = []
    matches = []
    for path in refs:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            old_id = str(data.get("machine_id") or "")
            if old_id:
                found.append({"file": path.name, "machine_id": old_id})
                matches.append(old_id == machine)
        except Exception:
            pass

    return {
        "references_found": found,
        "same_machine_as_all_references": bool(matches) and all(matches),
    }


# ---------------------------------------------------------------------------
# Relatório
# ---------------------------------------------------------------------------

def print_detection(label: str, d: Detection) -> None:
    print(
        f"{label:<18}: {bool_text(d.value):<4} | "
        f"confiança={d.confidence:<10} | fonte={d.source}"
    )
    if d.status not in ("ok", "consistente"):
        print(f"{'':18}  status={d.status} {d.detail}".rstrip())


def print_report(
    hw: HardwareInfo,
    engine: EngineStatus,
    bench: Optional[StorageBenchmark],
    rec: Recommendation,
    machine: str,
    continuity: Dict[str, Any],
) -> None:
    W = 88
    print("=" * W)
    print(f"{APP_NAME:^88}")
    print(f"{('AUTOTUNE V' + VERSION):^88}")
    print("=" * W)

    print("\nHARDWARE")
    print("-" * W)
    print(f"Máquina...........: {(hw.manufacturer + ' ' + hw.model).strip()}")
    print(f"CPU...............: {hw.cpu}")
    print(f"Núcleos/threads...: {hw.physical_cores}/{hw.logical_threads}")
    print(f"RAM total/livre...: {hw.ram_total_gb:.2f}/{hw.ram_available_gb:.2f} GB")
    print(f"Arquitetura.......: {hw.architecture}")
    print(f"Firmware..........: {hw.bios_mode}")

    print("\nCPU FEATURES + CONFIANÇA")
    print("-" * W)
    print_detection("SSE3", hw.cpu_features.sse3)
    print_detection("AVX", hw.cpu_features.avx)
    print_detection("AVX2", hw.cpu_features.avx2)
    print_detection("AVX512F", hw.cpu_features.avx512f)

    print("\nSECURE BOOT")
    print("-" * W)
    print_detection("Secure Boot", hw.secure_boot)

    print("\nGPU")
    print("-" * W)
    if not hw.gpus:
        print("Nenhuma GPU identificada.")
    for i, g in enumerate(hw.gpus):
        print(
            f"GPU {i}.............: {g.name} | {g.vendor} | "
            f"VRAM={g.vram_gb:.2f} GB | driver={g.driver or 'n/d'}"
        )
    print(f"NVIDIA driver.....: {'OK' if hw.nvidia_driver_ok else 'não confirmado'}")

    s = hw.storage
    print("\nARMAZENAMENTO DO AUTOTUNE")
    print("-" * W)
    print(f"Caminho...........: {s.current_path}")
    print(f"Unidade...........: {s.drive or 'n/d'}")
    print(f"Disco.............: {s.friendly_name or 'n/d'}")
    print(f"BusType...........: {s.bus_type or 'n/d'}")
    print(f"MediaType.........: {s.media_type or 'n/d'}")
    print(f"Filesystem........: {s.filesystem or 'n/d'}")
    print(f"Tamanho físico....: {s.size_gb:.2f} GB" if s.size_gb else "Tamanho físico....: n/d")
    print(f"Identificação.....: confiança={s.identification_confidence}")

    if bench:
        print("\nBENCHMARK DE ARMAZENAMENTO")
        print("-" * W)
        print(f"Tamanho do teste..: {bench.test_size_mb} MB x {len(bench.write_mb_s_samples)} passe(s)")
        print(f"Escrita amostras..: {bench.write_mb_s_samples}")
        print(f"Leitura amostras..: {bench.read_mb_s_samples}")
        print(f"Escrita mediana...: {bench.write_mb_s_median:.1f} MB/s")
        print(f"Leitura mediana...: {bench.read_mb_s_median:.1f} MB/s")
        print("Observação.........: leitura pode ser inflada por cache do Windows.")

    print("\nMOTOR")
    print("-" * W)
    print(f"Backend atual.....: {engine.selected_backend}")
    print(f"Build CUDA........: {'encontrada' if engine.cuda_bundle_present else 'ausente'}")
    print(f"Build CPU.........: {'encontrada' if engine.cpu_bundle_present else 'ausente'}")
    for d in engine.details:
        print(f"- {d}")

    print("\nRECOMENDAÇÃO")
    print("-" * W)
    print(f"Perfil............: {rec.profile}")
    print(f"Modelo............: {rec.model_class} {rec.quantization}")
    print(f"Contexto..........: {rec.context_size}")
    print(f"Backend...........: {rec.backend}")
    print(f"GPU offload.......: {rec.gpu_offload_policy}")
    print(f"VRAM budget.......: {rec.gpu_vram_budget_gb:.2f} GB")
    print(f"CPU threads.......: {rec.cpu_threads}")
    print(f"Machine ID........: {machine}")
    for note in rec.notes:
        print(f"- {note}")

    print("\nCONTINUIDADE")
    print("-" * W)
    refs = continuity.get("references_found", [])
    if refs:
        for ref in refs:
            print(f"{ref['file']}: {ref['machine_id']}")
        print(
            "Mesma máquina......: "
            + ("SIM" if continuity.get("same_machine_as_all_references") else "NÃO")
        )
    else:
        print("Nenhuma referência V0.1/V0.2 encontrada no pacote.")

    print("\n" + "=" * W)
    print("Arquivo principal: config/autotune_v0_2_1.json")
    print(f"Perfil: hardware_profiles/{machine}.json")
    print("=" * W)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} AutoTune V{VERSION}"
    )
    parser.add_argument(
        "--no-storage-benchmark",
        action="store_true",
        help="Não executa benchmark de armazenamento.",
    )
    parser.add_argument(
        "--storage-mb",
        type=int,
        default=256,
        help="Tamanho de cada passe do teste de armazenamento (64–1024 MB).",
    )
    parser.add_argument(
        "--storage-passes",
        type=int,
        default=2,
        help="Número de passes do benchmark (1–3).",
    )
    args = parser.parse_args()

    size_mb = max(64, min(args.storage_mb, 1024))
    passes = max(1, min(args.storage_passes, 3))

    system = platform.system().lower()
    if system == "windows":
        hw = detect_windows()
    elif system == "linux":
        hw = detect_linux()
    else:
        print(f"Sistema não suportado: {platform.system()}")
        return 2

    engine = detect_engine(hw)
    bench = None
    if not args.no_storage_benchmark:
        bench = benchmark_storage(size_mb=size_mb, passes=passes)

    rec = recommend(hw, engine)
    mid = machine_id(hw)
    continuity = continuity_check(mid)

    result = {
        "app": APP_NAME,
        "autotune_version": VERSION,
        "timestamp": now_iso(),
        "machine_id": mid,
        "hardware": asdict(hw),
        "storage_benchmark": asdict(bench) if bench else None,
        "engine": asdict(engine),
        "recommendation": asdict(rec),
        "continuity": continuity,
        "next_stage": {
            "target": "V0.3",
            "description": (
                "Adicionar llama.cpp portátil + GGUF real e medir CPU vs GPU offload."
            ),
        },
    }

    json_dump(CONFIG_DIR / "autotune_v0_2_1.json", result)
    json_dump(PROFILES_DIR / f"{mid}.json", result)

    history = PROFILES_DIR / f"{mid}_history.jsonl"
    with history.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "timestamp": result["timestamp"],
            "version": VERSION,
            "storage_benchmark": result["storage_benchmark"],
            "recommendation": result["recommendation"],
        }, ensure_ascii=False) + "\n")

    print_report(hw, engine, bench, rec, mid, continuity)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nCancelado pelo usuário.")
        raise SystemExit(130)
