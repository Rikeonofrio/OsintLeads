import json
import os
import re
import shutil
import subprocess
import urllib.parse
from typing import Dict, List, Optional

from lead_hunter_pkg import config
from lead_hunter_pkg.collectors.base import BaseCollector
from lead_hunter_pkg.models import Lead


class BNDESCollector(BaseCollector):
    def buscar(self, cnpj: str) -> list:
        raw = self._get(
            "https://dadosabertos.bndes.gov.br/api/3/action/datastore_search",
            params={
                "resource_id": "6a587f60-8087-4b03-95a5-3c7e013fd4d7",
                "filters": json.dumps({"cnpj_cliente": re.sub(r"\D", "", cnpj)}),
                "limit": 10,
            },
        )
        return raw.get("result", {}).get("records", []) if raw and raw.get("success") else []


class PNCPCollector(BaseCollector):
    def buscar(self, cnpj: str) -> list:
        raw = self._get(
            f"https://pncp.gov.br/api/pncp/v1/orgaos/{re.sub(r'\D','',cnpj)}/contratos",
            params={"pagina": 1, "tamanhoPagina": 10},
        )
        if isinstance(raw, list):
            return raw
        if isinstance(raw, dict):
            return raw.get("data", raw.get("content", []))
        return []


class IBGECollector(BaseCollector):
    def buscar_municipio(self, municipio: str, uf: str) -> dict:
        estados = self._get_list("https://servicodados.ibge.gov.br/api/v1/localidades/estados")
        if not estados:
            return {}
        uf_data = next((e for e in estados if e.get("sigla", "").upper() == uf.upper()), None)
        if not uf_data:
            return {}
        municipios = self._get_list(
            f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf_data['id']}/municipios"
        )
        if not municipios:
            return {}
        mun = next((m for m in municipios if municipio.lower() in m.get("nome", "").lower()), None)
        return {"nome": mun["nome"], "codigo": mun["id"], "uf": uf} if mun else {}


class HarvesterCollector(BaseCollector):
    def _bin(self) -> Optional[str]:
        for name in ["theHarvester", "theharvester"]:
            p = shutil.which(name)
            if p:
                return p
        for p in ["/usr/bin/theHarvester", "/usr/local/bin/theHarvester",
                  os.path.expanduser("~/.local/bin/theHarvester")]:
            if os.path.isfile(p):
                return p
        return None

    def disponivel(self) -> bool:
        return self._bin() is not None

    def coletar(self, dominio: str, fontes: str = "google,bing,duckduckgo") -> dict:
        r = {"emails": [], "hosts": [], "erro": ""}
        bin_path = self._bin()
        if not bin_path:
            r["erro"] = "theHarvester não encontrado"
            return r
        try:
            proc = subprocess.run(
                [bin_path, "-d", dominio, "-b", fontes, "-l", "100", "-f", "/tmp/lhbr_h"],
                capture_output=True, text=True, timeout=120,
            )
            saida = proc.stdout + proc.stderr
            emails = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", saida)
            r["emails"] = sorted(set(e.lower() for e in emails))
            if os.path.isfile("/tmp/lhbr_h.json"):
                jdata = json.load(open("/tmp/lhbr_h.json"))
                r["emails"] = sorted(set(r["emails"] + jdata.get("emails", [])))
                r["hosts"] = sorted(set(jdata.get("hosts", [])))
        except subprocess.TimeoutExpired:
            r["erro"] = "Timeout"
        except Exception as e:
            r["erro"] = str(e)
        return r


class ShodanCollector(BaseCollector):
    def disponivel(self) -> bool:
        return bool(config.SHODAN_API_KEY)

    def buscar(self, nome: str) -> dict:
        r = {"hosts": [], "portas": [], "cves": [], "erro": ""}
        if not config.SHODAN_API_KEY:
            r["erro"] = "SHODAN_API_KEY não configurada"
            return r
        try:
            import shodan as _shodan
            api = _shodan.Shodan(config.SHODAN_API_KEY)
            res = api.search(f'org:"{nome}"')
            for m in res.get("matches", [])[:10]:
                r["hosts"].append(m.get("ip_str", ""))
                r["portas"].append(m.get("port", ""))
                r["cves"].extend(m.get("vulns", {}).keys())
            r["cves"] = sorted(set(r["cves"]))
        except ImportError:
            r["erro"] = "pip install shodan"
        except Exception as e:
            r["erro"] = str(e)
        return r


class DorksGenerator:
    def gerar(self, lead: Lead) -> List[dict]:
        nome = lead.razao_social
        dominio = lead.dominio_provavel()

        def d(desc: str, query: str) -> dict:
            q = urllib.parse.quote_plus(query)
            return {
                "desc":   desc,
                "google": f"https://www.google.com/search?q={q}",
                "bing":   f"https://www.bing.com/search?q={q}",
            }

        dorks = [
            d("LinkedIn da empresa",        f'site:linkedin.com/company "{nome}"'),
            d("LinkedIn — sócios",          f'site:linkedin.com/in "{nome}"'),
            d("E-mails no site",            f'site:{dominio} email OR "fale conosco" OR "contato"'),
            d("PDFs públicos",              f'site:{dominio} filetype:pdf'),
            d("Planilhas expostas",         f'site:{dominio} filetype:xls OR filetype:xlsx OR filetype:csv'),
            d("Notícias",                   f'"{nome}" site:g1.globo.com OR site:uol.com.br OR site:folha.uol.com.br'),
            d("Reclame Aqui",               f'site:reclameaqui.com.br "{nome}"'),
            d("Licitações e contratos",     f'"{nome}" licitação OR contrato OR pregão'),
            d("Jusbrasil",                  f'site:jusbrasil.com.br "{nome}"'),
            d("Diário Oficial",             f'site:in.gov.br OR site:diariooficial.com.br "{nome}"'),
            d("Instagram",                  f'site:instagram.com "{nome}"'),
            d("Facebook",                   f'site:facebook.com "{nome}"'),
            d("Avaliações",                 f'"{nome}" avaliações OR reviews OR "google maps"'),
        ]

        for s in lead.socios[:3]:
            if s.nome:
                dorks += [
                    d(f"LinkedIn — {s.nome}",     f'site:linkedin.com/in "{s.nome}"'),
                    d(f"Processos — {s.nome}",    f'site:jusbrasil.com.br "{s.nome}"'),
                    d(f"Transparência — {s.nome}",f'site:portaldatransparencia.gov.br "{s.nome}"'),
                    d(f"Notícias — {s.nome}",     f'"{s.nome}" "{nome}"'),
                ]

        return dorks
