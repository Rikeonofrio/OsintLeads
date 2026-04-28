import re
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Socio:
    nome:         str = ""
    qualificacao: str = ""
    cpf_cnpj:     str = ""
    data_entrada: str = ""


@dataclass
class Lead:
    cnpj:              str  = ""
    razao_social:      str  = ""
    nome_fantasia:     str  = ""
    situacao:          str  = ""
    abertura:          str  = ""
    natureza_juridica: str  = ""
    porte:             str  = ""
    capital_social:    Any  = 0
    cnae_codigo:       str  = ""
    cnae_principal:    str  = ""
    simples_optante:   bool = False
    mei:               bool = False
    email:      str = ""
    telefone:   str = ""
    logradouro: str = ""
    numero:     str = ""
    complemento:str = ""
    bairro:     str = ""
    municipio:  str = ""
    uf:         str = ""
    cep:        str = ""
    socios: List[Socio] = field(default_factory=list)
    _fonte: str = ""
    osint:  Dict = field(default_factory=dict)

    def endereco_completo(self) -> str:
        partes = [self.logradouro, self.numero, self.complemento,
                  self.bairro, self.municipio, self.uf]
        end = ", ".join(p for p in partes if p)
        return end + (f" — CEP {self.cep}" if self.cep else "")

    def dominio_provavel(self) -> str:
        stop = {"ltda","sa","s/a","me","eireli","epp","mei","comercio","servicos",
                "industria","brasil","do","da","de","dos","das","e"}
        base = self.nome_fantasia or self.razao_social
        palavras = [p for p in re.sub(r"[^a-z0-9\s]", "", base.lower()).split()
                    if p not in stop and len(p) > 2]
        return f"{palavras[0]}.com.br" if palavras else "empresa.com.br"

    def to_dict(self) -> dict:
        d = dict(self.__dict__)
        d["socios"] = [s.__dict__ for s in self.socios]
        return d
