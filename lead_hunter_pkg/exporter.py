import csv
import json
from datetime import datetime
from typing import List

from lead_hunter_pkg.models import Lead
from lead_hunter_pkg.collectors import DorksGenerator


class Exporter:
    CAMPOS_CSV = [
        "cnpj", "razao_social", "nome_fantasia", "situacao", "abertura",
        "natureza_juridica", "porte", "capital_social", "cnae_codigo", "cnae_principal",
        "simples_optante", "mei", "email", "telefone", "logradouro", "numero",
        "complemento", "bairro", "municipio", "uf", "cep",
        "socios_count", "socios_nomes",
        "dominio", "whois_registrante", "whois_email",
        "tem_sancoes", "total_contratos", "total_convenios", "total_obras",
        "processos_trabalhistas", "processos_fiscais",
        "emails_osint", "hosts_osint",
        "site_ssl", "site_tecnologias", "sinais_dor",
        "bndes_financiamentos", "pncp_contratos",
        "setor_cnae", "oportunidades",
    ]

    def csv(self, leads: List[Lead], caminho: str) -> str:
        with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=self.CAMPOS_CSV, extrasaction="ignore")
            w.writeheader()
            for lead in leads:
                w.writerow(self._row(lead))
        return caminho

    def json(self, leads: List[Lead], caminho: str) -> str:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump([l.to_dict() for l in leads], f, ensure_ascii=False, indent=2)
        return caminho

    def html_dorks(self, leads: List[Lead], caminho: str) -> str:
        gen    = DorksGenerator()
        blocos = []
        for lead in leads:
            dorks  = lead.osint.get("dorks") or gen.gerar(lead)
            linhas = "".join(
                f"<tr><td>{dk['desc']}</td>"
                f"<td><a href='{dk['google']}' target='_blank'>Google</a></td>"
                f"<td><a href='{dk['bing']}'   target='_blank'>Bing</a></td></tr>"
                for dk in dorks
            )
            blocos.append(
                f'<div class="empresa"><h2>{lead.razao_social} <span class="cnpj">{lead.cnpj}</span></h2>'
                f"<table><thead><tr><th>Busca</th><th>Google</th><th>Bing</th></tr></thead>"
                f"<tbody>{linhas}</tbody></table></div>"
            )
        css = (
            "body{font-family:sans-serif;background:#0d1117;color:#e6edf3;padding:24px}"
            "h1{color:#58a6ff;border-bottom:1px solid #30363d;padding-bottom:8px}"
            ".empresa{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:18px;margin-bottom:18px}"
            "h2{color:#f0f6fc;font-size:1em;margin:0 0 12px}.cnpj{color:#8b949e;font-size:.8em;font-weight:normal;margin-left:8px}"
            "table{width:100%;border-collapse:collapse}"
            "th{background:#21262d;color:#8b949e;text-align:left;padding:7px 10px;font-size:.85em}"
            "td{padding:7px 10px;border-bottom:1px solid #21262d;font-size:.88em}"
            "tr:hover td{background:#1c2128}a{color:#58a6ff;text-decoration:none}a:hover{text-decoration:underline}"
        )
        html = (
            f'<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">'
            f'<title>Lead Hunter — Dorks</title><style>{css}</style></head>'
            f'<body><h1>🔍 Lead Hunter BR — Dorks</h1>{"".join(blocos)}'
            f'<p style="color:#8b949e;font-size:.78em;margin-top:24px">'
            f'Gerado em {datetime.now().strftime("%d/%m/%Y %H:%M")}</p></body></html>'
        )
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(html)
        return caminho

    def html_radiografia(self, lead: Lead, caminho: str) -> str:
        osint     = lead.osint
        transp    = osint.get("transparencia", {})
        processos = osint.get("processos", {})
        site_d    = osint.get("site", {})
        whois_d   = osint.get("whois", {})
        insight   = osint.get("cnae_insight", {})
        harvest   = osint.get("harvester", {})

        def kv(pares):
            rows = "".join(f"<tr><td class='k'>{k}</td><td>{v}</td></tr>" for k, v in pares if v)
            return f"<table class='kv'>{rows}</table>"

        def ul(items, cor=""):
            return "<ul>" + "".join(
                f"<li style='color:{cor}'>{i}</li>" if cor else f"<li>{i}</li>"
                for i in items
            ) + "</ul>"

        def card(titulo, conteudo, full=False):
            return f'<div class="{"card full" if full else "card"}"><h3>{titulo}</h3>{conteudo}</div>'

        cor_san  = "color:red" if transp.get("tem_sancoes") else "color:green"
        s_cad    = kv([
            ("CNPJ",              lead.cnpj),
            ("Razão Social",      lead.razao_social),
            ("Nome Fantasia",     lead.nome_fantasia),
            ("Situação",          lead.situacao),
            ("Abertura",          lead.abertura),
            ("Natureza Jurídica", lead.natureza_juridica),
            ("Porte",             lead.porte),
            ("Capital Social",    str(lead.capital_social)),
            ("CNAE",              f"{lead.cnae_codigo} — {lead.cnae_principal}"),
            ("Simples",           "Sim" if lead.simples_optante else "Não"),
            ("MEI",               "Sim" if lead.mei else "Não"),
            ("E-mail",            lead.email),
            ("Telefone",          lead.telefone),
            ("Endereço",          lead.endereco_completo()),
        ])
        s_socios = (
            "<table><tr><th>Nome</th><th>Qualificação</th><th>Entrada</th></tr>"
            + "".join(f"<tr><td>{s.nome}</td><td>{s.qualificacao}</td><td>{s.data_entrada}</td></tr>" for s in lead.socios)
            + "</table>"
        )
        s_transp = kv([
            ("Sanções",            f"<span style='{cor_san}'>{'⚠ SIM' if transp.get('tem_sancoes') else '✔ Não'}</span>"),
            ("Contratos federais", str(transp.get("total_contratos", 0))),
            ("Licitações",         str(transp.get("total_licitacoes", 0))),
            ("Convênios",          str(transp.get("total_convenios", 0))),
            ("Obras",              str(transp.get("total_obras", 0))),
            ("Cartão corporativo", str(transp.get("total_cartao", 0))),
        ])
        s_proc = kv([
            ("Total",          str(processos.get("total", 0))),
            ("Trabalhistas",   f"{'⚠ ' if processos.get('tem_trabalhista') else ''}{len(processos.get('trabalhistas', []))}"),
            ("Fiscais",        f"{'⚠ ' if processos.get('tem_fiscal') else ''}{len(processos.get('fiscais', []))}"),
            ("Cíveis",         str(len(processos.get("civeis", [])))),
        ])
        s_site = kv([
            ("Domínio",   site_d.get("dominio", "")),
            ("SSL",       "✔ Sim" if site_d.get("ssl") else "❌ Não"),
            ("Acessível", "✔ Sim" if site_d.get("acessivel") else "❌ Não"),
            ("Tecnologias",", ".join(site_d.get("tecnologias", [])) or "—"),
            ("Analytics", "✔" if site_d.get("tem_analytics") else "Não"),
            ("FB Pixel",  "✔" if site_d.get("tem_pixel") else "Não"),
        ]) + (ul(site_d.get("sinais_dor", []), "#f0ad4e") if site_d.get("sinais_dor") else "")
        s_whois = kv([
            ("Registrante", whois_d.get("registrante", "")),
            ("E-mail",      whois_d.get("email_registrante", "")),
            ("Criado",      whois_d.get("criado", "")),
            ("Expira",      whois_d.get("expira", "")),
            ("Nameservers", ", ".join(whois_d.get("nameservers", []))),
        ]) if whois_d.get("encontrado") else "<p>Domínio não encontrado.</p>"
        s_insight = (
            f"<p><b>Setor:</b> {insight.get('setor', '—')}</p>"
            + ul(insight.get("dores", []), "#f0ad4e")
            + "<p><b>Oportunidades:</b></p>"
            + ul(insight.get("oportunidades", []), "#5cb85c")
        )
        emails_h = harvest.get("emails", [])
        s_emails = ul(emails_h[:10]) if emails_h else "<p>Nenhum e-mail encontrado.</p>"

        css = (
            "*{box-sizing:border-box;margin:0;padding:0}"
            "body{font-family:sans-serif;background:#0d1117;color:#e6edf3;padding:24px}"
            "h1{color:#58a6ff;margin-bottom:4px}.sub{color:#8b949e;margin-bottom:20px;font-size:.88em}"
            ".grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}"
            ".card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px}"
            ".card.full{grid-column:1/-1}"
            "h3{color:#58a6ff;margin-bottom:10px;font-size:.9em;text-transform:uppercase;letter-spacing:.05em}"
            "table{width:100%;border-collapse:collapse;font-size:.86em}"
            "table.kv td.k{color:#8b949e;width:38%;padding:3px 6px 3px 0;vertical-align:top}"
            "table.kv td{padding:3px 0;border-bottom:1px solid #21262d;vertical-align:top}"
            "th{background:#21262d;color:#8b949e;text-align:left;padding:5px 8px;font-size:.83em}"
            "td{padding:5px 8px;border-bottom:1px solid #21262d}"
            "ul{padding-left:16px;font-size:.86em;line-height:1.7}"
            ".ts{color:#8b949e;font-size:.76em;margin-top:24px;text-align:right}"
        )
        html = (
            f'<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">'
            f"<title>{lead.razao_social}</title><style>{css}</style></head><body>"
            f"<h1>🔍 {lead.razao_social}</h1>"
            f'<p class="sub">{lead.cnpj} · {lead.municipio}/{lead.uf} · {lead._fonte}</p>'
            f'<div class="grid">'
            f"{card('📋 Cadastro', s_cad)}"
            f"{card('👥 Sócios', s_socios)}"
            f"{card('🏛 Transparência', s_transp)}"
            f"{card('⚖ Processos', s_proc)}"
            f"{card('🌐 Site', s_site)}"
            f"{card('🔒 WHOIS', s_whois)}"
            f"{card(f'🎯 Dores & Oportunidades — CNAE {lead.cnae_codigo}', s_insight, full=True)}"
            f"{card('📧 E-mails OSINT', s_emails)}"
            f"</div>"
            f'<p class="ts">Lead Hunter BR · {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>'
            f"</body></html>"
        )
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(html)
        return caminho

    def _row(self, lead: Lead) -> dict:
        osint   = lead.osint
        transp  = osint.get("transparencia", {})
        proc    = osint.get("processos", {})
        site_d  = osint.get("site", {})
        whois_d = osint.get("whois", {})
        harvest = osint.get("harvester", {})
        insight = osint.get("cnae_insight", {})
        return {
            "cnpj":                  lead.cnpj,
            "razao_social":          lead.razao_social,
            "nome_fantasia":         lead.nome_fantasia,
            "situacao":              lead.situacao,
            "abertura":              lead.abertura,
            "natureza_juridica":     lead.natureza_juridica,
            "porte":                 lead.porte,
            "capital_social":        lead.capital_social,
            "cnae_codigo":           lead.cnae_codigo,
            "cnae_principal":        lead.cnae_principal,
            "simples_optante":       "Sim" if lead.simples_optante else "Não",
            "mei":                   "Sim" if lead.mei else "Não",
            "email":                 lead.email,
            "telefone":              lead.telefone,
            "logradouro":            lead.logradouro,
            "numero":                lead.numero,
            "complemento":           lead.complemento,
            "bairro":                lead.bairro,
            "municipio":             lead.municipio,
            "uf":                    lead.uf,
            "cep":                   lead.cep,
            "socios_count":          len(lead.socios),
            "socios_nomes":          " | ".join(s.nome for s in lead.socios),
            "dominio":               osint.get("dominio", ""),
            "whois_registrante":     whois_d.get("registrante", ""),
            "whois_email":           whois_d.get("email_registrante", ""),
            "tem_sancoes":           "SIM ⚠" if transp.get("tem_sancoes") else "Não",
            "total_contratos":       transp.get("total_contratos", 0),
            "total_convenios":       transp.get("total_convenios", 0),
            "total_obras":           transp.get("total_obras", 0),
            "processos_trabalhistas":len(proc.get("trabalhistas", [])),
            "processos_fiscais":     len(proc.get("fiscais", [])),
            "emails_osint":          " | ".join(harvest.get("emails", [])[:5]),
            "hosts_osint":           " | ".join(harvest.get("hosts", [])[:5]),
            "site_ssl":              "Sim" if site_d.get("ssl") else "Não",
            "site_tecnologias":      ", ".join(site_d.get("tecnologias", [])),
            "sinais_dor":            " | ".join(site_d.get("sinais_dor", [])),
            "bndes_financiamentos":  len(osint.get("bndes", [])),
            "pncp_contratos":        len(osint.get("pncp", [])),
            "setor_cnae":            insight.get("setor", ""),
            "oportunidades":         " | ".join(insight.get("oportunidades", [])),
        }
