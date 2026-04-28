import re
import shutil
from typing import List

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from lead_hunter_pkg.collectors import HarvesterCollector
from lead_hunter_pkg.models import Lead
from lead_hunter_pkg import config

console = Console()


class Display:
    def __init__(self):
        self.c = console

    def _cor(self, s: str) -> str:
        u = s.upper()
        if "ATIVA" in u:
            return "green"
        if any(x in u for x in ("BAIXADA", "CANCELADA", "NULA")):
            return "red"
        if any(x in u for x in ("SUSPENSA", "INAPTA")):
            return "yellow"
        return "white"

    def _cnpj(self, c: str) -> str:
        c = re.sub(r"\D", "", c)
        return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}" if len(c) == 14 else c

    def _capital(self, v) -> str:
        try:
            return f"R$ {float(str(v).replace(',','.')):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception:
            return str(v)

    def banner(self):
        self.c.print("""
[bold blue] ██╗     ███████╗ █████╗ ██████╗     ██╗  ██╗██╗   ██╗███╗   ██╗████████╗███████╗██████╗ [/bold blue]
[bold blue] ██║     ██╔════╝██╔══██╗██╔══██╗    ██║  ██║██║   ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗[/bold blue]
[bold blue] ██║     █████╗  ███████║██║  ██║    ███████║██║   ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝[/bold blue]
[bold blue] ██║     ██╔══╝  ██╔══██║██║  ██║    ██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗[/bold blue]
[bold blue] ███████╗███████╗██║  ██║██████╔╝    ██║  ██║╚██████╔╝██║ ╚████║   ██║   ███████╗██║  ██║[/bold blue]
[bold blue] ╚══════╝╚══════╝╚═╝  ╚═╝╚═════╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝[/bold blue]
[dim]  BrasilAPI · CNPJá · Transparência · DataJud · WHOIS · BNDES · PNCP · Shodan[/dim]
""")
        st = [
            ("[green]✔[/green]" if HarvesterCollector().disponivel() else "[red]✘[/red]") + " theHarvester",
            ("[green]✔[/green]" if shutil.which("whois")              else "[dim]–[/dim]") + " whois",
            ("[green]✔[/green]" if config.SHODAN_API_KEY              else "[dim]–[/dim]") + " Shodan",
            ("[green]✔[/green]" if config.TRANSPARENCIA_API_KEY       else "[yellow]~[/yellow]") + " Transparência",
            ("[green]✔[/green]" if config.PAGESPEED_API_KEY           else "[dim]–[/dim]") + " PageSpeed",
        ]
        self.c.print("  " + "    ".join(st))
        self.c.print()

    def menu(self, session: "LeadSession"):
        t = Table(box=box.SIMPLE, show_header=False, pad_edge=False)
        t.add_column("cmd", style="bold cyan", width=12)
        t.add_column("desc")
        for cmd, desc in [
            ("cnpj",        "Consulta básica por CNPJ"),
            ("osint",       "CNPJ + enriquecimento completo"),
            ("radiografia", "OSINT + salva relatório HTML"),
            ("lote",        "Processa arquivo .txt com CNPJs"),
            ("cep",         "Busca endereço por CEP"),
            ("leads",       "Lista leads da sessão"),
            ("filtro",      "Filtra leads"),
            ("dorks",       "Abre buscas no navegador"),
            ("export",      "Exporta CSV / JSON / HTML"),
            ("config",      "API keys"),
            ("limpar",      "Limpa sessão"),
            ("sair",        "Sair"),
        ]:
            t.add_row(f"  {cmd}", desc)
        self.c.print(t)
        self.c.print(f"  [dim]Leads: [bold]{session.total()}[/bold][/dim]\n")

    def empresa(self, lead: Lead):
        c = self.c
        nome = lead.nome_fantasia or lead.razao_social
        sit = lead.situacao
        osint = lead.osint
        transp = osint.get("transparencia", {})

        c.print()
        titulo = Text()
        titulo.append(f" {nome} ", style="bold white on blue")
        if nome != lead.razao_social:
            titulo.append(f"  {lead.razao_social}", style="dim")
        c.print(titulo)

        sit_txt = Text(f"  ● {sit}  ", style=f"bold {self._cor(sit)}")
        sit_txt.append(f"[{lead._fonte}]", style="dim")
        if transp.get("tem_sancoes"):
            sit_txt.append("  ⚠ SANÇÕES", style="bold red")
        c.print(sit_txt)
        c.print()

        t = Table(box=box.SIMPLE, show_header=False, pad_edge=False, expand=True)
        t.add_column("k", style="dim", min_width=22)
        t.add_column("v", style="bold")

        def row(lb, v, st=""):
            if v:
                t.add_row(lb, Text(str(v), style=st) if st else str(v))

        row("CNPJ",              self._cnpj(lead.cnpj))
        row("Abertura",          lead.abertura)
        row("Natureza Jurídica", lead.natureza_juridica)
        row("Porte",             lead.porte)
        row("Capital Social",    self._capital(lead.capital_social))
        row("CNAE",              f"{lead.cnae_codigo} – {lead.cnae_principal}")
        row("Simples Nacional",  "✔ Sim" if lead.simples_optante else "✘ Não",
            "green" if lead.simples_optante else "red")
        row("MEI",               "✔ Sim" if lead.mei else "✘ Não",
            "green" if lead.mei else "red")
        c.print(Panel(t, title="[bold]📋 Cadastro", border_style="blue"))

        tc = Table(box=box.SIMPLE, show_header=False, pad_edge=False, expand=True)
        tc.add_column("k", style="dim", min_width=16)
        tc.add_column("v")
        if lead.email:
            tc.add_row("📧 E-mail",   lead.email)
        if lead.telefone:
            tc.add_row("📞 Telefone", lead.telefone)
        end = lead.endereco_completo()
        if end:
            tc.add_row("📍 Endereço", end)
        if lead.email or lead.telefone or end:
            c.print(Panel(tc, title="[bold]📬 Contato", border_style="cyan"))

        if lead.socios:
            tq = Table(box=box.SIMPLE_HEAVY, show_header=True, pad_edge=False, expand=True)
            tq.add_column("Nome",         style="bold white", min_width=28)
            tq.add_column("Qualificação", style="yellow")
            tq.add_column("CPF/CNPJ",     style="dim")
            tq.add_column("Entrada",      style="dim")
            for s in lead.socios:
                tq.add_row(s.nome, s.qualificacao, s.cpf_cnpj, s.data_entrada)
            c.print(Panel(tq, title=f"[bold]👥 Sócios ({len(lead.socios)})", border_style="magenta"))

        if not osint:
            c.print()
            return

        if transp:
            tt = Table(box=box.SIMPLE, show_header=False, pad_edge=False, expand=True)
            tt.add_column("k", style="dim", min_width=24)
            tt.add_column("v", style="bold")
            for tipo, key in [("CEIS", "sancoes_ceis"), ("CNEP", "sancoes_cnep"), ("CEPIM", "sancoes_cepim")]:
                itens = transp.get(key, [])
                tt.add_row(f"⚠ {tipo}" if itens else tipo,
                           Text(f"{len(itens)} sanção(ões)", style="bold red") if itens else Text("✔ Limpo", style="green"))
            tt.add_row("Contratos", str(transp.get("total_contratos", 0)))
            tt.add_row("Licitações", str(transp.get("total_licitacoes", 0)))
            tt.add_row("Convênios", str(transp.get("total_convenios", 0)))
            tt.add_row("Obras", str(transp.get("total_obras", 0)))
            tt.add_row("Cartão gov.", str(transp.get("total_cartao", 0)))
            srv = transp.get("servidores_socios", {})
            if srv:
                tt.add_row("⚠ Sócios servidores", Text(", ".join(srv.keys()), style="bold yellow"))
            c.print(Panel(tt, title="[bold]🏛 Portal da Transparência", border_style="yellow"))

        proc = osint.get("processos", {})
        if proc and proc.get("total", 0) > 0:
            tp = Table(box=box.SIMPLE, show_header=False, pad_edge=False, expand=True)
            tp.add_column("k", style="dim", min_width=22)
            tp.add_column("v", style="bold")
            tp.add_row("Total", str(proc["total"]))
            tp.add_row("Trabalhistas",   Text(str(len(proc.get("trabalhistas", []))), style="bold red" if proc.get("tem_trabalhista") else "green"))
            tp.add_row("Fiscais",        Text(str(len(proc.get("fiscais", []))),       style="bold red" if proc.get("tem_fiscal")      else "green"))
            tp.add_row("Cíveis",         str(len(proc.get("civeis", []))))
            c.print(Panel(tp, title="[bold]⚖ Processos (DataJud)", border_style="red"))

        site_d = osint.get("site", {})
        if site_d:
            ts = Table(box=box.SIMPLE, show_header=False, pad_edge=False, expand=True)
            ts.add_column("k", style="dim", min_width=18)
            ts.add_column("v")
            ts.add_row("Domínio",    site_d.get("dominio", ""))
            ts.add_row("SSL",        Text("✔ Sim", style="green") if site_d.get("ssl") else Text("❌ Não", style="red"))
            ts.add_row("Acessível",  Text("✔ Sim", style="green") if site_d.get("acessivel") else Text("❌ Não", style="red"))
            if site_d.get("tecnologias"):
                ts.add_row("Tecnologias", ", ".join(site_d["tecnologias"]))
            ts.add_row("Analytics", "✔" if site_d.get("tem_analytics") else "Não")
            ts.add_row("FB Pixel",  "✔" if site_d.get("tem_pixel") else "Não")
            if site_d.get("pagespeed_score") is not None:
                score = site_d["pagespeed_score"]
                cor = "green" if score >= 75 else ("yellow" if score >= 50 else "red")
                ts.add_row("PageSpeed", Text(f"{score}/100", style=f"bold {cor}"))
            c.print(Panel(ts, title="[bold]🌐 Site", border_style="green"))
            for dor in site_d.get("sinais_dor", []):
                c.print(f"    [yellow]{dor}[/yellow]")

        whois_d = osint.get("whois", {})
        if whois_d.get("encontrado"):
            tw = Table(box=box.SIMPLE, show_header=False, pad_edge=False, expand=True)
            tw.add_column("k", style="dim", min_width=18)
            tw.add_column("v", style="bold")
            for k, v in [
                ("Registrante",  whois_d.get("registrante", "")),
                ("E-mail",       whois_d.get("email_registrante", "")),
                ("Criado",       whois_d.get("criado", "")),
                ("Expira",       whois_d.get("expira", "")),
                ("Nameservers",  ", ".join(whois_d.get("nameservers", []))),
            ]:
                if v:
                    tw.add_row(k, v)
            c.print(Panel(tw, title="[bold]🔒 WHOIS", border_style="bright_green"))

        insight = osint.get("cnae_insight", {})
        if insight:
            ti = Table(box=box.SIMPLE, show_header=False, pad_edge=False, expand=True)
            ti.add_column("k", style="dim", min_width=18)
            ti.add_column("v")
            ti.add_row("Setor", insight.get("setor", ""))
            ti.add_row("Dores",         "\n".join(f"• {d}" for d in insight.get("dores", [])))
            ti.add_row("Oportunidades", Text("\n".join(f"• {o}" for o in insight.get("oportunidades", [])), style="bold green"))
            c.print(Panel(ti, title=f"[bold]🎯 Dores & Oportunidades — CNAE {lead.cnae_codigo}", border_style="bright_cyan"))

        harvest = osint.get("harvester", {})
        if harvest.get("emails") or harvest.get("hosts"):
            th = Table(box=box.SIMPLE, show_header=False, pad_edge=False, expand=True)
            th.add_column("k", style="dim", min_width=16)
            th.add_column("v")
            if harvest.get("emails"):
                th.add_row("📧 E-mails", "\n".join(harvest["emails"][:8]))
            if harvest.get("hosts"):
                th.add_row("🖥 Hosts",    "\n".join(harvest["hosts"][:8]))
            c.print(Panel(th, title="[bold]🌾 theHarvester", border_style="bright_green"))

        dorks = osint.get("dorks", [])
        if dorks:
            c.print(f"\n[bold bright_cyan]🔎 Dorks[/bold bright_cyan] [dim]— {len(dorks)} buscas — use o comando [bold]dorks[/bold] para abrir[/dim]\n")
            for i, dk in enumerate(dorks, 1):
                c.print(f"  [bold cyan]{i:>2}.[/bold cyan] [dim]{dk['desc']}[/dim]")
                c.print(f"      [cyan]G:[/cyan] {dk['google']}")
                c.print(f"      [blue]B:[/blue] {dk['bing']}")
                c.print()

        c.print()

    def lista(self, leads: List[Lead], titulo: str = "Leads"):
        if not leads:
            self.c.print("[yellow]  Nenhum lead.[/yellow]")
            return
        t = Table(title=f"[bold]{titulo} — {len(leads)} empresa(s)", box=box.ROUNDED, expand=True)
        t.add_column("#",      style="dim",   width=4)
        t.add_column("Razão",  style="bold",  min_width=24)
        t.add_column("Sit.",                  min_width=8)
        t.add_column("UF",                    width=4)
        t.add_column("Município",             min_width=12)
        t.add_column("E-mail", style="cyan",  min_width=18)
        t.add_column("San.",                  width=6)
        t.add_column("Proc.",                 width=6)
        t.add_column("SSL",                   width=5)
        t.add_column("Dores",  style="yellow",min_width=8)
        for i, l in enumerate(leads, 1):
            sit = l.situacao
            osint = l.osint
            transp = osint.get("transparencia", {})
            proc = osint.get("processos", {})
            site_d = osint.get("site", {})
            t.add_row(
                str(i),
                l.razao_social[:26],
                Text(sit, style=self._cor(sit)),
                l.uf,
                l.municipio[:14],
                l.email[:20],
                Text("⚠", style="bold red") if transp.get("tem_sancoes") else Text("✔", style="green"),
                Text(str(proc.get("total", 0)), style="red" if proc.get("total", 0) > 0 else "green"),
                Text("✔" if site_d.get("ssl") else ("❌" if site_d else "—"), style="green" if site_d.get("ssl") else "red"),
                str(len(site_d.get("sinais_dor", []))) + "x",
            )
        self.c.print(t)
        self.c.print()
