from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import pandas as pd
import json
import os

app = FastAPI(title="SEIA-PR | Dashboard de Licitações de TI")

import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "licitacoes_tecnologia_pr.csv")

# Adicionar o diretório base ao sys.path para garantir importações relativas robustas no Render
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Garantir que a base de dados existe
if not os.path.exists(CSV_FILE):
    try:
        from gerar_dados import gerar_dados_licitacoes
        gerar_dados_licitacoes(250)
    except Exception as e:
        print(f"Aviso: Erro ao importar gerar_dados. Gerando dados simplificados em app.py... Detalhe: {e}")
        # Gerador de fallback simplificado integrado para máxima segurança no Render
        import random
        from datetime import datetime, timedelta
        
        orgaos = ["SEIA", "Celepar", "SESA", "SEAP", "CGE", "DETRAN", "SEED", "SETI"]
        objetos = ["Licenciamento de IA para análise documental - Fase 1", "Contratação de Nuvem Híbrida - Fase 2", "Serviços de Chatbot E-Gov - Fase 3", "Consultoria LGPD - Fase 1"]
        modalidades = ["Pregão Eletrônico", "Inexigibilidade de Licitação", "Dispensa de Licitação", "Diálogo Competitivo", "Concorrência Pública"]
        situacoes = ["Homologado", "Homologado", "Deserto", "Fracassado", "Revogado", "Em Andamento"]
        empresas = [("TechPar Soluções Ltda", "12.345.678/0001-90"), ("Inova Sul S.A.", "98.765.432/0001-10"), ("Inteligência Global ME", "45.678.901/0001-23")]
        
        dados = []
        data_inicio = datetime(2021, 1, 1)
        for i in range(250):
            ano_processo = random.randint(21, 26)
            num_seq = random.randint(100000, 999999)
            numero_processo = f"{ano_processo}.{num_seq}-{random.randint(0, 9)}"
            orgao = random.choice(orgaos)
            objeto = random.choice(objetos)
            modalidade = random.choice(modalidades)
            valor_max = round(random.uniform(50000, 3000000), 2)
            situacao = random.choice(situacoes)
            
            if situacao == "Homologado":
                valor_hom = round(valor_max * random.uniform(0.75, 0.95), 2)
                empresa, cnpj = random.choice(empresas)
            elif situacao == "Em Andamento":
                valor_hom = None
                empresa, cnpj = "N/A", "N/A"
            else:
                valor_hom = 0.0
                empresa, cnpj = "N/A", "N/A"
                
            data_evento = data_inicio + timedelta(days=random.randint(0, 1900))
            if data_evento > datetime.now():
                data_evento = datetime.now() - timedelta(days=random.randint(1, 30))
                
            dados.append({
                "Numero_Processo": numero_processo,
                "Orgao_Demandante": orgao,
                "Objeto": objeto,
                "Modalidade": modalidade,
                "Valor_Maximo_Estimado": valor_max,
                "Valor_Homologado": valor_hom,
                "Situacao": situacao,
                "Razao_Social_Vencedora": empresa,
                "CNPJ_Vencedor": cnpj,
                "Data_Evento": data_evento.strftime("%Y-%m-%d")
            })
        
        df_fb = pd.DataFrame(dados)
        df_fb.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")
        print("Dataset de fallback gerado com sucesso.")

def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        df["Data_Evento"] = pd.to_datetime(df["Data_Evento"])
        df["Ano"] = df["Data_Evento"].dt.year
        # Substituir NaNs em todas as colunas para evitar problemas de serialização JSON
        df = df.fillna({
            "Valor_Homologado": 0.0,
            "Valor_Maximo_Estimado": 0.0,
            "Razao_Social_Vencedora": "N/A",
            "CNPJ_Vencedor": "N/A",
            "Objeto": "",
            "Numero_Processo": "",
            "Orgao_Demandante": "",
            "Modalidade": "",
            "Situacao": ""
        })
        return df
    return pd.DataFrame()

@app.get("/api/metadata")
def get_metadata():
    df = load_data()
    if df.empty:
        return {"anos": [], "orgaos": [], "modalidades": [], "situacoes": []}
    
    anos = sorted(df["Ano"].unique().tolist())
    orgaos = sorted(df["Orgao_Demandante"].unique().tolist())
    modalidades = sorted(df["Modalidade"].unique().tolist())
    situacoes = sorted(df["Situacao"].unique().tolist())
    
    return {
        "anos": anos,
        "orgaos": orgaos,
        "modalidades": modalidades,
        "situacoes": situacoes
    }

@app.get("/api/data")
def get_data(
    ano_min: int = Query(None),
    ano_max: int = Query(None),
    orgaos: str = Query(None), # Comma separated
    modalidades: str = Query(None), # Comma separated
    situacoes: str = Query(None) # Comma separated
):
    df = load_data()
    if df.empty:
        return {"summary": {}, "charts": {}, "records": []}
    
    # Aplicar filtros
    if ano_min is not None:
        df = df[df["Ano"] >= ano_min]
    if ano_max is not None:
        df = df[df["Ano"] <= ano_max]
    
    if orgaos:
        orgaos_list = orgaos.split(",")
        df = df[df["Orgao_Demandante"].isin(orgaos_list)]
    
    if modalidades:
        modalidades_list = modalidades.split(",")
        df = df[df["Modalidade"].isin(modalidades_list)]
        
    if situacoes:
        situacoes_list = situacoes.split(",")
        df = df[df["Situacao"].isin(situacoes_list)]
        
    # --- Calcular Métricas (KPIs) ---
    investimento_total = float(df[df["Situacao"] == "Homologado"]["Valor_Homologado"].sum())
    total_processos = int(df["Numero_Processo"].nunique())
    
    # Taxa de sucesso (Homologado / Finalizados)
    processos_finalizados = df[df["Situacao"].isin(["Homologado", "Deserto", "Fracassado", "Revogado"])]
    num_finalizados = int(processos_finalizados["Numero_Processo"].nunique())
    num_homologados = int(df[df["Situacao"] == "Homologado"]["Numero_Processo"].nunique())
    taxa_sucesso = float((num_homologados / num_finalizados * 100)) if num_finalizados > 0 else 0.0
    
    fornecedores_unicos = int(df[df["Razao_Social_Vencedora"] != "N/A"]["Razao_Social_Vencedora"].nunique())
    
    summary = {
        "investimento_total": investimento_total,
        "total_processos": total_processos,
        "taxa_sucesso": round(taxa_sucesso, 1),
        "fornecedores_ativos": fornecedores_unicos
    }
    
    # --- Gráfico 1: Taxa de Sucesso por Modalidade ---
    chart_modality = []
    if not processos_finalizados.empty:
        # Calcular taxa de sucesso para cada modalidade
        mod_groups = processos_finalizados.groupby("Modalidade")
        for name, group in mod_groups:
            total_g = group["Numero_Processo"].nunique()
            homologados_g = group[group["Situacao"] == "Homologado"]["Numero_Processo"].nunique()
            taxa_g = round((homologados_g / total_g * 100), 1) if total_g > 0 else 0.0
            chart_modality.append({"modalidade": name, "taxa_sucesso": taxa_g})
        # Ordenar por taxa
        chart_modality = sorted(chart_modality, key=lambda x: x["taxa_sucesso"])
        
    # --- Gráfico 2: Volume de Investimento por Órgão ---
    chart_orgao = []
    df_homologado = df[df["Situacao"] == "Homologado"]
    if not df_homologado.empty:
        org_groups = df_homologado.groupby("Orgao_Demandante")["Valor_Homologado"].sum().reset_index()
        org_groups = org_groups.sort_values(by="Valor_Homologado", ascending=True)
        for _, row in org_groups.iterrows():
            chart_orgao.append({"orgao": row["Orgao_Demandante"], "valor": float(row["Valor_Homologado"])})
            
    # --- Gráfico 3: Evolução Anual de Gastos ---
    chart_evolution = []
    if not df_homologado.empty:
        year_groups = df_homologado.groupby("Ano")["Valor_Homologado"].sum().reset_index()
        year_groups = year_groups.sort_values(by="Ano")
        for _, row in year_groups.iterrows():
            chart_evolution.append({"ano": int(row["Ano"]), "valor": float(row["Valor_Homologado"])})
            
    # --- Gráfico 4: Concentração de Fornecedores ---
    chart_vendors = []
    if not df_homologado.empty:
        vendor_groups = df_homologado.groupby("Razao_Social_Vencedora")["Valor_Homologado"].sum().reset_index()
        vendor_groups = vendor_groups.sort_values(by="Valor_Homologado", ascending=False)
        top_n = 5
        if len(vendor_groups) > top_n:
            top_df = vendor_groups.head(top_n)
            others_val = float(vendor_groups.iloc[top_n:]["Valor_Homologado"].sum())
            for _, row in top_df.iterrows():
                chart_vendors.append({"fornecedor": row["Razao_Social_Vencedora"], "valor": float(row["Valor_Homologado"])})
            chart_vendors.append({"fornecedor": "Outros Fornecedores", "valor": others_val})
        else:
            for _, row in vendor_groups.iterrows():
                chart_vendors.append({"fornecedor": row["Razao_Social_Vencedora"], "valor": float(row["Valor_Homologado"])})
                
    # --- Preparar Registros para a Tabela ---
    records = []
    # Copiar df para evitar problemas de modificação
    df_display = df.copy()
    # Ordenar por data mais recente
    df_display = df_display.sort_values(by="Data_Evento", ascending=False)
    
    for _, row in df_display.iterrows():
        records.append({
            "processo": row["Numero_Processo"],
            "orgao": row["Orgao_Demandante"],
            "objeto": row["Objeto"],
            "modalidade": row["Modalidade"],
            "valor_estimado": float(row["Valor_Maximo_Estimado"]),
            "valor_homologado": float(row["Valor_Homologado"]),
            "situacao": row["Situacao"],
            "fornecedor": row["Razao_Social_Vencedora"],
            "data": row["Data_Evento"].strftime("%d/%m/%Y")
        })
        
    return {
        "summary": summary,
        "charts": {
            "modality": chart_modality,
            "orgao": chart_orgao,
            "evolution": chart_evolution,
            "vendors": chart_vendors
        },
        "records": records
    }

@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    html_content = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEIA-PR | Dashboard de Licitações de TI</title>
    <!-- Google Fonts: Outfit -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <!-- Plotly.js CDN -->
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
    <style>
        :root {
            --primary-gradient: linear-gradient(135deg, #0A3A60 0%, #007791 50%, #00B5B8 100%);
            --sidebar-gradient: linear-gradient(180deg, #0A3A60 0%, #005571 100%);
            --primary-color: #0A3A60;
            --accent-color: #00B5B8;
            --bg-color: #F4F7F9;
            --card-bg: #FFFFFF;
            --text-color: #2F3E46;
            --text-muted: #6C7A89;
            --border-color: #E2E8F0;
            --success-color: #2E7D32;
            --warning-color: #F9A825;
            --danger-color: #C62828;
            --shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            --transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            display: flex;
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* --- SIDEBAR --- */
        aside {
            width: 320px;
            background: var(--sidebar-gradient);
            color: white;
            padding: 2rem 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 2rem;
            flex-shrink: 0;
            box-shadow: 4px 0 20px rgba(0,0,0,0.1);
            z-index: 10;
        }

        .sidebar-brand {
            background: rgba(255, 255, 255, 0.1);
            padding: 1rem 1.25rem;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.15);
            text-align: center;
        }

        .sidebar-brand h1 {
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        .sidebar-brand p {
            font-size: 0.8rem;
            opacity: 0.8;
            margin-top: 0.25rem;
        }

        .filter-section {
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
            flex-grow: 1;
            overflow-y: auto;
            padding-right: 0.25rem;
        }

        .filter-section::-webkit-scrollbar {
            width: 4px;
        }
        .filter-section::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
        }

        .filter-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .filter-title {
            font-size: 0.9rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 0.25rem;
        }

        /* Checkbox lists */
        .checkbox-list {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 0.75rem;
            max-height: 140px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }

        .checkbox-list::-webkit-scrollbar {
            width: 4px;
        }
        .checkbox-list::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 4px;
        }

        .checkbox-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.85rem;
            cursor: pointer;
            user-select: none;
        }

        .checkbox-item input {
            accent-color: var(--accent-color);
            cursor: pointer;
            width: 15px;
            height: 15px;
        }

        /* Slider range input styles */
        .range-inputs {
            display: flex;
            gap: 0.5rem;
        }

        .range-inputs select {
            flex: 1;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 6px;
            color: white;
            padding: 0.5rem;
            font-family: inherit;
            font-size: 0.85rem;
            outline: none;
            cursor: pointer;
        }

        .range-inputs select option {
            background: #0A3A60;
            color: white;
        }

        /* --- MAIN CONTENT --- */
        main {
            flex-grow: 1;
            padding: 2.5rem;
            display: flex;
            flex-direction: column;
            gap: 2rem;
            max-width: 1600px;
            margin: 0 auto;
            width: calc(100vw - 320px);
            overflow-y: auto;
        }

        header.hero {
            background: var(--primary-gradient);
            color: white;
            padding: 2.5rem;
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(10, 58, 96, 0.15);
            position: relative;
            overflow: hidden;
        }

        header.hero::after {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 300px;
            height: 100%;
            background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0) 70%);
            pointer-events: none;
        }

        header h2 {
            font-size: 2.25rem;
            font-weight: 800;
            letter-spacing: -0.5px;
        }

        header p.subtitle {
            font-size: 1.05rem;
            opacity: 0.9;
            margin-top: 0.5rem;
            font-weight: 300;
        }

        .badge-container {
            margin-top: 1.25rem;
        }

        .badge {
            background-color: rgba(255, 255, 255, 0.18);
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: white;
            padding: 6px 14px;
            border-radius: 50px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-block;
        }

        /* --- KPI ROW --- */
        .kpi-container {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1.5rem;
        }

        .kpi-card {
            background: var(--card-bg);
            border-radius: 14px;
            padding: 1.5rem;
            box-shadow: var(--shadow);
            border-left: 5px solid var(--primary-color);
            transition: var(--transition);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .kpi-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
        }

        .kpi-title {
            font-size: 0.85rem;
            text-transform: uppercase;
            font-weight: 600;
            color: var(--text-muted);
            letter-spacing: 0.5px;
        }

        .kpi-value {
            font-size: 2.25rem;
            font-weight: 700;
            color: var(--primary-color);
            margin: 0.5rem 0;
            line-height: 1.1;
        }

        .kpi-footer {
            font-size: 0.75rem;
            color: var(--text-muted);
        }

        /* Border Left Colors for KPIs */
        .kpi-card.kpi-total-investido { border-left-color: var(--success-color); }
        .kpi-card.kpi-total-licitacoes { border-left-color: var(--primary-color); }
        .kpi-card.kpi-taxa-sucesso { border-left-color: var(--accent-color); }
        .kpi-card.kpi-fornecedores { border-left-color: var(--warning-color); }

        /* --- CHART GRID --- */
        .chart-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1.5rem;
        }

        .chart-card {
            background: var(--card-bg);
            border-radius: 14px;
            padding: 1.5rem;
            box-shadow: var(--shadow);
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .chart-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .chart-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--primary-color);
        }

        .chart-container {
            width: 100%;
            height: 330px;
            position: relative;
        }

        /* --- DATA TABLE --- */
        .data-section {
            background: var(--card-bg);
            border-radius: 14px;
            padding: 1.5rem;
            box-shadow: var(--shadow);
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }

        .table-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .table-title-container {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }

        .table-title {
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--primary-color);
        }

        .table-subtitle {
            font-size: 0.85rem;
            color: var(--text-muted);
        }

        .search-container {
            display: flex;
            align-items: center;
            background: var(--bg-color);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 0.5rem 0.75rem;
            width: 300px;
            gap: 0.5rem;
        }

        .search-container input {
            border: none;
            background: transparent;
            outline: none;
            font-family: inherit;
            font-size: 0.9rem;
            width: 100%;
            color: var(--text-color);
        }

        .export-btn {
            background: var(--primary-color);
            color: white;
            border: none;
            padding: 0.6rem 1.25rem;
            border-radius: 8px;
            font-family: inherit;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            transition: var(--transition);
            box-shadow: 0 4px 10px rgba(10, 58, 96, 0.15);
        }

        .export-btn:hover {
            background: #005571;
            transform: translateY(-1px);
        }

        .table-wrapper {
            overflow-x: auto;
            max-height: 400px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
        }

        .table-wrapper::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        .table-wrapper::-webkit-scrollbar-thumb {
            background: #CBD5E1;
            border-radius: 4px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.9rem;
        }

        thead {
            background-color: var(--bg-color);
            position: sticky;
            top: 0;
            z-index: 1;
            border-bottom: 2px solid var(--border-color);
        }

        th {
            padding: 0.85rem 1rem;
            font-weight: 600;
            color: var(--primary-color);
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        td {
            padding: 0.85rem 1rem;
            border-bottom: 1px solid var(--border-color);
            color: var(--text-color);
            max-width: 300px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        tr:last-child td {
            border-bottom: none;
        }

        tr:hover td {
            background-color: rgba(0, 181, 184, 0.03);
        }

        /* Status tags */
        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .status-homologado { background-color: #E8F5E9; color: var(--success-color); }
        .status-em-andamento { background-color: #FFF9C4; color: #F57F17; }
        .status-deserto { background-color: #ECEFF1; color: var(--text-muted); }
        .status-fracassado, .status-revogado { background-color: #FFEBEE; color: var(--danger-color); }

        /* Empty state style */
        .no-data {
            text-align: center;
            padding: 3rem;
            color: var(--text-muted);
            font-size: 1rem;
        }

        /* --- FOOTER --- */
        footer {
            text-align: center;
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-top: 2rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--border-color);
            line-height: 1.6;
        }

        /* --- RESPONSIVENESS --- */
        @media (max-width: 1200px) {
            body {
                flex-direction: column;
            }
            aside {
                width: 100%;
                height: auto;
            }
            main {
                width: 100%;
                padding: 1.5rem;
            }
            .kpi-container {
                grid-template-columns: repeat(2, 1fr);
            }
            .chart-grid {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 768px) {
            .kpi-container {
                grid-template-columns: 1fr;
            }
            header.hero {
                padding: 1.5rem;
            }
            header h2 {
                font-size: 1.75rem;
            }
        }
    </style>
</head>
<body>

    <!-- SIDEBAR -->
    <aside>
        <div class="sidebar-brand">
            <h1>SEIA-PR</h1>
            <p>Diretoria de Inteligência Artificial</p>
        </div>

        <div class="filter-section">
            <h3 style="font-size: 1rem; margin-bottom: 0.5rem; font-weight: 600;">🔍 Filtros Estratégicos</h3>
            
            <!-- Filtro de Anos -->
            <div class="filter-group">
                <span class="filter-title">Período (Anos)</span>
                <div class="range-inputs">
                    <select id="select-ano-min" onchange="updateDashboard()">
                        <!-- Dinâmico -->
                    </select>
                    <span style="align-self: center; opacity: 0.7;">a</span>
                    <select id="select-ano-max" onchange="updateDashboard()">
                        <!-- Dinâmico -->
                    </select>
                </div>
            </div>

            <!-- Filtro de Órgão -->
            <div class="filter-group">
                <span class="filter-title">Órgão Demandante</span>
                <div class="checkbox-list" id="filter-orgao">
                    <!-- Dinâmico -->
                </div>
            </div>

            <!-- Filtro de Modalidade -->
            <div class="filter-group">
                <span class="filter-title">Modalidade Licitatória</span>
                <div class="checkbox-list" id="filter-modalidade">
                    <!-- Dinâmico -->
                </div>
            </div>

            <!-- Filtro de Situação -->
            <div class="filter-group">
                <span class="filter-title">Situação do Certame</span>
                <div class="checkbox-list" id="filter-situacao">
                    <!-- Dinâmico -->
                </div>
            </div>
        </div>
    </aside>

    <!-- MAIN DASHBOARD -->
    <main>
        <!-- Hero Header -->
        <header class="hero">
            <h2>COMPRAS PÚBLICAS DE TECNOLOGIA</h2>
            <p class="subtitle">Secretaria de Inovação e Inteligência Artificial — Governo do Estado do Paraná</p>
            <div class="badge-container">
                <span class="badge">Fonte oficial: Portal de Dados Abertos do Paraná (GMS)</span>
            </div>
        </header>

        <!-- KPI Row -->
        <section class="kpi-container">
            <div class="kpi-card kpi-total-investido">
                <span class="kpi-title">Total Investido (TI)</span>
                <div class="kpi-value" id="kpi-total-investido">R$ 0.00M</div>
                <span class="kpi-footer">Processos homologados</span>
            </div>
            <div class="kpi-card kpi-total-licitacoes">
                <span class="kpi-title">Total de Licitações</span>
                <div class="kpi-value" id="kpi-total-licitacoes">0</div>
                <span class="kpi-footer">No período selecionado</span>
            </div>
            <div class="kpi-card kpi-taxa-sucesso">
                <span class="kpi-title">Taxa de Sucesso</span>
                <div class="kpi-value" id="kpi-taxa-sucesso">0%</div>
                <span class="kpi-footer">Homologados vs. Desertose/Fracassados</span>
            </div>
            <div class="kpi-card kpi-fornecedores">
                <span class="kpi-title">Fornecedores Ativos</span>
                <div class="kpi-value" id="kpi-fornecedores">0</div>
                <span class="kpi-footer">Empresas com contrato firmado</span>
            </div>
        </section>

        <!-- Charts Grid -->
        <section class="chart-grid">
            <!-- Gráfico 1 -->
            <div class="chart-card">
                <div class="chart-header">
                    <span class="chart-title">📊 Taxa de Sucesso por Modalidade Licitatória</span>
                </div>
                <div class="chart-container" id="chart-modality"></div>
            </div>
            <!-- Gráfico 2 -->
            <div class="chart-card">
                <div class="chart-header">
                    <span class="chart-title">🏢 Volume de Investimento por Órgão Demandante</span>
                </div>
                <div class="chart-container" id="chart-orgao"></div>
            </div>
            <!-- Gráfico 3 -->
            <div class="chart-card">
                <div class="chart-header">
                    <span class="chart-title">📈 Evolução Anual de Gastos com TI</span>
                </div>
                <div class="chart-container" id="chart-evolution"></div>
            </div>
            <!-- Gráfico 4 -->
            <div class="chart-card">
                <div class="chart-header">
                    <span class="chart-title">🏆 Concentração de Fornecedores de Tecnologia</span>
                </div>
                <div class="chart-container" id="chart-vendors"></div>
            </div>
        </section>

        <!-- Data Table Section -->
        <section class="data-section">
            <div class="table-header">
                <div class="table-title-container">
                    <span class="table-title">📋 Detalhamento dos Processos Selecionados</span>
                    <span class="table-subtitle">Listagem filtrada para auditoria jurídica e operacional</span>
                </div>
                <div style="display: flex; gap: 1rem; align-items: center; flex-wrap: wrap;">
                    <div class="search-container">
                        <!-- Lupa icon -->
                        <span style="opacity: 0.5;">🔍</span>
                        <input type="text" id="search-input" placeholder="Buscar por Objeto ou Processo..." oninput="filterTableBySearch()">
                    </div>
                    <button class="export-btn" onclick="exportFilteredCSV()">
                        <span>📥</span> Exportar para CSV
                    </button>
                </div>
            </div>

            <div class="table-wrapper">
                <table id="data-table">
                    <thead>
                        <tr>
                            <th>Nº Processo</th>
                            <th>Órgão</th>
                            <th>Objeto do Certame</th>
                            <th>Modalidade</th>
                            <th>Vlr. Estimado</th>
                            <th>Vlr. Homologado</th>
                            <th>Situação</th>
                            <th>Fornecedor Vencedor</th>
                            <th>Data</th>
                        </tr>
                    </thead>
                    <tbody id="table-body">
                        <!-- Dinâmico -->
                    </tbody>
                </table>
            </div>
        </section>

        <!-- Footer -->
        <footer>
            Secretaria de Inovação e Inteligência Artificial do Paraná (SEIA-PR) — Diretoria de Inteligência Artificial<br>
            Desenvolvido com fins pedagógicos para a Avaliação Final de Gestão de Dados Públicos © 2026
        </footer>
    </main>

    <script>
        let fullDataRecords = []; // Armazenar todos os registros filtrados

        // Inicializar os filtros
        async function initFilters() {
            try {
                const response = await fetch('/api/metadata');
                const metadata = await response.json();

                // 1. Povoar Anos
                const selectMin = document.getElementById('select-ano-min');
                const selectMax = document.getElementById('select-ano-max');
                
                selectMin.innerHTML = '';
                selectMax.innerHTML = '';
                
                metadata.anos.forEach((ano, index) => {
                    const optMin = document.createElement('option');
                    optMin.value = ano;
                    optMin.textContent = ano;
                    if(index === 0) optMin.selected = true;
                    selectMin.appendChild(optMin);

                    const optMax = document.createElement('option');
                    optMax.value = ano;
                    optMax.textContent = ano;
                    if(index === metadata.anos.length - 1) optMax.selected = true;
                    selectMax.appendChild(optMax);
                });

                // 2. Povoar Órgãos
                const listOrgao = document.getElementById('filter-orgao');
                listOrgao.innerHTML = '';
                metadata.orgaos.forEach(org => {
                    listOrgao.appendChild(createCheckboxItem(org, 'orgao', true));
                });

                // 3. Povoar Modalidades
                const listModalidade = document.getElementById('filter-modalidade');
                listModalidade.innerHTML = '';
                metadata.modalidades.forEach(mod => {
                    listModalidade.appendChild(createCheckboxItem(mod, 'modalidade', true));
                });

                // 4. Povoar Situações (Pre-selecionar menos as indesejadas)
                const listSituacao = document.getElementById('filter-situacao');
                listSituacao.innerHTML = '';
                metadata.situacoes.forEach(sit => {
                    // Pre-selecionar as mais relevantes
                    const isChecked = ["Homologado", "Deserto", "Fracassado", "Revogado", "Em Andamento"].includes(sit);
                    listSituacao.appendChild(createCheckboxItem(sit, 'situacao', isChecked));
                });

                // Após carregar os metadados, atualizar o dashboard
                updateDashboard();

            } catch (error) {
                console.error("Erro ao carregar filtros iniciais:", error);
            }
        }

        function createCheckboxItem(value, type, checked) {
            const label = document.createElement('label');
            label.className = 'checkbox-item';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = value;
            checkbox.checked = checked;
            checkbox.name = type;
            checkbox.addEventListener('change', updateDashboard);
            
            label.appendChild(checkbox);
            label.appendChild(document.createTextNode(value));
            return label;
        }

        // Buscar dados filtrados da API e redesenhar a tela
        async function updateDashboard() {
            // Coletar anos
            const selectMin = document.getElementById('select-ano-min');
            const selectMax = document.getElementById('select-ano-max');
            const anoMin = selectMin ? selectMin.value : null;
            const anoMax = selectMax ? selectMax.value : null;

            // Coletar Órgãos
            const orgaosChecked = Array.from(document.querySelectorAll('input[name="orgao"]:checked')).map(cb => cb.value);
            // Coletar Modalidades
            const modalidadesChecked = Array.from(document.querySelectorAll('input[name="modalidade"]:checked')).map(cb => cb.value);
            // Coletar Situações
            const situacoesChecked = Array.from(document.querySelectorAll('input[name="situacao"]:checked')).map(cb => cb.value);

            // Construir query string de forma segura
            let params = [];
            if(anoMin && !isNaN(anoMin)) params.push(`ano_min=${anoMin}`);
            if(anoMax && !isNaN(anoMax)) params.push(`ano_max=${anoMax}`);
            if(orgaosChecked.length > 0) params.push(`orgaos=${encodeURIComponent(orgaosChecked.join(','))}`);
            if(modalidadesChecked.length > 0) params.push(`modalidades=${encodeURIComponent(modalidadesChecked.join(','))}`);
            if(situacoesChecked.length > 0) params.push(`situacoes=${encodeURIComponent(situacoesChecked.join(','))}`);

            let query = params.length > 0 ? `?${params.join('&')}` : '';

            try {
                const response = await fetch(`/api/data${query}`);
                const data = await response.json();

                fullDataRecords = data.records || [];

                // 1. Atualizar KPIs
                updateKPIs(data.summary);

                // 2. Renderizar Gráficos
                renderChartModality(data.charts.modality);
                renderChartOrgao(data.charts.orgao);
                renderChartEvolution(data.charts.evolution);
                renderChartVendors(data.charts.vendors);

                // 3. Renderizar Tabela
                renderTable(fullDataRecords);

            } catch (error) {
                console.error("Erro ao buscar dados filtrados:", error);
            }
        }

        function updateKPIs(summary) {
            if(!summary || Object.keys(summary).length === 0) {
                document.getElementById('kpi-total-investido').textContent = "R$ 0.00M";
                document.getElementById('kpi-total-licitacoes').textContent = "0";
                document.getElementById('kpi-taxa-sucesso').textContent = "0%";
                document.getElementById('kpi-fornecedores').textContent = "0";
                return;
            }

            const formattedInvestimento = (summary.investimento_total / 1000000).toFixed(2);
            document.getElementById('kpi-total-investido').textContent = `R$ ${formattedInvestimento}M`;
            document.getElementById('kpi-total-licitacoes').textContent = summary.total_processos.toLocaleString();
            document.getElementById('kpi-taxa-sucesso').textContent = `${summary.taxa_sucesso}%`;
            document.getElementById('kpi-fornecedores').textContent = summary.fornecedores_ativos.toLocaleString();
        }

        // Gráfico 1: Taxa de Sucesso por Modalidade
        function renderChartModality(chartData) {
            const container = document.getElementById('chart-modality');
            if(!chartData || chartData.length === 0) {
                container.innerHTML = '<div class="no-data">Nenhum dado encontrado para os filtros selecionados.</div>';
                return;
            }

            const yValues = chartData.map(item => item.modalidade);
            const xValues = chartData.map(item => item.taxa_sucesso);

            const plotlyData = [{
                type: 'bar',
                x: xValues,
                y: yValues,
                orientation: 'h',
                text: xValues.map(v => `${v}%`),
                textposition: 'outside',
                marker: {
                    color: xValues,
                    colorscale: 'Viridis',
                    reversescale: true
                }
            }];

            const layout = {
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { family: 'Outfit, sans-serif', size: 11, color: '#2F3E46' },
                margin: { l: 155, r: 40, t: 15, b: 30 },
                xaxis: { title: 'Taxa de Sucesso (%)', gridcolor: '#F1F5F9', zeroline: false },
                yaxis: { automargin: true }
            };

            Plotly.newPlot(container, plotlyData, layout, {responsive: true, displayModeBar: false});
        }

        // Gráfico 2: Volume por Órgão
        function renderChartOrgao(chartData) {
            const container = document.getElementById('chart-orgao');
            if(!chartData || chartData.length === 0) {
                container.innerHTML = '<div class="no-data">Sem investimentos homologados para exibir.</div>';
                return;
            }

            const yValues = chartData.map(item => item.orgao);
            const xValues = chartData.map(item => item.valor);

            const plotlyData = [{
                type: 'bar',
                x: xValues,
                y: yValues,
                orientation: 'h',
                text: xValues.map(v => `R$ ${(v/1e6).toFixed(1)}M`),
                textposition: 'outside',
                marker: {
                    color: xValues,
                    colorscale: 'Blues',
                    reversescale: false
                }
            }];

            const layout = {
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { family: 'Outfit, sans-serif', size: 11, color: '#2F3E46' },
                margin: { l: 80, r: 60, t: 15, b: 30 },
                xaxis: { title: 'Total Homologado (R$)', gridcolor: '#F1F5F9', zeroline: false },
                yaxis: { automargin: true }
            };

            Plotly.newPlot(container, plotlyData, layout, {responsive: true, displayModeBar: false});
        }

        // Gráfico 3: Evolução Anual
        function renderChartEvolution(chartData) {
            const container = document.getElementById('chart-evolution');
            if(!chartData || chartData.length === 0) {
                container.innerHTML = '<div class="no-data">Sem dados temporais disponíveis.</div>';
                return;
            }

            const xValues = chartData.map(item => item.ano);
            const yValues = chartData.map(item => item.valor);

            const plotlyData = [{
                x: xValues,
                y: yValues,
                type: 'scatter',
                mode: 'lines+markers',
                fill: 'tozeroy',
                line: { color: '#00B5B8', width: 3 },
                fillcolor: 'rgba(0, 181, 184, 0.15)',
                marker: { size: 8, color: '#0A3A60' }
            }];

            const layout = {
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { family: 'Outfit, sans-serif', size: 11, color: '#2F3E46' },
                margin: { l: 80, r: 30, t: 15, b: 30 },
                xaxis: { title: 'Ano', tickmode: 'linear', dtick: 1, gridcolor: '#F1F5F9' },
                yaxis: { title: 'Valor Homologado (R$)', gridcolor: '#F1F5F9' }
            };

            Plotly.newPlot(container, plotlyData, layout, {responsive: true, displayModeBar: false});
        }

        // Gráfico 4: Fornecedores
        function renderChartVendors(chartData) {
            const container = document.getElementById('chart-vendors');
            if(!chartData || chartData.length === 0) {
                container.innerHTML = '<div class="no-data">Sem dados de fornecedores disponíveis.</div>';
                return;
            }

            const labels = chartData.map(item => item.fornecedor);
            const values = chartData.map(item => item.valor);

            const plotlyData = [{
                values: values,
                labels: labels,
                type: 'pie',
                hole: 0.4,
                textinfo: 'percent',
                insidetextorientation: 'radial',
                marker: {
                    colors: ['#0A3A60', '#005571', '#007791', '#00B5B8', '#5CD2D4', '#CBD5E1']
                }
            }];

            const layout = {
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { family: 'Outfit, sans-serif', size: 11, color: '#2F3E46' },
                margin: { l: 20, r: 20, t: 15, b: 80 },
                legend: {
                    orientation: 'h',
                    y: -0.1,
                    x: 0.5,
                    xanchor: 'center'
                }
            };

            Plotly.newPlot(container, plotlyData, layout, {responsive: true, displayModeBar: false});
        }

        // Renderizar a Tabela
        function renderTable(records) {
            const tbody = document.getElementById('table-body');
            tbody.innerHTML = '';

            if(!records || records.length === 0) {
                tbody.innerHTML = `<tr><td colspan="9" class="no-data">Nenhum dado encontrado para os filtros selecionados.</td></tr>`;
                return;
            }

            records.forEach(row => {
                const tr = document.createElement('tr');
                
                // Formatar valores para exibição
                const valEstimado = `R$ ${row.valor_estimado.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                const valHomologado = row.situacao === 'Homologado' 
                    ? `R$ ${row.valor_homologado.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` 
                    : (row.situacao === 'Em Andamento' ? 'Em Andamento' : 'R$ 0,00');

                // Classe CSS correspondente para a situação
                let statusClass = 'status-badge';
                if(row.situacao === 'Homologado') statusClass += ' status-homologado';
                else if(row.situacao === 'Em Andamento') statusClass += ' status-em-andamento';
                else if(row.situacao === 'Deserto') statusClass += ' status-deserto';
                else statusClass += ' status-fracassado';

                tr.innerHTML = `
                    <td style="font-weight: 500;">${row.processo}</td>
                    <td>${row.orgao}</td>
                    <td title="${row.objeto}">${row.objeto}</td>
                    <td>${row.modalidade}</td>
                    <td>${valEstimado}</td>
                    <td style="font-weight: 500;">${valHomologado}</td>
                    <td><span class="${statusClass}">${row.situacao}</span></td>
                    <td title="${row.fornecedor}">${row.fornecedor}</td>
                    <td>${row.data}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        // Filtro em tempo real na tabela usando a caixa de pesquisa
        function filterTableBySearch() {
            const searchTerm = document.getElementById('search-input').value.toLowerCase().trim();
            if(searchTerm === '') {
                renderTable(fullDataRecords);
                return;
            }

            const filtered = fullDataRecords.filter(row => {
                return row.processo.toLowerCase().includes(searchTerm) || 
                       row.objeto.toLowerCase().includes(searchTerm) || 
                       row.orgao.toLowerCase().includes(searchTerm) || 
                       row.fornecedor.toLowerCase().includes(searchTerm);
            });

            renderTable(filtered);
        }

        // Exportar a tabela atual como CSV para download
        function exportFilteredCSV() {
            if(fullDataRecords.length === 0) {
                alert("Nenhum dado disponível para exportação!");
                return;
            }

            // Cabeçalho
            let csvContent = "Nº Processo,Órgão,Objeto,Modalidade,Valor Estimado,Valor Homologado,Situação,Fornecedor Vencedor,Data\r\n";

            // Linhas
            fullDataRecords.forEach(row => {
                const line = [
                    `"${row.processo}"`,
                    `"${row.orgao}"`,
                    `"${row.objeto.replace(/"/g, '""')}"`,
                    `"${row.modalidade}"`,
                    row.valor_estimado,
                    row.valor_homologado,
                    `"${row.situacao}"`,
                    `"${row.fornecedor}"`,
                    `"${row.data}"`
                ].join(",");
                csvContent += line + "\r\n";
            });

            // Criar um Blob com BOM UTF-8 para o Excel reconhecer acentos corretamente
            const blob = new Blob(["\ufeff" + csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.setAttribute("href", url);
            link.setAttribute("download", "licitacoes_filtradas.csv");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        }

        // Ponto de entrada do script
        window.addEventListener('DOMContentLoaded', initFilters);
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content, status_code=200)
