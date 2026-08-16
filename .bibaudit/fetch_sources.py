#!/usr/bin/env python3
"""Download primary sources for bibliography verification."""
import sys
import ssl
import urllib.request
from pathlib import Path

OUT = Path("/tmp/srcs")
OUT.mkdir(exist_ok=True)
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/126.0 Safari/537.36")

TARGETS = {
    # --- standards ---
    "rfc3393.txt": "https://www.rfc-editor.org/rfc/rfc3393.txt",
    "ts38401_v1750.pdf": "https://www.etsi.org/deliver/etsi_ts/138400_138499/138401/17.05.00_60/ts_138401v170500p.pdf",
    "ts38300_v1750.pdf": "https://www.etsi.org/deliver/etsi_ts/138300_138399/138300/17.05.00_60/ts_138300v170500p.pdf",
    "ts38463_v1700.pdf": "https://www.etsi.org/deliver/etsi_ts/138400_138499/138463/17.00.00_60/ts_138463v170000p.pdf",
    "ts22261_v1860.pdf": "https://www.etsi.org/deliver/etsi_ts/122200_122299/122261/18.06.00_60/ts_122261v180600p.pdf",
    "tr38913_v1800.pdf": "https://www.etsi.org/deliver/etsi_tr/138900_138999/138913/18.00.00_60/tr_138913v180000p.pdf",
    # --- policy / vendor ---
    "oncd2024.pdf": "https://bidenwhitehouse.archives.gov/wp-content/uploads/2024/02/Final-ONCD-Technical-Report.pdf",
    "cisa2023.pdf": "https://www.cisa.gov/sites/default/files/2023-12/The-Case-for-Memory-Safe-Roadmaps-508c.pdf",
    "android2022.html": "https://security.googleblog.com/2022/12/memory-safe-languages-in-android-13.html",
    "android2025.html": "https://blog.google/security/rust-in-android-move-fast-fix-things/",
    "eu_cra.html": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L_202402847",
    # --- WG21 ---
    "p3081r2.pdf": "https://isocpp.org/files/papers/P3081R2.pdf",
    "p3970r0.pdf": "https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p3970r0.pdf",
    "p3390r0.html": "https://safecpp.org/P3390R0.html",
    # --- USENIX ---
    "nsdi06_schroeder.pdf": "https://www.usenix.org/legacy/events/nsdi06/tech/full_papers/schroeder/schroeder.pdf",
    "nsdi20_firecracker.pdf": "https://www.usenix.org/system/files/nsdi20-paper-agache.pdf",
    "osdi20_redleaf.pdf": "https://www.usenix.org/system/files/osdi20-narayanan_vikram.pdf",
    "soups21_fulton.pdf": "https://www.usenix.org/system/files/soups2021-fulton.pdf",
    "atc24_rustforlinux.pdf": "https://www.usenix.org/system/files/atc24-li-hongyu.pdf",
    "atc25_converos.pdf": "https://www.usenix.org/system/files/atc25-tang.pdf",
    # --- LIPIcs ---
    "ecoop23_morello.pdf": "https://drops.dagstuhl.de/storage/00lipics/lipics-vol263-ecoop2023/LIPIcs.ECOOP.2023.39/LIPIcs.ECOOP.2023.39.pdf",
    "ecrts25_asyncrust.pdf": "https://drops.dagstuhl.de/storage/00lipics/lipics-vol335-ecrts2025/LIPIcs.ECRTS.2025.1/LIPIcs.ECRTS.2025.1.pdf",
    # --- misc primary ---
    "hdrhistogram.html": "https://hdrhistogram.github.io/HdrHistogram/",
    "lizard_pypi.json": "https://pypi.org/pypi/lizard/json",
    "alsoran_readme.md": "https://raw.githubusercontent.com/nplrkn/alsoran/main/README.md",
    "cidr25_oltp.pdf": "https://www.vldb.org/cidrdb/papers/2025/p17-zhou.pdf",
    "nostarch_rust.html": "https://nostarch.com/rust-programming-language-2nd-edition",
}


def get(name, url):
    dest = OUT / name
    if dest.exists() and dest.stat().st_size > 500:
        return f"cached  {name} ({dest.stat().st_size} B)"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": UA,
            "Accept": "*/*",
            "Accept-Language": "en-GB,en;q=0.9",
        })
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
            data = r.read()
        dest.write_bytes(data)
        return f"OK      {name} ({len(data)} B) {url}"
    except Exception as e:
        return f"FAIL    {name}: {e}  <- {url}"


if __name__ == "__main__":
    only = sys.argv[1:] or None
    for name, url in TARGETS.items():
        if only and not any(o in name for o in only):
            continue
        print(get(name, url), flush=True)
