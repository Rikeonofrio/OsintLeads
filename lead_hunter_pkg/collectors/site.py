from typing import List

import requests

from lead_hunter_pkg import config
from lead_hunter_pkg.collectors.base import BaseCollector


class SiteAnalyzer(BaseCollector):
    def _techs(self, html: str, headers: dict) -> List[str]:
        h = html.lower()
        srv = headers.get("Server", "").lower()
        pw = headers.get("X-Powered-By", "").lower()
        checks = [
            ("WordPress",        "wp-content" in h or "wp-includes" in h),
            ("Joomla",           "joomla" in h),
            ("Shopify",          "shopify" in h),
            ("Wix",              "wix.com" in h),
            ("PHP",              "php" in pw),
            ("ASP.NET",          "asp.net" in pw or "aspnet" in pw),
            ("Apache",           "apache" in srv),
            ("Nginx",            "nginx" in srv),
            ("Bootstrap",        "bootstrap" in h),
            ("React",            "react" in h or "__react" in h),
            ("jQuery",           "jquery" in h),
            ("Google Analytics", "google-analytics.com" in h or "gtag" in h),
            ("Facebook Pixel",   "connect.facebook.net" in h),
            ("WhatsApp Widget",  "wa.me" in h or "whatsapp" in h),
            ("Hotjar",           "hotjar" in h),
            ("RD Station",       "rdstation" in h),
        ]
        return [nome for nome, cond in checks if cond]

    def analisar(self, dominio: str) -> dict:
        r = {
            "dominio": dominio, "ssl": False, "acessivel": False,
            "tecnologias": [], "tem_analytics": False, "tem_pixel": False,
            "sinais_dor": [], "erro": "",
        }
        for scheme in ["https", "http"]:
            try:
                resp = requests.get(f"{scheme}://{dominio}", timeout=10,
                                    allow_redirects=True, headers=self.HEADERS)
                r["acessivel"] = True
                r["ssl"] = scheme == "https" or resp.url.startswith("https")
                r["tecnologias"] = self._techs(resp.text, dict(resp.headers))
                r["tem_analytics"] = "Google Analytics" in r["tecnologias"]
                r["tem_pixel"] = "Facebook Pixel" in r["tecnologias"]
                break
            except requests.exceptions.SSLError:
                r["sinais_dor"].append("❌ SSL inválido ou expirado")
            except Exception as e:
                r["erro"] = str(e)

        if not r["ssl"]:
            r["sinais_dor"].append("🔓 Sem HTTPS")
        if "WordPress" in r["tecnologias"]:
            r["sinais_dor"].append("🔧 WordPress — pode estar desatualizado")
        if not r["tem_analytics"]:
            r["sinais_dor"].append("📊 Sem Google Analytics")
        if not r["tem_pixel"]:
            r["sinais_dor"].append("📢 Sem Facebook Pixel")
        if "WhatsApp Widget" in r["tecnologias"]:
            r["sinais_dor"].append("📱 Atendimento via WhatsApp — sem CRM")
        if not r["acessivel"]:
            r["sinais_dor"].append("🚫 Site inacessível")

        if config.PAGESPEED_API_KEY and r["acessivel"]:
            ps = self._get(
                "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
                params={"url": f"https://{dominio}", "key": config.PAGESPEED_API_KEY, "strategy": "mobile"},
            )
            if ps:
                score = int(ps.get("lighthouseResult", {}).get("categories", {}).get("performance", {}).get("score", 0) * 100)
                r["pagespeed_score"] = score
                if score < 50:
                    r["sinais_dor"].append(f"🐌 Site lento ({score}/100)")
                elif score < 75:
                    r["sinais_dor"].append(f"⚠ Performance mediana ({score}/100)")
        return r
