import re
import time
from typing import Optional

import requests

from lead_hunter_pkg import config
from lead_hunter_pkg.collectors.base import BaseCollector
from lead_hunter_pkg.models import Lead


class DataJudCollector(BaseCollector):
    BASE = "https://api-publica.datajud.cnj.jus.br"
    INDICES = [
        "api_publica_tjsp", "api_publica_tjrj", "api_publica_tjmg",
        "api_publica_tjrs", "api_publica_tjpr", "api_publica_tjsc",
        "api_publica_trt2", "api_publica_trf3",
    ]

    def _buscar(self, indice: str, query: str) -> list:
        try:
            r = requests.post(
                f"{self.BASE}/{indice}/_search",
                json={"query": {"match": {"partes.nome": query}}, "size": 5},
                headers=self.HEADERS, timeout=10,
            )
            if r.status_code == 200:
                return [h.get("_source", {}) for h in r.json().get("hits", {}).get("hits", [])]
        except Exception:
            pass
        return []

    def buscar_processos(self, lead: Lead) -> dict:
        processos = []
        for idx in self.INDICES[:4]:
            for p in self._buscar(idx, lead.razao_social):
                p["_tribunal"] = idx.replace("api_publica_", "").upper()
                processos.append(p)
            time.sleep(0.2)

        socios_proc = {}
        for s in lead.socios[:2]:
            if s.nome:
                lista = self._buscar("api_publica_trt2", s.nome) + self._buscar("api_publica_tjsp", s.nome)
                if lista:
                    socios_proc[s.nome] = lista[:3]

        trab = [p for p in processos if "trabalhista" in str(p.get("classe", {}).get("nome", "")).lower()]
        fiscais = [p for p in processos if any(t in str(p.get("classe", {}).get("nome", "")).lower() for t in ["execução fiscal", "tributar"])]
        civeis = [p for p in processos if p not in trab + fiscais]

        return {
            "total": len(processos),
            "trabalhistas": trab[:5],
            "fiscais": fiscais[:5],
            "civeis": civeis[:5],
            "socios": socios_proc,
            "tem_trabalhista": bool(trab),
            "tem_fiscal": bool(fiscais),
        }
