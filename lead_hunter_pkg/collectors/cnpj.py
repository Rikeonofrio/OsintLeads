import re
import time
from typing import Optional

from lead_hunter_pkg import config
from lead_hunter_pkg.collectors.base import BaseCollector
from lead_hunter_pkg.models import Lead, Socio


class CNPJCollector(BaseCollector):
    SOURCES = {
        "brasilapi": "https://brasilapi.com.br/api/cnpj/v1/{cnpj}",
        "cnpja":     "https://open.cnpja.com/office/{cnpj}",
        "receitaws":  "https://receitaws.com.br/v1/cnpj/{cnpj}",
    }

    def buscar(self, cnpj: str) -> Optional[Lead]:
        c = re.sub(r"\D", "", cnpj)
        if len(c) != 14:
            return None
        for fonte, tpl in self.SOURCES.items():
            raw = self._get(tpl.format(cnpj=c))
            if raw and "message" not in raw and "erro" not in raw:
                raw["_fonte"] = fonte
                return self._normalizar(raw, fonte)
            time.sleep(0.4)
        return None

    def _normalizar(self, d: dict, fonte: str) -> Lead:
        if fonte == "brasilapi":
            return self._from_brasilapi(d)
        if fonte == "cnpja":
            return self._from_cnpja(d)
        return self._from_receitaws(d)

    def _from_brasilapi(self, d: dict) -> Lead:
        ddd = d.get("ddd_telefone_1", "")
        tel = d.get("telefone_1", "")
        telefone = f"({ddd}) {tel}".strip() if ddd and tel and ddd != tel else ddd or tel
        socios = [
            Socio(
                nome=s.get("nome_socio", ""),
                qualificacao=s.get("qualificacao_socio", ""),
                cpf_cnpj=s.get("cnpj_cpf_do_socio", ""),
                data_entrada=s.get("data_entrada_sociedade", ""),
            ) for s in (d.get("qsa") or [])
        ]
        return Lead(
            cnpj=d.get("cnpj", ""),
            razao_social=d.get("razao_social", ""),
            nome_fantasia=d.get("nome_fantasia", "") or d.get("razao_social", ""),
            situacao=d.get("descricao_situacao_cadastral", ""),
            abertura=d.get("data_inicio_atividade", ""),
            natureza_juridica=d.get("natureza_juridica", ""),
            porte=d.get("porte", ""),
            capital_social=d.get("capital_social", 0),
            cnae_codigo=str(d.get("cnae_fiscal", "")),
            cnae_principal=d.get("cnae_fiscal_descricao", ""),
            email=d.get("email", ""),
            telefone=telefone,
            logradouro=d.get("logradouro", ""),
            numero=d.get("numero", ""),
            complemento=d.get("complemento", ""),
            bairro=d.get("bairro", ""),
            municipio=d.get("municipio", ""),
            uf=d.get("uf", ""),
            cep=d.get("cep", ""),
            socios=socios,
            simples_optante=bool(d.get("opcao_pelo_simples")),
            mei=bool(d.get("opcao_pelo_mei")),
            _fonte="brasilapi",
        )

    def _from_cnpja(self, d: dict) -> Lead:
        company = d.get("company", {})
        address = d.get("address", {})
        phones = d.get("phones", [])
        emails = d.get("emails", [])
        activity = d.get("mainActivity", {})
        telefone = f"({phones[0].get('area','')}) {phones[0].get('number','')}".strip() if phones else ""
        email = emails[0].get("address", "") if emails else ""
        socios = [
            Socio(
                nome=m.get("person", {}).get("name", ""),
                qualificacao=m.get("role", {}).get("text", ""),
                cpf_cnpj=m.get("person", {}).get("taxId", ""),
                data_entrada=m.get("since", ""),
            ) for m in (company.get("members") or [])
        ]
        simples = company.get("simples") or {}
        simei = company.get("simei") or {}
        return Lead(
            cnpj=d.get("taxId", ""),
            razao_social=company.get("name", ""),
            nome_fantasia=d.get("alias", "") or company.get("name", ""),
            situacao=(d.get("status") or {}).get("text", ""),
            abertura=d.get("founded", ""),
            natureza_juridica=(company.get("nature") or {}).get("text", ""),
            porte=(company.get("size") or {}).get("text", ""),
            capital_social=company.get("equity", 0),
            cnae_codigo=str(activity.get("id", "")),
            cnae_principal=activity.get("text", ""),
            email=email,
            telefone=telefone,
            logradouro=address.get("street", ""),
            numero=address.get("number", ""),
            complemento=address.get("details", ""),
            bairro=address.get("district", ""),
            municipio=address.get("city", ""),
            uf=address.get("state", ""),
            cep=address.get("zip", ""),
            socios=socios,
            simples_optante=bool(simples.get("optant")),
            mei=bool(simei.get("optant")),
            _fonte="cnpja",
        )

    def _from_receitaws(self, d: dict) -> Lead:
        socios = [
            Socio(
                nome=s.get("nome", ""),
                qualificacao=s.get("qual", ""),
                cpf_cnpj=s.get("cpf_representante_legal", ""),
            ) for s in (d.get("qsa") or [])
        ]
        atv = (d.get("atividade_principal") or [{}])[0]
        return Lead(
            cnpj=d.get("cnpj", ""),
            razao_social=d.get("nome", ""),
            nome_fantasia=d.get("fantasia", "") or d.get("nome", ""),
            situacao=d.get("situacao", ""),
            abertura=d.get("abertura", ""),
            natureza_juridica=d.get("natureza_juridica", ""),
            porte=d.get("porte", ""),
            capital_social=d.get("capital_social", "0"),
            cnae_codigo=atv.get("code", ""),
            cnae_principal=atv.get("text", ""),
            email=d.get("email", ""),
            telefone=d.get("telefone", ""),
            logradouro=d.get("logradouro", ""),
            numero=d.get("numero", ""),
            complemento=d.get("complemento", ""),
            bairro=d.get("bairro", ""),
            municipio=d.get("municipio", ""),
            uf=d.get("uf", ""),
            cep=d.get("cep", ""),
            socios=socios,
            simples_optante=bool((d.get("simples") or {}).get("optante")),
            mei=bool((d.get("mei") or {}).get("optante")),
            _fonte="receitaws",
        )
