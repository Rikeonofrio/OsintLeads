import re
from typing import Optional

from lead_hunter_pkg import config
from lead_hunter_pkg.collectors.base import BaseCollector
from lead_hunter_pkg.models import Lead


class TransparenciaCollector(BaseCollector):
    BASE = "https://api.portaldatransparencia.gov.br/api-de-dados"

    def _h(self) -> dict:
        h = dict(self.HEADERS)
        if config.TRANSPARENCIA_API_KEY:
            h["chave-api-dados"] = config.TRANSPARENCIA_API_KEY
        return h

    def _q(self, path: str, params: dict = None) -> list:
        return self._get_list(f"{self.BASE}/{path}", params, self._h()) or []

    def sancoes_ceis(self, cnpj: str)  -> list: return self._q("ceis",    {"cnpjSancionado": re.sub(r"\D","",cnpj), "pagina": 1})
    def sancoes_cnep(self, cnpj: str)  -> list: return self._q("cnep",    {"cnpjSancionado": re.sub(r"\D","",cnpj), "pagina": 1})
    def sancoes_cepim(self, cnpj: str) -> list: return self._q("cepim",   {"cnpj":           re.sub(r"\D","",cnpj), "pagina": 1})
    def contratos(self, cnpj: str)     -> list: return self._q("contratos",  {"cnpjFornecedor": re.sub(r"\D","",cnpj), "pagina": 1})
    def licitacoes(self, cnpj: str)    -> list: return self._q("licitacoes", {"cnpj":           re.sub(r"\D","",cnpj), "pagina": 1})
    def convenios(self, cnpj: str)     -> list: return self._q("convenios",  {"cnpjConvenente": re.sub(r"\D","",cnpj), "pagina": 1})
    def obras(self, cnpj: str)         -> list: return self._q("obras",      {"cnpj":           re.sub(r"\D","",cnpj), "pagina": 1})
    def gastos_cartao(self, cnpj: str) -> list: return self._q("cartoes",    {"cnpjEstabelecimento": re.sub(r"\D","",cnpj), "pagina": 1})

    def buscar_servidor(self, nome: str) -> list:
        return self._q("servidores", {"nome": nome, "pagina": 1})

    def coletar_tudo(self, lead: Lead) -> dict:
        c = lead.cnpj
        ceis = self.sancoes_ceis(c)
        cnep = self.sancoes_cnep(c)
        cepim = self.sancoes_cepim(c)
        contratos = self.contratos(c)
        licit = self.licitacoes(c)
        convs = self.convenios(c)
        obras = self.obras(c)
        cartao = self.gastos_cartao(c)
        servidores = {}
        for s in lead.socios[:3]:
            if s.nome:
                r = self.buscar_servidor(s.nome)
                if r:
                    servidores[s.nome] = r[:3]
        return {
            "sancoes_ceis":      ceis,
            "sancoes_cnep":      cnep,
            "sancoes_cepim":     cepim,
            "contratos":         contratos[:5],
            "licitacoes":        licit[:5],
            "convenios":         convs[:5],
            "obras":             obras[:5],
            "gastos_cartao":     cartao[:5],
            "servidores_socios": servidores,
            "tem_sancoes":       bool(ceis or cnep or cepim),
            "total_contratos":   len(contratos),
            "total_licitacoes":  len(licit),
            "total_convenios":   len(convs),
            "total_obras":       len(obras),
            "total_cartao":      len(cartao),
        }
