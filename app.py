import streamlit as st
import pandas as pd

# Configuração da Página
st.set_page_config(page_title="Sistema de Isenção de IR - Doença Grave", layout="wide")

st.title("⚖️ Sistema Interno do Escritório")
st.subheader("Análise e Cálculo de Restituição de IR (Lei nº 7.713/88)")

with st.sidebar:
    st.header("📋 Dados do Segurado")
    nome_cliente = st.text_input("Nome do Cliente", "Cliente Exemplo")
    patologia = st.text_input("Patologia / CID", "C20 (Neoplasia Maligna do Reto)")
    data_inicio = st.date_input("Data de Início da Doença (Laudo)")
    st.markdown("---")
    st.info("Preencha os valores conforme as Declarações de IRPF e o Histórico do INSS.")

# Abas de Análise por Ano
aba_2023, aba_2024, aba_2025 = st.tabs(["Ano 2023", "Ano 2024", "Ano 2025"])

with aba_2023:
    st.markdown("### Ano-Calendário 2023")
    c1, c2 = st.columns(2)
    with c1:
        rend_23 = st.number_input("Rendimentos Tributáveis Totais (R$)", value=70557.31, step=100.00, key="r23")
        inss_23 = st.number_input("Rendimentos do INSS (R$)", value=38367.12, step=100.00, key="i23")
        ded_23 = st.number_input("Deduções Legais Declaradas (R$)", value=19797.72, step=100.00, key="d23")
    with c2:
        iro_23 = st.number_input("Imposto Devido Original (R$)", value=3662.58, step=10.00, key="iro23")
        ir13_23 = st.number_input("IR Retido sobre o 13º do INSS (R$)", value=41.79, step=1.00, key="1323")
        fator_23 = st.slider("Fator de Isenção no Ano (Proporção pós-laudo)", 0.0, 1.0, 8/12, help="Ex: 8/12 se a isenção começou em maio.")

with aba_2024:
    st.markdown("### Ano-Calendário 2024")
    c1, c2 = st.columns(2)
    with c1:
        rend_24 = st.number_input("Rendimentos Tributáveis Totais (R$)", value=69797.83, step=100.00, key="r24")
        inss_24 = st.number_input("Rendimentos do INSS (R$)", value=39671.83, step=100.00, key="i24")
        ded_24 = st.number_input("Deduções Legais Declaradas (R$)", value=19669.25, step=100.00, key="d24")
    with c2:
        iro_24 = st.number_input("Imposto Devido Original (R$)", value=3336.76, step=10.00, key="iro24")
        ir13_24 = st.number_input("IR Retido sobre o 13º do INSS (R$)", value=36.89, step=1.00, key="1324")
        fator_24 = 1.0

with aba_2025:
    st.markdown("### Ano-Calendário 2025")
    c1, c2 = st.columns(2)
    with c1:
        rend_25 = st.number_input("Rendimentos Tributáveis Totais (R$)", value=76301.60, step=100.00, key="r25")
        inss_25 = st.number_input("Rendimentos do INSS (R$)", value=41530.20, step=100.00, key="i25")
        ded_25 = st.number_input("Deduções Legais Declaradas (R$)", value=17943.67, step=100.00, key="d25")
    with c2:
        iro_25 = st.number_input("Imposto Devido Original (R$)", value=5194.65, step=10.00, key="iro25")
        ir13_25 = st.number_input("IR Retido sobre o 13º do INSS (R$)", value=35.86, step=1.00, key="1325")
        fator_25 = 1.0

st.markdown("---")

if st.button("🚀 Processar Análise de Viabilidade", type="primary", use_container_width=True):
    tabelas_oficiais = {
        2023: {"limite_isencao": 2475174, "aliquota": 0.075},
        2024: {"limite_isencao": 2696320, "aliquota": 0.075},
        2025: {"limite_isencao": 2846720, "aliquota": 0.075}
    }
    
    dados_anos = {
        2023: {'rend': int(rend_23*100), 'inss': int(inss_23*100), 'ded': int(ded_23*100), 'iro': int(iro_23*100), 'ir13': int(ir13_23*100), 'fator': fator_23},
        2024: {'rend': int(rend_24*100), 'inss': int(inss_24*100), 'ded': int(ded_24*100), 'iro': int(iro_24*100), 'ir13': int(ir13_24*100), 'fator': fator_24},
        2025: {'rend': int(rend_25*100), 'inss': int(inss_25*100), 'ded': int(ded_25*100), 'iro': int(iro_25*100), 'ir13': int(ir13_25*100), 'fator': fator_25}
    }
    
    resultado_linhas = []
    soma_total_geral = 0
    
    for ano, info in dados_anos.items():
        inss_isento = int(info['inss'] * info['fator'])
        rend_restante = info['rend'] - inss_isento
        nova_base = max(0, rend_restante - info['ded'])
        
        tabela = tabelas_oficiais[ano]
        if nova_base <= tabela["limite_isencao"]:
            ir_simulado = 0
        else:
            excedente = nova_base - tabela["limite_isencao"]
            ir_simulado = int(excedente * tabela["aliquota"])
            
        dif_anual = info['iro'] - ir_simulado
        total_ano = dif_anual + info['ir13']
        soma_total_geral += total_ano
        
        resultado_linhas.append({
            "Ano": ano,
            "Rend. Tributável (R$)": info['rend'] / 100,
            "INSS Isento (R$)": inss_isento / 100,
            "Nova Base (R$)": nova_base / 100,
            "IR Original (R$)": info['iro'] / 100,
            "IR Simulado (R$)": ir_simulado / 100,
            "Diferença Anual (R$)": dif_anual / 100,
            "IR do 13º (R$)": info['ir13'] / 100,
            "Total Estimado (R$)": total_ano / 100
        })
        
    df_final = pd.DataFrame(resultado_linhas)
    
    st.success("Cálculo executado com sucesso!")
    st.markdown(f"### 📄 Relatório Técnico para: {nome_cliente}")
    st.write(f"**CID:** {patologia} | **Início da Isenção:** {data_inicio}")
    st.dataframe(df_final[['Ano', 'Diferença Anual (R$)', 'IR do 13º (R$)', 'Total Estimado (R$)']], use_container_width=True)
    st.metric(label="💰 VALOR TOTAL ESTIMADO DA RESTITUIÇÃO / ATRASADOS", value=f"R$ {soma_total_geral/100:,.2f}")
    
    if soma_total_geral > 0:
        st.markdown("🟢 **STATUS:** `VIÁVEL PARA AJUIZAMENTO` — Há direito creditício recuperável.")
    else:
        st.markdown("🔴 **STATUS:** `INVIÁVEL` — Sem diferença apurada no período.")
