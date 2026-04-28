from typing import List, Optional

from lead_hunter_pkg.models import Lead


class LeadSession:
    def __init__(self):
        self._leads: List[Lead] = []

    def adicionar(self, lead: Lead):
        if any(l.cnpj == lead.cnpj for l in self._leads):
            self._leads = [lead if l.cnpj == lead.cnpj else l for l in self._leads]
        else:
            self._leads.append(lead)

    def todos(self) -> List[Lead]:
        return list(self._leads)

    def limpar(self):
        self._leads = []

    def total(self) -> int:
        return len(self._leads)

    def filtrar(
        self,
        uf: Optional[str] = None,
        municipio: Optional[str] = None,
        cnae: Optional[str] = None,
        situacao: Optional[str] = None,
        com_email: bool = False,
        com_telefone: bool = False,
        sem_sancoes: bool = False,
    ) -> List[Lead]:
        r = self._leads
        if uf:
            r = [l for l in r if l.uf.upper() == uf.upper()]
        if municipio:
            r = [l for l in r if municipio.lower() in l.municipio.lower()]
        if cnae:
            r = [l for l in r if cnae in l.cnae_codigo]
        if situacao:
            r = [l for l in r if situacao.lower() in l.situacao.lower()]
        if com_email:
            r = [l for l in r if l.email.strip()]
        if com_telefone:
            r = [l for l in r if l.telefone.strip()]
        if sem_sancoes:
            r = [l for l in r if not l.osint.get("transparencia", {}).get("tem_sancoes")]
        return r
