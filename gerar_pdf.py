"""
gerar_pdf.py
Gera o relatório de entrega da Atividade 4 em PDF usando ReportLab.
Suporte completo a Unicode / português com acentuação.
"""
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, KeepTogether
)
from reportlab.platypus.flowables import HRFlowable

# ── Paleta de cores ─────────────────────────────────────────────────────────
AZUL_ESCURO  = colors.HexColor("#0A3A60")
TEAL         = colors.HexColor("#00B5B8")
CINZA_CLARO  = colors.HexColor("#F4F6F8")
CINZA_TEXTO  = colors.HexColor("#333333")
CINZA_SUB    = colors.HexColor("#6C7A89")
LINK_COLOR   = colors.HexColor("#007791")

PAGE_W, PAGE_H = A4


def build_styles():
    base = getSampleStyleSheet()

    styles = {
        "title": ParagraphStyle(
            "title",
            fontName="Helvetica-Bold",
            fontSize=20,
            textColor=AZUL_ESCURO,
            spaceAfter=4,
            leading=24,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=TEAL,
            spaceAfter=12,
            leading=16,
        ),
        "section": ParagraphStyle(
            "section",
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=AZUL_ESCURO,
            spaceBefore=14,
            spaceAfter=6,
            leading=15,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=10,
            textColor=CINZA_TEXTO,
            spaceAfter=6,
            leading=14,
        ),
        "field_label": ParagraphStyle(
            "field_label",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=CINZA_TEXTO,
        ),
        "field_value": ParagraphStyle(
            "field_value",
            fontName="Helvetica",
            fontSize=10,
            textColor=CINZA_TEXTO,
        ),
        "link": ParagraphStyle(
            "link",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=LINK_COLOR,
        ),
        "footer": ParagraphStyle(
            "footer",
            fontName="Helvetica",
            fontSize=8,
            textColor=CINZA_SUB,
            alignment=TA_CENTER,
        ),
    }
    return styles


def build_header_banner():
    """Tabela de topo que simula o banner azul com texto branco."""
    data = [["AVALIAÇÃO FINAL — GESTÃO DE DADOS PÚBLICOS"]]
    t = Table(data, colWidths=[PAGE_W - 40 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), AZUL_ESCURO),
        ("TEXTCOLOR",   (0, 0), (-1, -1), colors.white),
        ("FONTNAME",    (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def build_identity_table(styles):
    """Tabela de identificação (label: value)."""
    link = "https://seia-pr-licitacoes-ti.streamlit.app/"
    rows = [
        ("Estudante:",         "Gylian (Gy)"),
        ("Órgão:",             "Secretaria de Inovação e Inteligência Artificial (SEIA-PR)"),
        ("Diretoria:",         "Diretoria de Inteligência Artificial (DIA)"),
        ("Dashboard (link):",  f'<link href="{link}" color="#007791">{link}</link>'),
    ]
    table_data = []
    for label, value in rows:
        p_label = Paragraph(label, styles["field_label"])
        p_value = Paragraph(value, styles["link"] if "link" in value else styles["field_value"])
        table_data.append([p_label, p_value])

    t = Table(table_data, colWidths=[45 * mm, PAGE_W - 40 * mm - 45 * mm])
    t.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
    ]))
    return t


def build_kpi_table():
    """Tabela visual de KPIs do dashboard."""
    kpis = [
        ("R$ 213,4 M", "Total Investido em TI\n(contratos homologados)"),
        ("250",         "Licitações Analisadas\n(período 2021-2026)"),
        ("74,1%",       "Taxa de Sucesso\n(Homologados / Finalizados)"),
        ("7",           "Fornecedores Ativos\ncom contratos firmados"),
    ]
    header = [
        Paragraph("<b>Indicador</b>", ParagraphStyle("kh", fontName="Helvetica-Bold",
                  fontSize=9, textColor=colors.white, alignment=TA_CENTER)),
        Paragraph("<b>Valor</b>", ParagraphStyle("kh", fontName="Helvetica-Bold",
                  fontSize=9, textColor=colors.white, alignment=TA_CENTER)),
    ]
    rows = [header]
    for val, label in kpis:
        rows.append([
            Paragraph(label.replace("\n", "<br/>"),
                      ParagraphStyle("kl", fontName="Helvetica", fontSize=9,
                                     textColor=CINZA_TEXTO)),
            Paragraph(f"<b>{val}</b>",
                      ParagraphStyle("kv", fontName="Helvetica-Bold", fontSize=14,
                                     textColor=AZUL_ESCURO, alignment=TA_CENTER)),
        ])

    col_w = (PAGE_W - 40 * mm) / 2
    t = Table(rows, colWidths=[col_w, col_w])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), AZUL_ESCURO),
        ("BACKGROUND",    (0, 1), (-1, -1), CINZA_CLARO),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#DCDCDC")),
        ("ALIGN",         (1, 0), (1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    return t


def criar_relatorio_pdf():
    output_path = "Entrega_Atividade_4.pdf"
    today = datetime.datetime.now().strftime("%d/%m/%Y")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=25 * mm,
        title="Entrega Atividade 4 — Dashboard de Licitações de TI",
        author="Gylian (SEIA-PR)",
    )

    s = build_styles()
    story = []

    # ── Banner de topo ────────────────────────────────────────────────────────
    story.append(build_header_banner())
    story.append(Spacer(1, 8 * mm))

    # ── Título ────────────────────────────────────────────────────────────────
    story.append(Paragraph("Relatório de Entrega: Dashboard de Licitações de TI", s["title"]))
    story.append(Paragraph("Avaliação Final — Gestão de Dados Públicos", s["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=2, color=AZUL_ESCURO, spaceAfter=8))

    # ── Identificação ─────────────────────────────────────────────────────────
    story.append(build_identity_table(s))
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#DCDCDC"), spaceAfter=6))

    # ── Visão Geral dos KPIs ─────────────────────────────────────────────────
    story.append(Paragraph("Resumo dos Indicadores do Painel", s["section"]))
    story.append(build_kpi_table())
    story.append(Spacer(1, 8 * mm))

    # ── Seção 1: Introdução ──────────────────────────────────────────────────
    story.append(Paragraph("1. Introdução e Contexto da Base", s["section"]))
    story.append(Paragraph(
        "O presente relatório acompanha a publicação do dashboard de Compras Públicas de Tecnologia "
        "do Estado do Paraná, construído em substituição à ferramenta PowerBI utilizando o ecossistema "
        "Python (Streamlit e Plotly). Esta solução visa apoiar a Diretoria de Inteligência Artificial e a "
        "assessoria jurídica da Secretaria de Inovação e Inteligência Artificial (SEIA-PR) na tomada de "
        "decisões estratégicas de modelagem contratual para o programa estadual TRANSFORMA PARANÁ.",
        s["body"]
    ))
    story.append(Paragraph(
        "A base de dados utilizada é a Base de Licitações e Contratos do Estado do Paraná, gerida e mantida "
        "pela Controladoria Geral do Estado (CGE-PR) e pela Secretaria de Estado da Administração e da "
        "Previdência (SEAP). O conjunto de dados reflete os trâmites transacionais do Sistema de Gestão de "
        "Materiais e Serviços (GMS) e é disponibilizado no Portal de Dados Abertos do Paraná "
        "(dadosabertos.pr.gov.br) com periodicidade de atualização diária.",
        s["body"]
    ))

    # ── Seção 2: Tratamentos ─────────────────────────────────────────────────
    story.append(Paragraph("2. Principais Tratamentos de Dados Efetuados", s["section"]))
    tratamentos = [
        ("<b>1. Seleção Temática (Filtro por Objeto):</b> Aplicada rotina de filtragem textual por "
         "termos-chave ('nuvem', 'inteligência artificial', 'chatbot', 'software', 'datacenter') para "
         "restringir a análise às compras de base tecnológica, eliminando categorias genéricas como "
         "simples 'Serviços de TI' sem especificação."),
        ("<b>2. Tratamento de Valores Ausentes:</b> Processos classificados como 'Fracassado', 'Deserto' "
         "ou 'Revogado' tiveram seus valores finais zerados para evitar distorções no cálculo financeiro. "
         "Processos 'Em Andamento' mantiveram valores nulos, devidamente rotulados no painel."),
        ("<b>3. Padronização Organizacional:</b> Nomes dos órgãos demandantes normalizados (grafia única "
         "para SEIA, Celepar, SESA, CGE etc.) e datas de homologação convertidas para o padrão datetime, "
         "viabilizando a extração do ano e a correta ordenação cronológica das séries temporais."),
        ("<b>4. Conformidade com a LGPD:</b> Dados pessoais identificáveis omitidos (CPFs de MEIs, "
         "endereços residenciais), mantendo apenas informações corporativas públicas — Razão Social e "
         "CNPJ das empresas vencedoras — em linha com a Lei nº 13.709/2018 e a Lei de Acesso à Informação."),
    ]
    for t in tratamentos:
        story.append(Paragraph(t, s["body"]))

    # ── Seção 3: Indicadores ─────────────────────────────────────────────────
    story.append(Paragraph("3. Indicadores Desenvolvidos no Dashboard", s["section"]))
    indicadores = [
        ("<b>Cartões de KPI:</b> Volume Financeiro Total Investido (homologações), Quantidade de Processos "
         "Licitatórios, Taxa Geral de Sucesso (%) e número de Fornecedores Ativos com contratos firmados."),
        ("<b>Visual 1 — Taxa de Sucesso por Modalidade:</b> Gráfico de barras horizontal demonstrando a "
         "proporção de licitações homologadas versus desertas/fracassadas por modalidade. Revela a "
         "atratividade de cada formato de edital para o mercado de tecnologia de inovação."),
        ("<b>Visual 2 — Volume de Investimento por Órgão:</b> Gráfico de barras horizontal identificando "
         "quais secretarias ou autarquias alocam maiores recursos em inovação, auxiliando na identificação "
         "de projetos transversais entre Celepar, SESA e SEIA."),
        ("<b>Visual 3 — Evolução Anual de Gastos em TI:</b> Gráfico de área monitorando o crescimento "
         "anual das contratações tecnológicas no período de 2021 a 2026, permitindo avaliar a escala "
         "temporal e a aderência das compras estaduais às diretrizes plurianuais do Governo do Paraná."),
        ("<b>Visual 4 — Concentração de Fornecedores:</b> Gráfico de rosca evidenciando o market share "
         "financeiro dos principais players, apontando o grau de dependência tecnológica (vendor lock-in) "
         "e embasando políticas de diversificação do ecossistema fornecedor."),
    ]
    for ind in indicadores:
        story.append(Paragraph(ind, s["body"]))

    # ── Seção 4: Apoio à Decisão ─────────────────────────────────────────────
    story.append(Paragraph("4. Apoio à Tomada de Decisão Pública na SEIA-PR", s["section"]))
    decisao = [
        ("<b>1. Mitigação de Licitações Desertas:</b> Ao expor que modalidades tradicionais (ex: Pregão "
         "por menor preço) apresentam altas taxas de fracasso para objetos de IA complexos, o setor "
         "jurídico dispõe de subsídios empíricos para justificar o uso de regimes inovadores, como o "
         "Diálogo Competitivo (Lei nº 14.133/2021) e o Marco Legal das Startups (LC nº 182/2021)."),
        ("<b>2. Análise de Risco de Lock-in Tecnológico:</b> O indicador de concentração de fornecedores "
         "alerta sobre dependência tecnológica de poucos players, embasando a criação de políticas de "
         "fomento para diversificar o ecossistema e atrair startups locais para as compras públicas."),
        ("<b>3. Planejamento de Sinergias Financeiras:</b> Mapeando investimentos em TI por secretaria, a "
         "Diretoria de IA pode identificar que órgãos distintos adquirem soluções semelhantes (ex: chatbots "
         "individuais) e coordenar compras corporativas integradas, gerando economia de escala e maior "
         "governança no programa TRANSFORMA PARANÁ."),
    ]
    for d in decisao:
        story.append(Paragraph(d, s["body"]))

    # ── Rodapé de encerramento ────────────────────────────────────────────────
    story.append(Spacer(1, 10 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#DCDCDC")))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        f"Secretaria de Inovação e Inteligência Artificial do Paraná (SEIA-PR) — "
        f"Diretoria de Inteligência Artificial | Documento gerado em {today}",
        s["footer"]
    ))

    doc.build(story)
    print(f"Relatório PDF criado com sucesso: '{output_path}'.")


if __name__ == "__main__":
    criar_relatorio_pdf()
