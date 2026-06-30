import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Configuração da Página
st.set_page_config(
    page_title="SEIA-PR | Dashboard de Licitações de TI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Garantir que a base de dados existe
if not os.path.exists("licitacoes_tecnologia_pr.csv"):
    try:
        from gerar_dados import gerar_dados_licitacoes
        gerar_dados_licitacoes(250)
    except Exception as e:
        st.error(f"Erro ao gerar dados sintéticos: {e}")

# Carregar os dados
@st.cache_data
def load_data():
    if os.path.exists("licitacoes_tecnologia_pr.csv"):
        df = pd.read_csv("licitacoes_tecnologia_pr.csv")
        df["Data_Evento"] = pd.to_datetime(df["Data_Evento"])
        df["Ano"] = df["Data_Evento"].dt.year
        return df
    return pd.DataFrame()

df_raw = load_data()

# Custom CSS para estilo premium (SEIA-PR)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    /* Fontes globais */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Top banner */
    .header-container {
        background: linear-gradient(135deg, #0A3A60 0%, #007791 50%, #00B5B8 100%);
        padding: 2.5rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    .header-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .header-subtitle {
        font-size: 1.1rem;
        font-weight: 300;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
    .source-badge {
        background-color: rgba(255,255,255,0.2);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-top: 1rem;
        border: 1px solid rgba(255,255,255,0.3);
    }
    
    /* Custom KPI Cards */
    .kpi-card {
        background-color: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        border-left: 5px solid #00B5B8;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 18px rgba(0,0,0,0.08);
    }
    .kpi-title {
        font-size: 0.9rem;
        color: #6C7A89;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #0A3A60;
        margin-top: 0.5rem;
        line-height: 1;
    }
    .kpi-footer {
        font-size: 0.75rem;
        color: #8C9A9E;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR (FILTROS) ---
st.sidebar.image("https://www.dadosabertos.pr.gov.br/assets/images/logo-governo.png", width=180, error_bad_lines=False)
st.sidebar.markdown("### 🔍 Filtros Estratégicos")
st.sidebar.markdown("Refine sua pesquisa de contratações públicas de TI e Inovação:")

# Filtro de Ano
anos_disponiveis = sorted(df_raw["Ano"].unique())
ano_selecionado = st.sidebar.slider("Período (Anos)", min_value=int(min(anos_disponiveis)), max_value=int(max(anos_disponiveis)), value=(int(min(anos_disponiveis)), int(max(anos_disponiveis))))

# Filtro de Órgão Demandante
orgaos_disponiveis = sorted(df_raw["Orgao_Demandante"].unique())
orgaos_selecionados = st.sidebar.multiselect("Órgão Demandante", orgaos_disponiveis, default=orgaos_disponiveis)

# Filtro de Modalidade
modalidades_disponiveis = sorted(df_raw["Modalidade"].unique())
modalidades_selecionadas = st.sidebar.multiselect("Modalidade Licitatória", modalidades_disponiveis, default=modalidades_disponiveis)

# Filtro de Situação
situacoes_disponiveis = sorted(df_raw["Situacao"].unique())
situacoes_selecionadas = st.sidebar.multiselect("Situação do Certame", situacoes_disponiveis, default=["Homologado", "Deserto", "Fracassado", "Revogado", "Em Andamento"])

# Aplicar Filtros
df_filtered = df_raw[
    (df_raw["Ano"] >= ano_selecionado[0]) & 
    (df_raw["Ano"] <= ano_selecionado[1]) & 
    (df_raw["Orgao_Demandante"].isin(orgaos_selecionados)) & 
    (df_raw["Modalidade"].isin(modalidades_selecionadas)) & 
    (df_raw["Situacao"].isin(situacoes_selecionadas))
]

# --- MAIN PAGE CONTENT ---

# Cabeçalho Principal (Estilizado)
st.markdown("""
<div class="header-container">
    <div class="header-title">COMPRAS PÚBLICAS DE TECNOLOGIA</div>
    <div class="header-subtitle">Diretoria de Inteligência Artificial — Secretaria de Inovação e Inteligência Artificial (SEIA-PR)</div>
    <div class="source-badge">Fonte oficial: Portal de Dados Abertos do Paraná (GMS)</div>
</div>
""", unsafe_allow_html=True)

# Se os dados filtrados estiverem vazios, mostrar aviso
if df_filtered.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados. Por favor, ajuste as opções na barra lateral.")
else:
    # --- ROW 1: KPI CARDS ---
    col1, col2, col3, col4 = st.columns(4)
    
    # Cálculo das métricas
    investimento_total = df_filtered[df_filtered["Situacao"] == "Homologado"]["Valor_Homologado"].sum()
    total_processos = df_filtered["Numero_Processo"].nunique()
    
    # Taxa de sucesso (Homologado / Processos Finalizados)
    processos_finalizados = df_filtered[df_filtered["Situacao"].isin(["Homologado", "Deserto", "Fracassado", "Revogado"])]
    num_finalizados = processos_finalizados["Numero_Processo"].nunique()
    num_homologados = df_filtered[df_filtered["Situacao"] == "Homologado"]["Numero_Processo"].nunique()
    taxa_sucesso = (num_homologados / num_finalizados * 100) if num_finalizados > 0 else 0.0
    
    fornecedores_unicos = df_filtered[df_filtered["Razao_Social_Vencedora"] != "N/A"]["Razao_Social_Vencedora"].nunique()
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #2E7D32;">
            <div class="kpi-title">Total Investido (TI)</div>
            <div class="kpi-value">R$ {investimento_total/1e6:.2f}M</div>
            <div class="kpi-footer">Apenas processos homologados</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #0A3A60;">
            <div class="kpi-title">Total de Licitações</div>
            <div class="kpi-value">{total_processos}</div>
            <div class="kpi-footer">No período selecionado</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #00B5B8;">
            <div class="kpi-title">Taxa de Sucesso</div>
            <div class="kpi-value">{taxa_sucesso:.1f}%</div>
            <div class="kpi-footer">Homologados vs. Desertose/Fracassados</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #F9A825;">
            <div class="kpi-title">Fornecedores Ativos</div>
            <div class="kpi-value">{fornecedores_unicos}</div>
            <div class="kpi-footer">Empresas com contratos firmados</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    
    # --- ROW 2: VISUALS 2 & 3 ---
    row2_col1, row2_col2 = st.columns(2)
    
    with row2_col1:
        st.subheader("📊 Taxa de Sucesso por Modalidade Licitatória")
        # Criar dataframe para taxa de sucesso por modalidade
        df_mod = df_filtered[df_filtered["Situacao"].isin(["Homologado", "Deserto", "Fracassado", "Revogado"])]
        if not df_mod.empty:
            df_mod_grouped = df_mod.groupby(["Modalidade", "Situacao"]).size().unstack(fill_value=0).reset_index()
            # Garantir colunas
            for col in ["Homologado", "Deserto", "Fracassado", "Revogado"]:
                if col not in df_mod_grouped.columns:
                    df_mod_grouped[col] = 0
            
            df_mod_grouped["Total"] = df_mod_grouped["Homologado"] + df_mod_grouped["Deserto"] + df_mod_grouped["Fracassado"] + df_mod_grouped["Revogado"]
            df_mod_grouped["Taxa Sucesso (%)"] = (df_mod_grouped["Homologado"] / df_mod_grouped["Total"] * 100).round(1)
            df_mod_grouped = df_mod_grouped.sort_values(by="Taxa Sucesso (%)", ascending=True)
            
            fig_mod = px.bar(
                df_mod_grouped,
                y="Modalidade",
                x="Taxa Sucesso (%)",
                orientation='h',
                text="Taxa Sucesso (%)",
                color="Taxa Sucesso (%)",
                color_continuous_scale="Viridis",
                labels={"Taxa Sucesso (%)": "Taxa de Sucesso (%)", "Modalidade": "Modalidade Licitatória"}
            )
            fig_mod.update_traces(textposition='outside')
            fig_mod.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=350,
                margin=dict(l=20, r=20, t=20, b=20),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_mod, use_container_width=True)
        else:
            st.info("Sem dados suficientes para calcular taxa de sucesso por modalidade.")
            
    with row2_col2:
        st.subheader("🏢 Volume de Investimento por Órgão Demandante")
        df_invest_org = df_filtered[df_filtered["Situacao"] == "Homologado"].groupby("Orgao_Demandante")["Valor_Homologado"].sum().reset_index()
        df_invest_org = df_invest_org.sort_values(by="Valor_Homologado", ascending=True)
        
        if not df_invest_org.empty:
            fig_org = px.bar(
                df_invest_org,
                y="Orgao_Demandante",
                x="Valor_Homologado",
                orientation='h',
                labels={"Valor_Homologado": "Total Homologado (R$)", "Orgao_Demandante": "Órgão Demandante"},
                color="Valor_Homologado",
                color_continuous_scale="Blues"
            )
            fig_org.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=350,
                margin=dict(l=20, r=20, t=20, b=20),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_org, use_container_width=True)
        else:
            st.info("Sem investimentos homologados para exibir.")
            
    st.markdown("---")
    
    # --- ROW 3: VISUALS 4 & 5 ---
    row3_col1, row3_col2 = st.columns(2)
    
    with row3_col1:
        st.subheader("📈 Evolução Anual de Gastos com TI")
        df_temporal = df_filtered[df_filtered["Situacao"] == "Homologado"].groupby("Ano")["Valor_Homologado"].sum().reset_index()
        df_temporal = df_temporal.sort_values("Ano")
        
        if not df_temporal.empty:
            fig_temp = px.area(
                df_temporal,
                x="Ano",
                y="Valor_Homologado",
                labels={"Valor_Homologado": "Investimento Homologado (R$)", "Ano": "Ano da Homologação"},
                markers=True
            )
            fig_temp.update_traces(
                line_color='#00B5B8',
                fillcolor='rgba(0, 181, 184, 0.2)'
            )
            fig_temp.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(tickmode='linear', dtick=1),
                height=350,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig_temp, use_container_width=True)
        else:
            st.info("Sem dados temporais disponíveis.")
            
    with row3_col2:
        st.subheader("🏆 Concentração de Fornecedores de Tecnologia")
        df_forn = df_filtered[df_filtered["Situacao"] == "Homologado"].groupby("Razao_Social_Vencedora")["Valor_Homologado"].sum().reset_index()
        
        if not df_forn.empty:
            df_forn = df_forn.sort_values(by="Valor_Homologado", ascending=False)
            # Agrupar menores fornecedores como "Outros"
            top_n = 5
            if len(df_forn) > top_n:
                top_df = df_forn.head(top_n).copy()
                others_val = df_forn.iloc[top_n:]["Valor_Homologado"].sum()
                others_df = pd.DataFrame([{"Razao_Social_Vencedora": "Outros Fornecedores", "Valor_Homologado": others_val}])
                df_forn_pie = pd.concat([top_df, others_df])
            else:
                df_forn_pie = df_forn
                
            fig_pie = px.pie(
                df_forn_pie,
                names="Razao_Social_Vencedora",
                values="Valor_Homologado",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=350,
                margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Sem dados de fornecedores disponíveis.")

    # --- ROW 4: DATA TABLE ---
    st.markdown("---")
    st.subheader("📋 Detalhamento dos Processos Selecionados")
    st.markdown("Veja abaixo a listagem de registros filtrados para auditoria jurídica e operacional:")
    
    # Formatação da tabela
    df_table = df_filtered.copy()
    df_table["Valor_Maximo_Estimado"] = df_table["Valor_Maximo_Estimado"].map("R$ {:,.2f}".format)
    df_table["Valor_Homologado"] = df_table["Valor_Homologado"].apply(lambda x: f"R$ {x:,.2f}" if pd.notnull(x) else "Em Andamento")
    df_table["Data_Evento"] = df_table["Data_Evento"].dt.strftime("%d/%m/%Y")
    
    df_table_display = df_table[[
        "Numero_Processo", "Orgao_Demandante", "Objeto", 
        "Modalidade", "Valor_Maximo_Estimado", "Valor_Homologado", 
        "Situacao", "Razao_Social_Vencedora", "Data_Evento"
    ]].rename(columns={
        "Numero_Processo": "Nº Processo",
        "Orgao_Demandante": "Órgão",
        "Objeto": "Objeto do Certame",
        "Modalidade": "Modalidade",
        "Valor_Maximo_Estimado": "Vlr. Estimado",
        "Valor_Homologado": "Vlr. Homologado",
        "Situacao": "Situação",
        "Razao_Social_Vencedora": "Fornecedor Vencedor",
        "Data_Evento": "Data do Evento"
    })
    
    st.dataframe(df_table_display, use_container_width=True, hide_index=True)
    
    # Opção de Download
    csv_data = df_filtered.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="📥 Exportar Dados Filtrados em CSV",
        data=csv_data,
        file_name="licitacoes_filtradas.csv",
        mime="text/csv"
    )

# Rodapé
st.markdown("""
<div style="text-align: center; color: #8C9A9E; font-size: 0.85rem; margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #E0E0E0;">
    Secretaria de Inovação e Inteligência Artificial do Paraná (SEIA-PR) — Diretoria de Inteligência Artificial<br>
    Desenvolvido com fins pedagógicos para a Avaliação Final de Gestão de Dados Públicos © 2026
</div>
""", unsafe_allow_html=True)
