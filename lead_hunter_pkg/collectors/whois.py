from lead_hunter_pkg.collectors.base import BaseCollector


class WhoisCollector(BaseCollector):
    def buscar(self, dominio: str) -> dict:
        r = {"dominio": dominio, "encontrado": False}
        raw = self._get(f"https://rdap.registro.br/domain/{dominio}")
        if not raw:
            return r
        r["encontrado"] = True
        r["status"] = raw.get("status", [])
        r["nameservers"] = [n.get("ldhName", "") for n in raw.get("nameservers", [])]
        r["criado"] = ""
        r["expira"] = ""
        r["registrante"] = ""
        r["email_registrante"] = ""
        for ev in raw.get("events", []):
            if ev.get("eventAction") == "registration":
                r["criado"] = ev.get("eventDate", "")[:10]
            if ev.get("eventAction") == "expiration":
                r["expira"] = ev.get("eventDate", "")[:10]
        for ent in raw.get("entities", []):
            if "registrant" not in ent.get("roles", []):
                continue
            for campo in ent.get("vcardArray", [None, []])[1]:
                if isinstance(campo, list):
                    if campo[0] == "fn":
                        r["registrante"] = campo[3]
                    if campo[0] == "email":
                        r["email_registrante"] = campo[3]
        return r
