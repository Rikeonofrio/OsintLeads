import re
from typing import Dict, Optional

SHODAN_API_KEY: Optional[str] = None
TRANSPARENCIA_API_KEY: Optional[str] = None
PAGESPEED_API_KEY: Optional[str] = None

CNAE_DORES: Dict[str, Dict] = {
    "6920": {
        "setor": "Contabilidade",
        "dores": [
            "Processos manuais e planilhas",
            "Emissão de NF manual",
            "Obrigações acessórias (SPED, EFD) sem automação",
            "Comunicação com clientes dispersa",
        ],
        "oportunidades": [
            "Software contábil (Domínio, Alterdata)",
            "Automação de obrigações fiscais",
            "Portal do cliente",
            "Assinatura digital",
        ],
    },
    "4120": {
        "setor": "Construção civil",
        "dores": [
            "Gestão de obras sem sistema",
            "Controle de materiais no papel",
            "Medições e contratos manuais",
            "Subempreiteiros sem rastreabilidade",
        ],
        "oportunidades": ["ERP para construção", "Gestão de contratos", "BIM", "Consultoria RET"],
    },
    "4110": {
        "setor": "Incorporação imobiliária",
        "dores": ["Vendas na planilha", "Comissionamento manual", "Sem CRM para corretores"],
        "oportunidades": ["CRM imobiliário", "Sistema de incorporação", "Marketing digital"],
    },
    "4711": {
        "setor": "Supermercado / varejo alimentar",
        "dores": ["Estoque falho", "Perda de validade", "PDV lento", "SPED varejo manual"],
        "oportunidades": ["PDV + ERP", "Gestão de estoque", "Automação fiscal"],
    },
    "4713": {
        "setor": "Loja de departamentos",
        "dores": ["Sem integração com marketplaces", "Devoluções sem sistema", "Estoque multicanal"],
        "oportunidades": ["E-commerce", "ERP varejo", "Integração Mercado Livre/Shopee"],
    },
    "8630": {
        "setor": "Saúde — clínicas e hospitais",
        "dores": [
            "Prontuário em papel",
            "Faturamento de planos manual",
            "Agenda via WhatsApp",
            "Inadimplência sem cobrança automática",
        ],
        "oportunidades": ["Sistema de gestão clínica", "Prontuário eletrônico", "Cobrança automática"],
    },
    "8621": {
        "setor": "Ambulatório / serviços de saúde",
        "dores": ["Agenda manual", "Fila de espera", "Laudos no papel"],
        "oportunidades": ["Agendamento online", "Telemedicina", "Laudos digitais"],
    },
    "4921": {
        "setor": "Transporte coletivo",
        "dores": ["Frota sem controle", "Combustível sem gestão", "Manutenção corretiva"],
        "oportunidades": ["TMS / telemetria", "GPS", "Gestão de manutenção"],
    },
    "4930": {
        "setor": "Transporte de cargas",
        "dores": ["CIOT manual", "Entregas sem rastreio", "SPED Transportes trabalhoso"],
        "oportunidades": ["TMS", "Roteirização", "CTe/MDFe integrado"],
    },
    "6911": {
        "setor": "Advocacia",
        "dores": [
            "Prazos em planilha",
            "Financeiro manual",
            "Procurações e documentos físicos",
            "Cobrança de honorários sem sistema",
        ],
        "oportunidades": ["Software jurídico (Projuris, Advwin)", "Assinatura digital", "Cobrança recorrente"],
    },
    "8511": {
        "setor": "Educação infantil",
        "dores": ["Matrícula em papel", "Inadimplência sem automação", "Comunicação com pais no WhatsApp"],
        "oportunidades": ["ERP educacional", "App escola-pais", "Cobrança automática"],
    },
    "8512": {
        "setor": "Ensino fundamental",
        "dores": ["Diário de classe manual", "Avaliações sem sistema", "Sem portal do aluno"],
        "oportunidades": ["Sistema escolar", "Portal do aluno", "EAD"],
    },
    "5611": {
        "setor": "Restaurantes",
        "dores": ["Comanda no papel", "Delivery manual", "CMV sem controle", "Caixa frágil"],
        "oportunidades": ["Sistema de restaurante", "Integração iFood/Rappi", "Gestão de CMV"],
    },
    "6201": {
        "setor": "Desenvolvimento de software",
        "dores": ["Projetos gerenciados no e-mail", "Horas no Excel", "Proposta no Word"],
        "oportunidades": ["Jira / ClickUp", "CRM", "Automação de propostas"],
    },
    "6202": {
        "setor": "TI / infraestrutura",
        "dores": ["Suporte sem chamados", "SLA não monitorado", "Faturamento por projeto manual"],
        "oportunidades": ["Service desk", "Monitoramento", "ERP para TI"],
    },
    "7490": {
        "setor": "Consultoria",
        "dores": ["Proposta no Word", "Projetos por e-mail", "Cobrança de horas no Excel"],
        "oportunidades": ["CRM", "Automação de propostas", "Gestão de projetos", "Cobrança recorrente"],
    },
}

CNAE_GENERICO = {
    "dores": [
        "Processos manuais",
        "Financeiro sem visibilidade",
        "Dificuldade para escalar",
        "Gestão de clientes informal",
    ],
    "oportunidades": ["ERP / sistema de gestão", "CRM", "Automação financeira", "Marketing digital"],
}


def mapear_cnae(codigo: str) -> Dict:
    return CNAE_DORES.get(re.sub(r"\D", "", codigo)[:4], CNAE_GENERICO)
