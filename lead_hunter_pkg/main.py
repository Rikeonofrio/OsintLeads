#!/usr/bin/env python3
# lead_hunter — entry point
# pip install rich requests shodan

import os
import re
import sys
import time
import threading
import webbrowser
from datetime import datetime

from rich import box
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

from lead_hunter_pkg import Lead, LeadSession, Enricher, Exporter, Display, CNPJCollector
from lead_hunter_pkg.collectors import BaseCollector, DorksGenerator
from lead_hunter_pkg import config

console = Console()


class CLI:
    def __init__(self):
        self.session  = LeadSession()
        self.cnpj_col = CNPJCollector()
        self.enricher = Enricher()
        self.exporter = Exporter()
        self.display  = Display()

    def _opcoes_osint(self) -> dict:
        return {
            "usar_datajud":   Confirm.ask("  DataJud?",       default=True),
            "usar_site":      Confirm.ask("  Analisar site?", default=True),
            "usar_harvester": Confirm.ask("  theHarvester?",  default=False) if self.enricher.harvester.disponivel() else False,
            "usar_shodan":    Confirm.ask("  Shodan?",        default=False) if self.enricher.shodan.disponivel()    else False,
        }

    def _enriquecer(self, lead: Lead, opcoes: dict) -> Lead:
        etapa  = [""]
        result = [None]
        erro   = [None]

        def cb(msg): etapa[0] = msg
        def run():
            try:    result[0] = self.enricher.enriquecer(lead, callback=cb, **opcoes)
            except Exception as e: erro[0] = e

        with Progress(SpinnerColumn(), TextColumn("[cyan]{task.description}")) as prog:
            task = prog.add_task("Iniciando...", total=None)
            t = threading.Thread(target=run)
            t.start()
            while t.is_alive():
                prog.update(task, description=f"[cyan]{etapa[0]}")
                time.sleep(0.3)
            t.join()

        if erro[0]:
            console.print(f"  [red]Erro: {erro[0]}[/red]")
        return result[0] or lead

    def cmd_cnpj(self):
        cnpj = Prompt.ask("  [cyan]CNPJ[/cyan]").strip()
        if not cnpj: return
        with Progress(SpinnerColumn(), TextColumn("[cyan]Consultando..."), transient=True) as p:
            p.add_task("")
            lead = self.cnpj_col.buscar(cnpj)
        if not lead:
            console.print("[red]  ✘ Não encontrado.[/red]\n"); return
        self.display.empresa(lead)
        if Confirm.ask("  Adicionar à sessão?", default=True):
            self.session.adicionar(lead)
            console.print(f"  [green]✔ {self.session.total()} leads[/green]\n")

    def cmd_osint(self):
        cnpj = Prompt.ask("  [cyan]CNPJ[/cyan]").strip()
        if not cnpj: return
        with Progress(SpinnerColumn(), TextColumn("[cyan]Buscando..."), transient=True) as p:
            p.add_task("")
            lead = self.cnpj_col.buscar(cnpj)
        if not lead:
            console.print("[red]  ✘ Não encontrado.[/red]\n"); return
        lead = self._enriquecer(lead, self._opcoes_osint())
        self.display.empresa(lead)
        if Confirm.ask("  Adicionar?", default=True):
            self.session.adicionar(lead)
            console.print(f"  [green]✔ {self.session.total()} leads[/green]\n")

    def cmd_radiografia(self):
        cnpj = Prompt.ask("  [cyan]CNPJ[/cyan]").strip()
        if not cnpj: return
        with Progress(SpinnerColumn(), TextColumn("[cyan]Buscando..."), transient=True) as p:
            p.add_task("")
            lead = self.cnpj_col.buscar(cnpj)
        if not lead:
            console.print("[red]  ✘ Não encontrado.[/red]\n"); return
        lead    = self._enriquecer(lead, self._opcoes_osint())
        self.display.empresa(lead)
        nome_e  = re.sub(r"[^a-z0-9]", "_", lead.razao_social.lower())[:25]
        caminho = f"radiografia_{nome_e}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        self.exporter.html_radiografia(lead, caminho)
        console.print(f"\n  [green]✔ {caminho}[/green]")
        if Confirm.ask("  Abrir no navegador?", default=True):
            webbrowser.open(f"file://{os.path.abspath(caminho)}")
        if Confirm.ask("  Adicionar à sessão?", default=True):
            self.session.adicionar(lead)
            console.print(f"  [green]✔ {self.session.total()} leads[/green]\n")

    def cmd_lote(self):
        arquivo = Prompt.ask("  [cyan]Arquivo[/cyan]").strip()
        try:
            with open(arquivo) as f:
                cnpjs = [l.strip() for l in f if l.strip()]
        except FileNotFoundError:
            console.print(f"  [red]✘ {arquivo}[/red]\n"); return
        enrich = Confirm.ask(f"  Enriquecer ({len(cnpjs)} CNPJs)?", default=False)
        ok = erros = 0
        with Progress(SpinnerColumn(), TextColumn("[cyan]{task.description}"), transient=False) as prog:
            task = prog.add_task("...", total=len(cnpjs))
            for cnpj in cnpjs:
                prog.update(task, description=f"[cyan]{cnpj}")
                lead = self.cnpj_col.buscar(cnpj)
                if lead:
                    if enrich: lead = self.enricher.enriquecer(lead, usar_harvester=False)
                    self.session.adicionar(lead)
                    ok += 1
                else:
                    erros += 1
                prog.advance(task)
                time.sleep(0.8)
        console.print(f"\n  [green]✔ {ok}[/green]  [red]{erros} falhas[/red]  total: [bold]{self.session.total()}[/bold]\n")

    def cmd_cep(self):
        cep = Prompt.ask("  [cyan]CEP[/cyan]").strip()
        if not cep: return
        col = BaseCollector.__new__(BaseCollector)
        with Progress(SpinnerColumn(), TextColumn("[cyan]Consultando..."), transient=True) as p:
            p.add_task("")
            data = col._get(f"https://brasilapi.com.br/api/cep/v2/{re.sub(r'[^0-9]','',cep)}")
        if not data:
            console.print("  [red]✘ CEP não encontrado.[/red]\n"); return
        t = Table(box=box.SIMPLE, show_header=False)
        t.add_column("k", style="dim", min_width=14)
        t.add_column("v", style="bold")
        for lb, k in [("CEP","cep"),("Logradouro","street"),("Bairro","neighborhood"),
                      ("Cidade","city"),("Estado","state"),("IBGE","ibge")]:
            v = str(data.get(k, ""))
            if v: t.add_row(lb, v)
        console.print(t)
        console.print()

    def cmd_leads(self):
        leads = self.session.todos()
        if not leads:
            console.print("  [yellow]Sessão vazia.[/yellow]\n"); return
        self.display.lista(leads, "Leads")

    def cmd_filtro(self):
        if not self.session.total():
            console.print("  [yellow]Sessão vazia.[/yellow]\n"); return
        console.print("  [dim]Enter para ignorar.[/dim]")
        uf        = Prompt.ask("  UF",        default="").strip()
        municipio = Prompt.ask("  Município", default="").strip()
        cnae      = Prompt.ask("  CNAE",      default="").strip()
        situacao  = Prompt.ask("  Situação",  default="").strip()
        com_email = Confirm.ask("  Só com e-mail?",   default=False)
        com_tel   = Confirm.ask("  Só com telefone?", default=False)
        sem_san   = Confirm.ask("  Excluir sanções?", default=False)
        resultado = self.session.filtrar(
            uf=uf or None, municipio=municipio or None,
            cnae=cnae or None, situacao=situacao or None,
            com_email=com_email, com_telefone=com_tel, sem_sancoes=sem_san,
        )
        self.display.lista(resultado, "Filtro")
        console.print(f"  [dim]{len(resultado)} de {self.session.total()}[/dim]\n")

    def cmd_dorks(self):
        leads = self.session.todos()
        if not leads:
            console.print("  [yellow]Sessão vazia.[/yellow]\n"); return
        for i, l in enumerate(leads, 1):
            console.print(f"  {i}. {l.razao_social}")
        idx = Prompt.ask("  Número").strip()
        try:
            lead = leads[int(idx) - 1]
        except (ValueError, IndexError):
            console.print("  [red]Inválido.[/red]\n"); return

        dorks = lead.osint.get("dorks") or DorksGenerator().gerar(lead)
        console.print()
        for i, dk in enumerate(dorks, 1):
            console.print(f"  [bold cyan]{i:>2}.[/bold cyan] [dim]{dk['desc']}[/dim]")
            console.print(f"      [cyan]G:[/cyan] {dk['google']}")
            console.print(f"      [blue]B:[/blue] {dk['bing']}")
            console.print()

        console.print("  [bold]Ação:[/bold]  all · bing · 1,3,5 · html · nao")
        acao = Prompt.ask("  Ação").strip().lower()

        if acao in ("nao", ""):
            return
        if acao == "html":
            nome_e  = re.sub(r"[^a-z0-9]", "_", lead.razao_social.lower())[:20]
            caminho = f"dorks_{nome_e}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            self.exporter.html_dorks([lead], caminho)
            console.print(f"\n  [green]✔ {caminho}[/green]")
            if Confirm.ask("  Abrir?", default=True):
                webbrowser.open(f"file://{os.path.abspath(caminho)}")
        else:
            engine  = "bing" if acao == "bing" else "google"
            indices = list(range(len(dorks))) if acao in ("all", "bing") else [int(x.strip()) - 1 for x in acao.split(",")]
            abertos = 0
            for i in indices:
                if 0 <= i < len(dorks):
                    webbrowser.open(dorks[i]["google"] if engine == "google" else dorks[i]["bing"])
                    abertos += 1
                    time.sleep(0.4)
            console.print(f"\n  [green]✔ {abertos} abertas[/green]\n")

    def cmd_export(self):
        if not self.session.total():
            console.print("  [yellow]Sessão vazia.[/yellow]\n"); return
        fmt     = Prompt.ask("  Formato", choices=["csv", "json", "html"], default="csv")
        ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
        caminho = Prompt.ask("  Arquivo", default=f"leads_{ts}.{fmt}").strip()
        leads   = self.session.todos()
        if fmt == "csv":    dest = self.exporter.csv(leads, caminho)
        elif fmt == "json": dest = self.exporter.json(leads, caminho)
        else:               dest = self.exporter.html_dorks(leads, caminho)
        console.print(f"\n  [green]✔ {len(leads)} leads → {dest}[/green]\n")

    def cmd_config(self):
        s = Prompt.ask("  Shodan",        default=config.SHODAN_API_KEY        or "").strip()
        t = Prompt.ask("  Transparência", default=config.TRANSPARENCIA_API_KEY or "").strip()
        g = Prompt.ask("  PageSpeed",     default=config.PAGESPEED_API_KEY     or "").strip()
        if s: config.SHODAN_API_KEY        = s
        if t: config.TRANSPARENCIA_API_KEY = t
        if g: config.PAGESPEED_API_KEY     = g
        console.print("  [green]✔[/green]\n")

    def cmd_limpar(self):
        if not self.session.total():
            console.print("  [yellow]Já vazia.[/yellow]\n"); return
        if Confirm.ask(f"  Limpar {self.session.total()} leads?", default=False):
            self.session.limpar()
            console.print("  [green]✔[/green]\n")

    CMDS = {
        "cnpj":        "cmd_cnpj",
        "osint":       "cmd_osint",
        "radiografia": "cmd_radiografia",
        "lote":        "cmd_lote",
        "cep":         "cmd_cep",
        "leads":       "cmd_leads",
        "filtro":      "cmd_filtro",
        "dorks":       "cmd_dorks",
        "export":      "cmd_export",
        "config":      "cmd_config",
        "limpar":      "cmd_limpar",
    }

    def run(self):
        self.display.banner()
        self.display.menu(self.session)
        while True:
            try:
                cmd = Prompt.ask("\n[bold blue]lead-hunter[/bold blue]").strip().lower()
            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]Até logo![/dim]")
                sys.exit(0)
            if cmd in ("sair", "exit", "q"):
                console.print("[dim]Até logo![/dim]"); break
            elif cmd == "ajuda":
                self.display.menu(self.session)
            elif cmd in self.CMDS:
                try:
                    getattr(self, self.CMDS[cmd])()
                except KeyboardInterrupt:
                    console.print("\n  [yellow]Cancelado.[/yellow]")
            elif cmd:
                console.print(f"  [red]?[/red] '{cmd}'")


if __name__ == "__main__":
    CLI().run()
