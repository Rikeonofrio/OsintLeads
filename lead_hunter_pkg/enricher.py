from lead_hunter_pkg import config
from lead_hunter_pkg.collectors import (
    TransparenciaCollector,
    DataJudCollector,
    WhoisCollector,
    SiteAnalyzer,
    BNDESCollector,
    PNCPCollector,
    IBGECollector,
    HarvesterCollector,
    ShodanCollector,
    DorksGenerator,
)
from lead_hunter_pkg.models import Lead
from lead_hunter_pkg.config import mapear_cnae


class Enricher:
    def __init__(self):
        self.transparencia = TransparenciaCollector()
        self.datajud = DataJudCollector()
        self.whois = WhoisCollector()
        self.site = SiteAnalyzer()
        self.bndes = BNDESCollector()
        self.pncp = PNCPCollector()
        self.ibge = IBGECollector()
        self.harvester = HarvesterCollector()
        self.shodan = ShodanCollector()
        self.dorks = DorksGenerator()

    def enriquecer(
        self,
        lead: Lead,
        usar_harvester: bool = False,
        usar_shodan: bool = False,
        usar_datajud: bool = True,
        usar_site: bool = True,
        callback=None,
    ) -> Lead:
        def step(msg):
            if callback:
                callback(msg)

        osint = {"dominio": lead.dominio_provavel()}

        step("Portal da Transparência...")
        osint["transparencia"] = self.transparencia.coletar_tudo(lead)

        if usar_datajud:
            step("DataJud — processos...")
            osint["processos"] = self.datajud.buscar_processos(lead)

        step("WHOIS...")
        osint["whois"] = self.whois.buscar(lead.dominio_provavel())

        if usar_site:
            step("Analisando site...")
            osint["site"] = self.site.analisar(lead.dominio_provavel())

        step("BNDES...")
        osint["bndes"] = self.bndes.buscar(lead.cnpj)

        step("PNCP...")
        osint["pncp"] = self.pncp.buscar(lead.cnpj)

        step("IBGE...")
        osint["ibge"] = self.ibge.buscar_municipio(lead.municipio, lead.uf)

        if usar_harvester and self.harvester.disponivel():
            step("theHarvester...")
            osint["harvester"] = self.harvester.coletar(lead.dominio_provavel())
        else:
            osint["harvester"] = {"emails": [], "hosts": [], "erro": "desativado"}

        if usar_shodan and self.shodan.disponivel():
            step("Shodan...")
            osint["shodan"] = self.shodan.buscar(lead.razao_social)

        step("Mapeando CNAE...")
        osint["cnae_insight"] = mapear_cnae(lead.cnae_codigo)

        osint["dorks"] = self.dorks.gerar(lead)

        lead.osint = osint
        return lead
