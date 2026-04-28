# 🔍 Lead Hunter BR

Ferramenta de terminal em Python para coleta de dados públicos de empresas brasileiras, com foco em prospecção B2B e due diligence.

Cruza múltiplas fontes abertas e gratuitas para gerar uma visão completa de qualquer CNPJ: cadastro, sócios, processos judiciais, sanções, contratos com o governo, infraestrutura do site e muito mais.

---

## Fontes de dados

| Fonte | O que coleta |
|---|---|
| BrasilAPI / CNPJá / ReceitaWS | Cadastro, QSA, CNAE, endereço, contato |
| Portal da Transparência (CGU) | Sanções CEIS/CNEP/CEPIM, contratos, licitações, convênios, obras, cartão corporativo, servidores públicos |
| DataJud (CNJ) | Processos judiciais em todos os TJs, TRTs e TRFs — trabalhistas, fiscais, cíveis |
| Registro.br RDAP | Domínio .com.br, registrante, e-mail, nameservers, datas |
| Google PageSpeed | Performance e velocidade do site |
| BNDES Open Data | Financiamentos públicos recebidos |
| PNCP | Contratos ativos com governo federal |
| IBGE | Dados do município |
| theHarvester | E-mails e subdomínios indexados (OSINT) |
| Shodan | IPs públicos, portas abertas, CVEs *(requer API key)* |
| Google Dorks | Links de busca gerados automaticamente para investigação manual |

---

## Instalação

```bash
git clone https://github.com/seu-usuario/lead-hunter-br
cd lead-hunter-br
pip install rich requests
```

Para Shodan (opcional):
```bash
pip install shodan
```

Para theHarvester (opcional, BlackArch/Kali já inclui):
```bash
pip install theHarvester
```

---

## Configuração

Abra o arquivo `lead_hunter.py` e preencha as chaves no topo:

```python
SHODAN_API_KEY        = "sua_chave"   # https://account.shodan.io
TRANSPARENCIA_API_KEY = "sua_chave"   # https://portaldatransparencia.gov.br/api-de-dados/cadastrar-email
PAGESPEED_API_KEY     = "sua_chave"   # https://console.cloud.google.com
```

As três são **gratuitas**. O app funciona sem elas, mas com as chaves os limites de requisição aumentam.

---

## Uso

```bash
python lead_hunter.py
```

### Comandos disponíveis

| Comando | Descrição |
|---|---|
| `cnpj` | Consulta básica por CNPJ |
| `osint` | CNPJ + enriquecimento completo (Transparência, DataJud, WHOIS, site...) |
| `radiografia` | Igual ao `osint`, mas salva um relatório HTML completo |
| `lote` | Processa um arquivo `.txt` com vários CNPJs, um por linha |
| `cep` | Busca endereço por CEP |
| `leads` | Lista todos os leads coletados na sessão |
| `filtro` | Filtra leads por UF, município, CNAE, situação, e-mail, telefone, sanções |
| `dorks` | Abre as buscas no navegador ou exporta HTML clicável |
| `export` | Exporta para CSV, JSON ou HTML |
| `config` | Atualiza API keys sem reiniciar |
| `limpar` | Limpa a sessão atual |

---

## O que o OSINT retorna

Para cada empresa consultada via `osint` ou `radiografia`:

**Cadastro**
- CNPJ, razão social, nome fantasia, situação, abertura, natureza jurídica, porte, capital social
- CNAE principal com descrição
- Simples Nacional / MEI
- E-mail, telefone e endereço completo
- QSA completo — nome, qualificação, CPF/CNPJ e data de entrada de cada sócio

**Portal da Transparência**
- Sanções CEIS (empresa inidônea/suspensa)
- Sanções CNEP (empresa punida)
- CEPIM (impedida de receber verbas federais)
- Contratos e licitações federais
- Convênios e obras públicas
- Gastos de cartão corporativo do governo
- Verifica se algum sócio é servidor público federal

**Processos judiciais (DataJud/CNJ)**
- Busca em TJSP, TJRJ, TJMG, TJRS, TJPR, TJSC, TRT2 e TRF3
- Categoriza em trabalhistas, execuções fiscais e cíveis
- Busca também pelo nome dos sócios

**Site da empresa**
- SSL/HTTPS ativo ou não
- Tecnologias detectadas (WordPress, Shopify, React, PHP, Bootstrap, etc.)
- Presença de Google Analytics e Facebook Pixel
- Score de performance via PageSpeed
- **Sinais de dor** gerados automaticamente com base no que falta

**WHOIS**
- Registrante do domínio .com.br
- E-mail técnico de contato
- Datas de criação e expiração
- Nameservers

**Mapeamento de dores por CNAE**
- Identifica o setor da empresa e lista as dores típicas daquele mercado
- Sugere oportunidades de venda com base no segmento

**OSINT**
- E-mails e subdomínios coletados pelo theHarvester
- IPs públicos, portas abertas e CVEs via Shodan

**Google Dorks**
- Links prontos para busca no Google e Bing: LinkedIn da empresa, perfis dos sócios, PDFs expostos, planilhas públicas, Reclame Aqui, Jusbrasil, Diário Oficial, notícias, redes sociais

---

## Exportação

- **CSV** — compatível com Excel, Google Sheets e CRMs. Inclui todos os campos OSINT como colunas.
- **JSON** — estrutura completa para integração com outros sistemas
- **HTML (dorks)** — página com tema escuro, todos os links clicáveis, organizados por empresa
- **HTML (radiografia)** — relatório visual completo de uma empresa, com grid de cards para cada seção

---

## Arquitetura

O projeto usa POO com classes bem separadas por responsabilidade:

```
CLI
├── LeadSession          — armazena leads na memória durante a sessão
├── CNPJCollector        — BrasilAPI / CNPJá / ReceitaWS
├── Enricher             — orquestra todos os coletores
│   ├── TransparenciaCollector
│   ├── DataJudCollector
│   ├── WhoisCollector
│   ├── SiteAnalyzer
│   ├── BNDESCollector
│   ├── PNCPCollector
│   ├── IBGECollector
│   ├── HarvesterCollector
│   ├── ShodanCollector
│   └── DorksGenerator
├── Exporter             — CSV / JSON / HTML
└── Display              — interface rich no terminal
```

Cada coletor herda de `BaseCollector` e pode ser usado de forma independente.

---

## Arquivo de lote

Para consultar vários CNPJs de uma vez, crie um `.txt` com um por linha:

```
11222333000181
44555666000190
00394460005887
```

Use o comando `lote` e aponte para o arquivo. O app pergunta se quer enriquecer cada um (mais lento) ou só fazer a consulta básica (mais rápido).

---

## Mapeamento de setores

O app já tem mapeamento de dores e oportunidades para os seguintes CNAEs:

- Contabilidade (6920)
- Construção civil (4120)
- Incorporação imobiliária (4110)
- Supermercado / varejo (4711, 4713)
- Saúde — clínicas e hospitais (8630, 8621)
- Transporte (4921, 4930)
- Advocacia (6911)
- Educação (8511, 8512)
- Restaurantes (5611)
- Desenvolvimento de software / TI (6201, 6202)
- Consultoria (7490)

Para CNAEs fora da lista, usa um mapeamento genérico.

---

## Dependências

```
rich>=13.0.0
requests>=2.28.0
shodan          (opcional)
```

---

## Aviso legal

Todos os dados coletados são **públicos**, provenientes de APIs abertas do governo brasileiro e fontes de acesso livre. Use com responsabilidade e em conformidade com a LGPD.

---

## Licença

MIT
