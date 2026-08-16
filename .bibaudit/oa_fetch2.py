#!/usr/bin/env python3
"""Second pass: Semantic Scholar / arXiv fallbacks for sources ACM and IEEE blocked."""
import json
import re
import ssl
import time
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path("/tmp/srcs")
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/126.0 Safari/537.36")

WANTED = {
    "jung2018rustbelt": "10.1145/3158154",
    "astrauskas2020unsafe": "10.1145/3428204",
    "jung2021safe": "10.1145/3418295",
    "jung2020stacked": "10.1145/3371109",
    "xu2021rustcve": "10.1145/3466642",
    "qin2020rust": "10.1145/3385412.3386036",
    "balasubramanian2017rust": "10.1145/3102980.3103006",
    "dean2013tail": "10.1145/2408776.2408794",
    "barroso2017microseconds": "10.1145/3015146",
    "li2014tales": "10.1145/2670979.2670988",
    "li2021ipc": "10.1145/3477113.3487275",
    "levy2017kernel": "10.1145/3124680.3124717",
    "zhang2022runtime": "10.1145/3551349.3559494",
    "bae2021rudra": "10.1145/3477132.3483570",
    "zheng2024security": "10.1145/3624738",
    "qin2024safety": "10.1109/TSE.2024.3380393",
    "zhang2026deadlock": "10.1007/s10515-026-00614-z",
    "rivera2021galeed": "10.1145/3485832.3485903",
    "kirth2022pkrusafe": "10.1145/3492321.3519582",
    "li2022crosslang": "10.1007/978-3-031-17143-7_33",
    "cai2026interop": "10.1145/3795532",
    "schuermann2023encapsulated": "10.1145/3625275.3625397",
    "emre2023aliasing": "10.1145/3586046",
    "sharma2024embedded": "10.1145/3658644.3690275",
    "fan2026android": "10.1145/3803437.3805227",
    "ardito2021verbosity": "10.7717/peerj-cs.406",
    "crichton2024learning": "10.1145/3649812",
    "michaelides2026ranlatency": "10.1145/3765613.3797453",
    "watson2025memorysafety": "10.1145/3708553",
    "enberg2019threadpercore": "10.1109/ANCS.2019.8901874",
    "huang2017predictability": "10.1145/3035918.3064016",
    "natella2016fault": "10.1145/2841425",
    "qazi2017pepc": "10.1145/3098822.3098848",
    "polese2023oran": "10.1109/COMST.2023.3239220",
    "cui2025perfbugs": "10.1109/ISSRE66568.2025.00045",
    "pereira2017energy": "10.1145/3136014.3136031",
    "mo2023rustshyper": "10.1016/j.sysarc.2023.102948",
    "xiao2024rpkt": "10.1007/978-981-96-2864-3_36",
    "liu2023l25gc": "10.1109/CloudNet59005.2023.10490024",
}


def req(url, accept="application/json"):
    return urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})


def download(url, dest):
    with urllib.request.urlopen(req(url, "*/*"), timeout=90,
                                context=ssl.create_default_context()) as r:
        data = r.read()
    if data[:4] != b"%PDF":
        return None
    dest.write_bytes(data)
    return len(data)


for key, doi in WANTED.items():
    dest = OUT / f"oa_{key}.pdf"
    if dest.exists():
        continue
    url = None
    try:
        u = ("https://api.semanticscholar.org/graph/v1/paper/DOI:"
             + urllib.parse.quote(doi) + "?fields=title,externalIds,openAccessPdf")
        with urllib.request.urlopen(req(u), timeout=40) as r:
            j = json.load(r)
        ax = (j.get("externalIds") or {}).get("ArXiv")
        if ax:
            url = f"https://arxiv.org/pdf/{ax}"
        elif j.get("openAccessPdf"):
            url = j["openAccessPdf"].get("url")
    except Exception as e:
        print(f"S2 fail {key}: {e}")
    if not url:
        print(f"NO SOURCE {key}")
        time.sleep(1.2)
        continue
    try:
        n = download(url, dest)
        print(f"{'OK      ' if n else 'NOT PDF '} {key}  {url}")
    except Exception as e:
        print(f"DL FAIL {key}: {e}  <- {url}")
    time.sleep(1.2)
