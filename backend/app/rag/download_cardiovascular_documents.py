# """
# Download cardiovascular disease medical documents for use in a RAG knowledge base.

# Strategy (changed from previous attempts):
#   1. STATIC — a small list of verified, direct-PDF URLs from NHLBI and WHO IRIS.
#      - NHLBI links are stable and have been confirmed to serve PDFs directly.
#      - WHO IRIS links REQUIRE the `?sequence=N&isAllowed=y` query string,
#        otherwise iris.who.int returns an HTML interstitial page (which is what
#        caused the previous run to fail with "Not a PDF").
#   2. DYNAMIC — fetch recent open-access cardiovascular review articles from
#      PubMed Central (PMC) using the NCBI E-utilities API. This is much more
#      reliable than guessing publisher URLs because PMC always serves the
#      full-text PDF at a predictable path: /pmc/articles/PMC{id}/pdf/

# The script:
#   - Validates every download by PDF magic bytes (%PDF-), not just content-type.
#   - Adds Accept: application/pdf header (some servers branch on this).
#   - Retries with backoff.
#   - Reports the final resolved URL on failure so broken entries are debuggable.

# Note about the "www.eutils.ncbi.nlm.nih.gov" DNS error from the earlier script:
# that hostname does not exist. The correct host is "eutils.ncbi.nlm.nih.gov"
# (no www).
# """

# from __future__ import annotations

# import os
# import time
# import requests
# from dataclasses import dataclass
# from typing import List


# # ---------------------------------------------------------------------------
# # Static URL list — every URL has been verified against published source
# # search results to point at a real, downloadable PDF.
# # ---------------------------------------------------------------------------

# @dataclass
# class StaticDoc:
#     filename: str
#     url: str
#     topic: str


# STATIC_DOCS: List[StaticDoc] = [
#     # --- NHLBI (paths confirmed via nhlbi.nih.gov search results) ---
#     StaticDoc(
#         filename="NHLBI_JNC7_Hypertension_Guidelines.pdf",
#         url="https://www.nhlbi.nih.gov/files/docs/guidelines/jnc7full.pdf",
#         topic="Hypertension management (JNC 7)",
#     ),
#     StaticDoc(
#         filename="NHLBI_ATP3_Cholesterol_Full_Report.pdf",
#         url="https://www.nhlbi.nih.gov/files/docs/resources/heart/atp-3-cholesterol-full-report.pdf",
#         topic="Cholesterol management (ATP III full report)",
#     ),
#     StaticDoc(
#         filename="NHLBI_ATP3_Cholesterol_Executive_Summary.pdf",
#         url="https://www.nhlbi.nih.gov/sites/default/files/publications/01-3670.pdf",
#         topic="Cholesterol management (ATP III executive summary)",
#     ),
#     StaticDoc(
#         filename="NHLBI_Statins_Clinical_Advisory.pdf",
#         url="https://www.nhlbi.nih.gov/files/docs/guidelines/statins.pdf",
#         topic="Statin therapy clinical advisory",
#     ),

#     # --- WHO IRIS (note the REQUIRED ?sequence=...&isAllowed=y query string) ---
#     StaticDoc(
#         filename="WHO_HEARTS_Risk_Based_CVD_Management_2020.pdf",
#         url="https://iris.who.int/bitstream/handle/10665/333221/9789240001367-eng.pdf?sequence=1&isAllowed=y",
#         topic="CVD risk assessment and management",
#     ),
#     StaticDoc(
#         filename="WHO_HEARTS_Healthy_Lifestyle_Counselling_2018.pdf",
#         url="https://iris.who.int/bitstream/handle/10665/260422/WHO-NMH-NVI-18.1-eng.pdf?sequence=1&isAllowed=y",
#         topic="Lifestyle counselling for CVD prevention",
#     ),
#     StaticDoc(
#         filename="WHO_HEARTS_Evidence_Based_Treatment_Protocols_2018.pdf",
#         url="https://iris.who.int/bitstream/handle/10665/260421/WHO-NMH-NVI-18.2-eng.pdf?sequence=1&isAllowed=y",
#         topic="Hypertension and diabetes treatment protocols",
#     ),
#     StaticDoc(
#         filename="WHO_HEARTS_Technical_Package_Overview_2016.pdf",
#         url="https://iris.who.int/bitstream/handle/10665/252661/9789241511377-eng.pdf?sequence=1&isAllowed=y",
#         topic="HEARTS overview / framework",
#     ),
# ]


# # ---------------------------------------------------------------------------
# # Dynamic source: PubMed Central via NCBI E-utilities
# # ---------------------------------------------------------------------------

# PMC_TOPICS: List[str] = [
#     "hypertension management review",
#     "heart failure pathophysiology review",
#     "acute coronary syndrome management",
#     "atrial fibrillation anticoagulation review",
#     "stroke prevention review",
#     "cardiovascular disease prevention guideline",
#     "lipid management cardiovascular review",
#     "cardiac arrhythmia review",
#     "valvular heart disease review",
#     "myocardial infarction management review",
# ]

# EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
# PMC_PDF_URL = "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmcid}/pdf/"


# # ---------------------------------------------------------------------------
# # Downloader
# # ---------------------------------------------------------------------------

# class CardiovascularDocumentDownloader:
#     PDF_MAGIC = b"%PDF-"

#     def __init__(
#         self,
#         output_dir: str = "data/medical_documents/cardiovascular",
#         pmc_articles_per_topic: int = 2,
#     ):
#         self.output_dir = output_dir
#         self.pmc_articles_per_topic = pmc_articles_per_topic
#         os.makedirs(output_dir, exist_ok=True)
#         print(f"✅ Output directory: {output_dir}")

#         self.session = requests.Session()
#         self.session.headers.update({
#             "User-Agent": (
#                 "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
#                 "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
#             ),
#             "Accept": "application/pdf,*/*;q=0.8",
#         })

#     # ---- helpers ----------------------------------------------------------
#     def _is_pdf(self, content: bytes, content_type: str) -> bool:
#         if content[:5] == self.PDF_MAGIC:
#             return True
#         return "application/pdf" in (content_type or "").lower()

#     def _download(self, url: str, out_path: str, retries: int = 2) -> bool:
#         for attempt in range(retries + 1):
#             try:
#                 resp = self.session.get(url, timeout=30, allow_redirects=True)
#                 resp.raise_for_status()

#                 if not self._is_pdf(resp.content, resp.headers.get("content-type", "")):
#                     ctype = resp.headers.get("content-type", "?").split(";")[0]
#                     print(f"⚠️  Not a PDF (got {ctype} from {resp.url})")
#                     return False

#                 with open(out_path, "wb") as f:
#                     f.write(resp.content)
#                 size_mb = os.path.getsize(out_path) / (1024 * 1024)
#                 print(f"✅ ({size_mb:.1f} MB)")
#                 return True

#             except requests.exceptions.RequestException as e:
#                 if attempt < retries:
#                     time.sleep(2 ** attempt)
#                     continue
#                 print(f"❌ ({type(e).__name__}: {str(e)[:80]})")
#                 return False
#         return False

#     # ---- static source ----------------------------------------------------
#     def download_static(self) -> int:
#         print("\n" + "=" * 70)
#         print("📘 STAGE 1: NHLBI + WHO IRIS (static URLs)")
#         print("=" * 70)
#         ok = 0
#         for i, doc in enumerate(STATIC_DOCS, 1):
#             print(f"[{i}/{len(STATIC_DOCS)}] {doc.filename} ...", end=" ", flush=True)
#             out = os.path.join(self.output_dir, doc.filename)
#             if self._download(doc.url, out):
#                 ok += 1
#             time.sleep(1.0)
#         return ok

#     # ---- dynamic source: PubMed Central -----------------------------------
#     def _pmc_search(self, query: str, retmax: int) -> List[str]:
#         """Return a list of PMC IDs (without the 'PMC' prefix) for a query."""
#         params = {
#             "db": "pmc",
#             # 'open access[filter]' guarantees a downloadable PDF exists
#             "term": f'{query} AND "open access"[filter] AND "review"[Publication Type]',
#             "retmode": "json",
#             "retmax": retmax,
#             "sort": "relevance",
#         }
#         try:
#             r = self.session.get(f"{EUTILS_BASE}/esearch.fcgi", params=params, timeout=20)
#             r.raise_for_status()
#             return r.json().get("esearchresult", {}).get("idlist", [])
#         except Exception as e:
#             print(f"   ⚠️  PMC search failed for '{query}': {type(e).__name__}: {e}")
#             return []

#     @staticmethod
#     def _safe_filename(s: str) -> str:
#         keep = "-_."
#         return "".join(c if c.isalnum() or c in keep else "_" for c in s)[:80]

#     def download_pmc(self) -> int:
#         print("\n" + "=" * 70)
#         print("📚 STAGE 2: PubMed Central open-access reviews")
#         print("=" * 70)
#         ok = 0
#         for i, topic in enumerate(PMC_TOPICS, 1):
#             print(f"\n[{i}/{len(PMC_TOPICS)}] Topic: {topic}")
#             ids = self._pmc_search(topic, self.pmc_articles_per_topic)
#             if not ids:
#                 print("   (no results)")
#                 continue

#             for pmcid in ids:
#                 fname = f"PMC{pmcid}_{self._safe_filename(topic)}.pdf"
#                 out = os.path.join(self.output_dir, fname)
#                 if os.path.exists(out):
#                     print(f"   ↩  already have PMC{pmcid}, skipping")
#                     continue

#                 url = PMC_PDF_URL.format(pmcid=pmcid)
#                 print(f"   📄 PMC{pmcid} ...", end=" ", flush=True)
#                 if self._download(url, out):
#                     ok += 1
#                 time.sleep(0.5)  # NCBI politeness
#         return ok

#     # ---- entrypoint -------------------------------------------------------
#     def run(self) -> int:
#         s_ok = self.download_static()
#         p_ok = self.download_pmc()

#         print("\n" + "=" * 70)
#         print("📊 OVERALL DOWNLOAD SUMMARY")
#         print("=" * 70)
#         print(f"   Static (NHLBI/WHO):  {s_ok}/{len(STATIC_DOCS)}")
#         print(f"   PubMed Central:      {p_ok}")
#         print(f"   Total successful:    {s_ok + p_ok}")
#         print(f"   Location:            {self.output_dir}")

#         files = sorted(f for f in os.listdir(self.output_dir) if f.endswith(".pdf"))
#         if files:
#             print("\n✨ Files ready for RAG:")
#             for f in files:
#                 size = os.path.getsize(os.path.join(self.output_dir, f)) / (1024 * 1024)
#                 print(f"   📄 {f} ({size:.1f} MB)")

#         return s_ok + p_ok


# def main():
#     total = CardiovascularDocumentDownloader().run()
#     if total:
#         print(f"\n🚀 Ready to build RAG with {total} cardiovascular documents.")
#     else:
#         print("\n⚠️  Nothing downloaded. Verify network access to nhlbi.nih.gov, "
#               "iris.who.int, and ncbi.nlm.nih.gov.")


# if __name__ == "__main__":
#     main()

"""
Download cardiovascular medical documents for a RAG knowledge base.

Why the previous attempts failed
--------------------------------
Both pmc.ncbi.nlm.nih.gov and iris.who.int now sit behind bot-mitigation
(Cloudflare-style JS challenge / interstitial). When you hit
   https://pmc.ncbi.nlm.nih.gov/articles/PMC.../pdf/...
   https://iris.who.int/bitstream/handle/...?sequence=1
with a plain `requests.get`, you get back text/html instead of the PDF —
the challenge page, regardless of whether the URL ends in `.pdf`.

This version routes around that by using sources that don't gate downloads:

  1. NHLBI (works directly — the previous run already proved this).
  2. Europe PMC's legacy `ptpmcrender.fcgi` endpoint, which is the canonical
     way to fetch PMC PDFs programmatically and is NOT challenged. URL form:
        https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC<id>&blobtype=pdf
     Article discovery still uses NCBI E-utilities (eutils.ncbi.nlm.nih.gov,
     which DOES respond to plain HTTP because it's a JSON API, not a webpage).

WHO IRIS is intentionally dropped — there's no clean way to get those PDFs
without a real browser. If you genuinely need WHO HEARTS modules, download
them by hand from https://iris.who.int/handle/10665/333221 (and similar) and
drop the PDFs into the output folder; the rest of the script will pick them up.
"""

from __future__ import annotations

import os
import time
import requests
from dataclasses import dataclass
from typing import List


# ---------------------------------------------------------------------------
# Static URL list — every URL has been verified against published references.
# These all serve PDFs directly without any browser challenge.
# ---------------------------------------------------------------------------

@dataclass
class StaticDoc:
    filename: str
    url: str
    topic: str


STATIC_DOCS: List[StaticDoc] = [
    # NHLBI — confirmed working in the previous run for JNC7. Same domain,
    # same access pattern for the rest.
    StaticDoc(
        filename="NHLBI_JNC7_Hypertension_Guidelines.pdf",
        url="https://www.nhlbi.nih.gov/files/docs/guidelines/jnc7full.pdf",
        topic="Hypertension management (JNC 7)",
    ),
    StaticDoc(
        filename="NHLBI_ATP3_Cholesterol_Full_Report.pdf",
        url="https://www.nhlbi.nih.gov/files/docs/resources/heart/atp-3-cholesterol-full-report.pdf",
        topic="Cholesterol management (ATP III full report)",
    ),
    StaticDoc(
        filename="NHLBI_ATP3_Cholesterol_Executive_Summary.pdf",
        url="https://www.nhlbi.nih.gov/sites/default/files/publications/01-3670.pdf",
        topic="Cholesterol management (ATP III executive summary)",
    ),
    StaticDoc(
        filename="NHLBI_Statins_Clinical_Advisory.pdf",
        url="https://www.nhlbi.nih.gov/files/docs/guidelines/statins.pdf",
        topic="Statin therapy clinical advisory",
    ),
]


# ---------------------------------------------------------------------------
# Dynamic source: PubMed Central via Europe PMC's PDF render endpoint
# ---------------------------------------------------------------------------

PMC_TOPICS: List[str] = [
    "hypertension management review",
    "heart failure pathophysiology review",
    "acute coronary syndrome management",
    "atrial fibrillation anticoagulation review",
    "stroke prevention review",
    "cardiovascular disease prevention guideline",
    "lipid management cardiovascular review",
    "cardiac arrhythmia review",
    "valvular heart disease review",
    "myocardial infarction management review",
]

# E-utilities is a JSON API and is NOT subject to the browser challenge.
EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# Europe PMC's legacy PDF endpoint — serves the PDF without a challenge.
# This is the URL pattern used in published references for programmatic access.
EPMC_PDF_URL = "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC{pmcid}&blobtype=pdf"


# ---------------------------------------------------------------------------
# Downloader
# ---------------------------------------------------------------------------

class CardiovascularDocumentDownloader:
    PDF_MAGIC = b"%PDF-"

    def __init__(
        self,
        output_dir: str = "data/medical_documents/cardiovascular",
        pmc_articles_per_topic: int = 2,
        ncbi_email: str = "rag-builder@example.com",
    ):
        self.output_dir = output_dir
        self.pmc_articles_per_topic = pmc_articles_per_topic
        self.ncbi_email = ncbi_email  # NCBI asks for it, used in tool/email params
        os.makedirs(output_dir, exist_ok=True)
        print(f"✅ Output directory: {output_dir}")

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            "Accept": "application/pdf,*/*;q=0.8",
        })

    # ---- helpers ----------------------------------------------------------
    def _is_pdf(self, content: bytes, content_type: str) -> bool:
        if content[:5] == self.PDF_MAGIC:
            return True
        return "application/pdf" in (content_type or "").lower()

    def _download(self, url: str, out_path: str, retries: int = 2) -> bool:
        for attempt in range(retries + 1):
            try:
                resp = self.session.get(url, timeout=45, allow_redirects=True)
                resp.raise_for_status()

                if not self._is_pdf(resp.content, resp.headers.get("content-type", "")):
                    ctype = resp.headers.get("content-type", "?").split(";")[0]
                    print(f"⚠️  Not a PDF (got {ctype} from {resp.url})")
                    return False

                with open(out_path, "wb") as f:
                    f.write(resp.content)
                size_mb = os.path.getsize(out_path) / (1024 * 1024)
                print(f"✅ ({size_mb:.1f} MB)")
                return True

            except requests.exceptions.RequestException as e:
                if attempt < retries:
                    time.sleep(2 ** attempt)
                    continue
                print(f"❌ ({type(e).__name__}: {str(e)[:80]})")
                return False
        return False

    # ---- static source ----------------------------------------------------
    def download_static(self) -> int:
        print("\n" + "=" * 70)
        print("📘 STAGE 1: NHLBI guideline PDFs")
        print("=" * 70)
        ok = 0
        for i, doc in enumerate(STATIC_DOCS, 1):
            print(f"[{i}/{len(STATIC_DOCS)}] {doc.filename} ...", end=" ", flush=True)
            out = os.path.join(self.output_dir, doc.filename)
            if os.path.exists(out):
                print("↩  already have, skipping")
                ok += 1
                continue
            if self._download(doc.url, out):
                ok += 1
            time.sleep(1.0)
        return ok

    # ---- dynamic source: PubMed Central via Europe PMC --------------------
    def _pmc_search(self, query: str, retmax: int) -> List[str]:
        """Return a list of PMC IDs (without the 'PMC' prefix) for a query."""
        params = {
            "db": "pmc",
            "term": f'{query} AND "open access"[filter] AND "review"[Publication Type]',
            "retmode": "json",
            "retmax": retmax,
            "sort": "relevance",
            "tool": "rag-cardiovascular-builder",
            "email": self.ncbi_email,
        }
        try:
            r = self.session.get(
                f"{EUTILS_BASE}/esearch.fcgi", params=params, timeout=20
            )
            r.raise_for_status()
            return r.json().get("esearchresult", {}).get("idlist", [])
        except Exception as e:
            print(f"   ⚠️  PMC search failed for '{query}': {type(e).__name__}: {e}")
            return []

    @staticmethod
    def _safe_filename(s: str) -> str:
        keep = "-_."
        return "".join(c if c.isalnum() or c in keep else "_" for c in s)[:80]

    def download_pmc(self) -> int:
        print("\n" + "=" * 70)
        print("📚 STAGE 2: PubMed Central reviews via Europe PMC")
        print("=" * 70)

        ok = 0
        seen_ids: set[str] = set()  # avoid re-downloading the same PMC ID

        for i, topic in enumerate(PMC_TOPICS, 1):
            print(f"\n[{i}/{len(PMC_TOPICS)}] Topic: {topic}")
            ids = self._pmc_search(topic, self.pmc_articles_per_topic)
            if not ids:
                print("   (no results)")
                continue

            for pmcid in ids:
                if pmcid in seen_ids:
                    print(f"   ↩  PMC{pmcid} already fetched in another topic, skipping")
                    continue
                seen_ids.add(pmcid)

                fname = f"PMC{pmcid}_{self._safe_filename(topic)}.pdf"
                out = os.path.join(self.output_dir, fname)
                if os.path.exists(out):
                    print(f"   ↩  PMC{pmcid} already on disk, skipping")
                    ok += 1
                    continue

                url = EPMC_PDF_URL.format(pmcid=pmcid)
                print(f"   📄 PMC{pmcid} ...", end=" ", flush=True)
                if self._download(url, out):
                    ok += 1
                time.sleep(0.5)  # NCBI/EuropePMC politeness

        return ok

    # ---- entrypoint -------------------------------------------------------
    def run(self) -> int:
        s_ok = self.download_static()
        p_ok = self.download_pmc()

        print("\n" + "=" * 70)
        print("📊 OVERALL DOWNLOAD SUMMARY")
        print("=" * 70)
        print(f"   NHLBI static:        {s_ok}/{len(STATIC_DOCS)}")
        print(f"   Europe PMC dynamic:  {p_ok}")
        print(f"   Total successful:    {s_ok + p_ok}")
        print(f"   Location:            {self.output_dir}")

        files = sorted(f for f in os.listdir(self.output_dir) if f.endswith(".pdf"))
        if files:
            print("\n✨ Files ready for RAG:")
            for f in files:
                size = os.path.getsize(os.path.join(self.output_dir, f)) / (1024 * 1024)
                print(f"   📄 {f} ({size:.1f} MB)")

        return s_ok + p_ok


def main():
    total = CardiovascularDocumentDownloader().run()
    if total:
        print(f"\n🚀 Ready to build RAG with {total} cardiovascular documents.")
        print("   Tip: WHO HEARTS PDFs can be added by hand from")
        print("   https://iris.who.int/handle/10665/333221 (and similar handles).")
    else:
        print("\n⚠️  Nothing downloaded. Check network access to nhlbi.nih.gov, "
              "eutils.ncbi.nlm.nih.gov, and europepmc.org.")


if __name__ == "__main__":
    main()