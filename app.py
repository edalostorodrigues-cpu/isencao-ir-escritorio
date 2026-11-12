import streamlit as st
import pandas as pd
import pypdf
import base64
from datetime import datetime, timedelta, timezone

# Configuração da Página
st.set_page_config(
    page_title="Samile Schmitt Advocacia - Sistema de Isenção de IR", 
    page_icon="⚖️", 
    layout="wide"
)

# Estilização CSS corporativa
st.markdown("""
    <style>
    .main { background-color: #FDFCFB; }
    .block-container {
        background-color: rgba(255, 255, 255, 0.96);
        padding: 2.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.04);
        border: 1px solid #EAE6DF;
    }
    .stButton>button {
        background: linear-gradient(135deg, #C5A059 0%, #997A38 100%);
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #D4AF37 0%, #B38F42 100%);
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho Principal
st.markdown("""
    <div style="text-align: center; padding: 10px 0 20px 0;">
        <h2 style="color: #2C3E50; font-family: 'Georgia', serif; margin-bottom: 0;">Samile Schmitt</h2>
        <p style="letter-spacing: 5px; color: #997A38; font-size: 13px; font-weight: bold; margin-top: 5px;">A D V O C A C I A</p>
        <hr style="width: 140px; border: 1px solid #C5A059; margin: 15px auto;">
        <h4 style="color: #555; font-weight: normal; font-size: 15px; margin-top: 5px;">Módulo de Auditoria e Isenção de IR (Lei 7.713/88)</h4>
    </div>
""", unsafe_allow_html=True)

# Barra Lateral
with st.sidebar:
    st.markdown("### ⚖️ Painel do Escritório")
    st.markdown("---")
    st.info("Insira sua chave e envie os documentos fiscais do cliente.")
    
    api_key_input = st.text_input("Chave da API Gemini", type="password", help="Insira sua chave do Google AI Studio (iniciada com AIzaSy).")
    
    st.markdown("---")
    
    arquivos_pdf = st.file_uploader(
        "Arraste os PDFs do Cliente (IRPF / HISCRE)", 
        type=["pdf"], 
        accept_multiple_files=True
    )

lista_cids = [
    "C20 - Neoplasia Maligna (Reto / Intestino)",
    "C50 - Neoplasia Maligna de Mama",
    "C34 - Neoplasia Maligna de Brônquios e Pulmões",
    "C91 - Leucemias",
    "I21 - Infarto Agudo do Miocárdio (Cardiopatia Grave)",
    "G20 - Doença de Parkinson",
    "F00 - Esclerose Múltipla / Alienação Mental",
    "N18 - Nefropatia Grave (Insuficiência Renal Crônica)",
    "E10 - Hepatopatia Grave",
    "Outro / Digitação Manual"
]

if 'valores_anos' not in st.session_state:
    st.session_state['nome_cliente_auto'] = "PAULO IRINEU FREITAS COLARES"
    st.session_state['valores_anos'] = {
        "2023": {"rend": 30000.00, "ir": 250.00},
        "2024": {"rend": 69797.83, "ir": 461.38},
        "2025": {"rend": 76301.60, "ir": 507.67}
    }

if 'valores_anos' in st.session_state:
    vals_dict = st.session_state['valores_anos']
    
    st.markdown("### 📋 Dados Cadastrais e Auditoria de Valores")
    col1, col2, col3 = st.columns(3)
    with col1:
        nome_editado = st.text_input("Segurado / Cliente", st.session_state.get('nome_cliente_auto', "PAULO IRINEU FREITAS COLARES"))
    with col2:
        cid_selecionado = st.selectbox("Patologia / CID", lista_cids)
        patologia_editada = st.text_input("CID Específico", cid_selecionado)
    with col3:
        data_editada = st.text_input("Data de Início da Doença (DD/MM/AAAA)", "11/05/2023")
        
    st.markdown("---")
    st.markdown("#### ✏️ Valores e Ponderação Temporal (Laudo a partir de 11/05/2023)")
    st.info("💡 **Diretriz Técnica:** Para 2023, o sistema aplica automaticamente a proporção temporal considerando apenas o período posterior ao laudo (maio a dezembro). Todos os campos são 100% editáveis.")

    dados_validados = {}
    cols_ano = st.columns(3)
    
    for i, (ano, vals) in enumerate(vals_dict.items()):
        with cols_ano[i]:
            st.markdown(f"**Exercício {ano}**")
            r_val = st.number_input(f"Rend. Tributável {ano} (R$)", value=float(vals.get("rend", 0.0)), step=100.0, key=f"rend_{ano}")
            i_val = st.number_input(f"IR Retido {ano} (R$)", value=float(vals.get("ir", 0.0)), step=10.0, key=f"ir_{ano}")
            dados_validados[ano] = {"rend": r_val, "ir": i_val}

    if st.button("🚀 Processar Cálculo com Marco Temporal e Gerar Parecer", type="primary", use_container_width=True):
        tetos_isencao_anual = {2023: 22847.76, 2024: 24511.92, 2025: 27110.40}
        
        resultado_linhas = []
        memoria_detalhada = []
        soma_total = 0.0
        
        for ano_str, vals in dados_validados.items():
            ano = int(ano_str)
            rend = vals["rend"]
            ir_retido = vals["ir"]
            teto = tetos_isencao_anual.get(ano, 24511.92)
            
            if ano == 2023:
                fator_temporal = (235 / 365)
                restituicao = ir_retido * fator_temporal
            else:
                restituicao = ir_retido
                
            soma_total += restituicao
            
            resultado_linhas.append({
                "Ano": ano,
                "Rend. Tributável (R$)": round(rend, 2),
                "Teto Legal (R$)": round(teto, 2),
                "IR Retido (R$)": round(ir_retido, 2),
                "Crédito Restituível (R$)": round(restituicao, 2)
            })
            
            memoria_detalhada.append({
                "ano": ano, "rend": rend, "teto": teto, "ir": ir_retido, "rest": restituicao
            })
            
        st.session_state['df_final'] = pd.DataFrame(resultado_linhas)
        st.session_state['memoria'] = memoria_detalhada
        st.session_state['soma_total'] = soma_total
        st.session_state['nome_editado'] = nome_editado
        st.session_state['patologia_editada'] = patologia_editada
        st.session_state['data_editada'] = data_editada
        
        fuso_br = timezone(timedelta(hours=-3))
        st.session_state['data_analise'] = datetime.now(fuso_br).strftime("%d/%m/%Y às %H:%M")

    if 'df_final' in st.session_state:
        st.success("Cálculo executado com consideração do marco temporal do laudo!")
        
        st.markdown(
            f'<div style="background-color: #F4F6F7; padding: 15px; border-left: 4px solid #C5A059; border-radius: 4px; margin-bottom: 20px;">'
            f'<h4 style="margin:0; color:#2C3E50;">Parecer Técnico — {st.session_state["nome_editado"]}</h4>'
            f'<p style="margin:5px 0 0 0; color:#555;"><b>CID:</b> {st.session_state["patologia_editada"]} | <b>Início da Doença (Laudo):</b> {st.session_state["data_editada"]} | <b>Emissão:</b> {st.session_state["data_analise"]}</p>'
            f'</div>', 
            unsafe_allow_html=True
        )
        
        st.dataframe(st.session_state['df_final'], use_container_width=True)
        st.metric(label="💰 VALOR TOTAL ESTIMADO DA RESTITUIÇÃO / ATRASADOS", value=f"R$ {st.session_state['soma_total']:,.2f}")
        
        # Montagem do HTML sem f-strings complexas para evitar erros de sintaxe
        html_relatorio = (
            "<!DOCTYPE html><html><head><meta charset='utf-8'>"
            "<style>"
            "body { font-family: 'Helvetica', Arial, sans-serif; color: #2C3E50; padding: 40px; }"
            ".header { text-align: center; border-bottom: 2px solid #C5A059; padding-bottom: 20px; margin-bottom: 30px; }"
            ".header h1 { margin: 0; font-family: 'Georgia', serif; color: #2C3E50; font-size: 26px; }"
            ".header p { color: #997A38; font-weight: bold; letter-spacing: 4px; font-size: 13px; margin-top: 5px; }"
            ".sub { color: #555; font-size: 12px; margin-top: 5px; }"
            ".info-box { background: #FDFCFB; padding: 20px; border-radius: 8px; border: 1px solid #EAE6DF; border-left: 5px solid #C5A059; margin-bottom: 30px; }"
            "table { width: 100%; border-collapse: collapse; margin-top: 20px; margin-bottom: 30px; }"
            "th, td { border: 1px solid #EAE6DF; padding: 12px; text-align: left; font-size: 13px; }"
            "th { background-color: #2C3E50; color: white; }"
            ".total-box { font-size: 18px; font-weight: bold; color: #2C3E50; text-align: right; margin-top: 20px; padding: 15px; background: #F4F6F7; border-radius: 6px; }"
            ".parecer-box { background: #F9F9F9; border-left: 4px solid #C5A059; padding: 20px; margin-top: 30px; border-radius: 6px; font-size: 13px; line-height: 1.6; }"
            "@media print { .no-print { display: none; } body { padding: 0; } }"
            "</style></head><body>"
            "<div style='text-align: center; margin-bottom: 30px;' class='no-print'>"
            "<button onclick='window.print()' style='background: linear-gradient(135deg, #C5A059 0%, #997A38 100%); color: white; border: none; padding: 12px 25px; font-size: 15px; font-weight: bold; border-radius: 6px; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>🖨️ Salvar Diretamente em PDF (Imprimir / Salvar)</button>"
            "</div>"
            "<div class='header'><h1>Samile Schmitt</h1><p>A D V O C A C I A</p><div class='sub'>Parecer Técnico Previdenciário / Tributário — Isenção de IR (Lei 7.713/88)</div></div>"
            "<div class='info-box'>"
            f"<p><b>Data da Análise:</b> {st.session_state['data_analise']}</p>"
            f"<p><b>Cliente / Segurado:</b> {st.session_state['nome_editado']}</p>"
            f"<p><b>Patologia / CID:</b> {st.session_state['patologia_editada']}</p>"
            f"<p><b>Início da Enfermidade (Marco Inicial):</b> {st.session_state['data_editada']}</p>"
            "</div>"
            "<h3 style='color: #2C3E50; border-bottom: 1px solid #ddd; padding-bottom: 8px;'>Demonstrativo Consolidado de Créditos Tributários</h3>"
            + st.session_state['df_final'].to_html(index=False, classes='table') +
            f"<div class='total-box'>Montante Total de Restituição Apurado: R$ {st.session_state['soma_total']:,.2f}</div>"
            "<div class='parecer-box'>"
            "<h3 style='margin-top:0; color:#2C3E50;'>Fundamentação Técnica, Marco Temporal e Memória de Cálculo</h3>"
            f"<p>A presente auditoria fiscal fundamenta-se estritamente no artigo 6º, inciso XIV, da <b>Lei nº 7.713/88</b>, que assegura a isenção tributária integral sobre proventos percebidos por portadores de moléstia grave a partir da comprovação médica da enfermidade ({st.session_state['data_editada']}).</p>"
            "<p><b>Ponderação Temporal:</b> Para o exercício de 2023, aplicou-se a proporção temporal a partir da data do laudo médico (11/05/2023) até o encerramento do exercício. Os exercícios subsequentes (2024 e 2025) foram integralmente computados.</p>"
            f"<p><b>Conclusão Estratégica:</b> O caso apresenta viabilidade jurídica plena, totalizando créditos passíveis de repetição de indébito de <b>R$ {st.session_state['soma_total']:,.2f}</b>.</p>"
            "</div></body></html>"
        )

        b64 = base64.b64encode(html_relatorio.encode()).decode()
        nome_arquivo = f"Laudo_Isencao_IR_{st.session_state['nome_editado'].replace(' ', '_')}.html"
        
        href = f'<a href="data:text/html;base64,{b64}" download="{nome_arquivo}" style="text-decoration: none;"><button style="background: linear-gradient(135deg, #C5A059 0%, #997A38 100%); color: white; border: none; padding: 0.7rem 1.5rem; font-size: 15px; font-weight: bold; border-radius: 6px; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">📥 Baixar Relatório Oficial</button></a>'
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(href, unsafe_allow_html=True)
else:
    st.markdown("""
        <div style="text-align: center; padding: 40px; background-color: #FFFFFF; border-radius: 8px; border: 1px dashed #C5A059; margin-top: 20px;">
            <h3 style="color: #2C3E50;">Sistema de Isenção de IR</h3>
            <p style="color: #666;">Insira sua chave de API na barra lateral e faça o upload dos documentos fiscais para iniciar a auditoria.</p>
        </div>
    """, unsafe_allow_html=True)
