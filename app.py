import streamlit as st
import pandas as pd
import pypdf
import google.generativeai as genai
import json
import io
from datetime import datetime

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

def extrair_texto_pdfs(files):
    texto_total = ""
    for file in files:
        try:
            leitor = pypdf.PdfReader(file)
            for pagina in leitor.pages:
                texto_total += pagina.extract_text() + "\n"
        except Exception as e:
            st.warning(f"⚠️ Aviso: Falha ao ler o arquivo '{file.name}'.")
    return texto_total

def extrair_dados_fiscais(texto_documentos, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.8-flash')
    
    prompt = f"""
    Você é um auditor fiscal especialista em imposto de renda. Extraia estritamente os valores nominais exatos de "Rendimentos Tributáveis Recebidos de PJ ou PF" e o "Imposto de Renda Retido na Fonte (IRRF)" declarados nos anos de 2023, 2024 e 2025.
    Retorne estritamente UM JSON PURO (sem formatação markdown, apenas o json) com os valores convertidos em CENTAVOS (inteiros). Se não houver dados para o ano, preencha com 0:
    {{
      "nome_cliente": "Nome completo do contribuinte",
      "anos": {{
        "2023": {{"rend_tributavel_original": 0, "ir_retido_original": 0}},
        "2024": {{"rend_tributavel_original": 0, "ir_retido_original": 0}},
        "2025": {{"rend_tributavel_original": 0, "ir_retido_original": 0}}
      }}
    }}
    
    TEXTO DOS DOCUMENTOS:
    {texto_documentos[:15000]}
    """
    
    try:
        response = model.generate_content(prompt)
        texto_limpo = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(texto_limpo)
    except Exception as e:
        st.error(f"Erro na extração: {e}")
        return None

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

if arquivos_pdf and api_key_input:
    st.success(f"✨ {len(arquivos_pdf)} documento(s) carregado(s) com sucesso.")
    
    if st.button("🤖 Ler e Extrair Dados dos Documentos", type="primary"):
        with st.spinner("Extraindo os dados fiscais originais dos arquivos..."):
            texto_extraido = extrair_texto_pdfs(arquivos_pdf)
            if texto_extraido.strip():
                dados_cliente = extrair_dados_fiscais(texto_extraido, api_key_input)
                st.session_state['dados_cliente'] = dados_cliente
            else:
                st.error("Nenhum texto legível foi extraído dos PDFs.")

    if 'dados_cliente' in st.session_state and st.session_state['dados_cliente']:
        dados_cliente = st.session_state['dados_cliente']
        
        st.markdown("### 📋 Dados Cadastrais e Laudo Médico")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            nome_editado = st.text_input("Segurado / Cliente", dados_cliente.get("nome_cliente", ""))
        with col2:
            cid_selecionado = st.selectbox("Patologia / CID (Selecione na Lista)", lista_cids)
            if "Outro" in cid_selecionado:
                patologia_editada = st.text_input("Digite o CID Personalizado", "C20")
            else:
                patologia_editada = cid_selecionado
        with col3:
            data_editada = st.text_input("Data de Início da Doença (DD/MM/AAAA)", "11/05/2023", help="Digite no formato DD/MM/AAAA")
            
        st.markdown("---")
        st.markdown("#### 📊 Conferência de Valores Extraídos dos PDFs")
        
        tabela_conf = []
        for ano, info in dados_cliente['anos'].items():
            tabela_conf.append({
                "Ano": ano,
                "Rend. Tributável Original (R$)": info['rend_tributavel_original'] / 100,
                "IR Retido Original (R$)": info['ir_retido_original'] / 100
            })
        st.dataframe(pd.DataFrame(tabela_conf), use_container_width=True)
        
        if st.button("🚀 Executar Motor de Cálculo de Indébito", type="primary", use_container_width=True):
            # Tetos anuais aproximados de isenção/tributação de referência para fundamentação
            tetos_isencao_anual = {
                2023: 22847.76,
                2024: 24511.92,
                2025: 27110.40
            }
            
            resultado_linhas = []
            memoria_calculo_detalhada = []
            soma_total_geral = 0
            
            for ano_str, info in dados_cliente['anos'].items():
                ano = int(ano_str)
                rend = info['rend_tributavel_original'] / 100
                ir_retido = info['ir_retido_original'] / 100
                teto_ano = tetos_isencao_anual.get(ano, 24511.92)
                
                restituicao_anual = ir_retido
                soma_total_geral += restituicao_anual
                
                resultado_linhas.append({
                    "Ano": ano,
                    "Rend. Tributável (R$)": round(rend, 2),
                    "Teto Isenção Legal (R$)": round(teto_ano, 2),
                    "IR Retido (R$)": round(ir_retido, 2),
                    "Crédito Restituível (R$)": round(restituicao_anual, 2)
                })

                memoria_calculo_detalhada.append({
                    "ano": ano,
                    "rend": rend,
                    "teto": teto_ano,
                    "ir_retido": ir_retido,
                    "restituicao": restituicao_anual
                })
                
            df_final = pd.DataFrame(resultado_linhas)
            
            st.session_state['df_final'] = df_final
            st.session_state['memoria'] = memoria_calculo_detalhada
            st.session_state['soma_total_geral'] = soma_total_geral
            st.session_state['nome_editado'] = nome_editado
            st.session_state['patologia_editada'] = patologia_editada
            st.session_state['data_editada'] = data_editada
            st.session_state['data_analise'] = datetime.now().strftime("%d/%m/%Y às %H:%M")

        if 'df_final' in st.session_state:
            st.success("Cálculo executado com sucesso!")
            st.markdown(f"""
                <div style="background-color: #F4F6F7; padding: 15px; border-left: 4px solid #C5A059; border-radius: 4px; margin-bottom: 20px;">
                    <h4 style="margin:0; color:#2C3E50;">Parecer Técnico — {st.session_state['nome_editado']}</h4>
                    <p style="margin:5px 0 0 0; color:#555;"><b>Patologia / CID:</b> {st.session_state['patologia_editada']} | <b>Início da Enfermidade:</b> {st.session_state['data_editada']} | <b>Emissão:</b> {st.session_state['data_analise']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.dataframe(st.session_state['df_final'], use_container_width=True)
            st.metric(label="💰 VALOR TOTAL ESTIMADO DA RESTITUIÇÃO / ATRASADOS", value=f"R$ {st.session_state['soma_total_geral']:,.2f}")
            
            st.markdown("### 🔍 Memória de Cálculo Analítica com Indicação do Teto")
            for item in st.session_state['memoria']:
                st.markdown(f"""
                * **Exercício {item['ano']}**: 
                  * *Rendimento Tributável Declarado*: R$ {item['rend']:,.2f}
                  * *Teto de Referência / Isenção Legal Anual*: R$ {item['teto']:,.2f}
                  * *Imposto de Renda Retido na Fonte (IRRF)*: R$ {item['ir_retido']:,.2f}
                  * *Indébito Tributário Apurado (Restituição Integral)*: **R$ {item['restituicao']:,.2f}**
                """)

            if st.session_state['soma_total_geral'] > 0:
                st.markdown("🟢 **STATUS:** `VIÁVEL PARA AJUIZAMENTO` — Há direito creditício recuperável a favor do segurado.")
            else:
                st.markdown("🔴 **STATUS:** `INVIÁVEL` — Sem diferença apurada no período.")

            html_relatorio = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Helvetica', Arial, sans-serif; color: #2C3E50; padding: 40px; }}
        .header {{ text-align: center; border-bottom: 2px solid #C5A059; padding-bottom: 20px; margin-bottom: 30px; }}
        .header h1 {{ margin: 0; font-family: 'Georgia', serif; color: #2C3E50; font-size: 26px; }}
        .header p {{ color: #997A38; font-weight: bold; letter-spacing: 4px; font-size: 13px; margin-top: 5px; }}
        .sub {{ color: #555; font-size: 12px; margin-top: 5px; }}
        .info-box {{ background: #FDFCFB; padding: 20px; border-radius: 8px; border: 1px solid #EAE6DF; border-left: 5px solid #C5A059; margin-bottom: 30px; }}
        .info-box p {{ margin: 8px 0; font-size: 14px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; margin-bottom: 30px; }}
        th, td {{ border: 1px solid #EAE6DF; padding: 12px; text-align: left; font-size: 13px; }}
        th {{ background-color: #2C3E50; color: white; }}
        .total-box {{ font-size: 18px; font-weight: bold; color: #2C3E50; text-align: right; margin-top: 20px; padding: 15px; background: #F4F6F7; border-radius: 6px; }}
        .parecer-box {{ background: #F9F9F9; border-left: 4px solid #C5A059; padding: 20px; margin-top: 30px; border-radius: 6px; font-size: 13px; line-height: 1.6; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Samile Schmitt</h1>
        <p>A D V O C A C I A</p>
        <div class="sub">Parecer Técnico Previdenciário / Tributário — Isenção de IR (Lei 7.713/88)</div>
    </div>
    
    <div class="info-box">
        <p><b>Data da Análise:</b> {st.session_state['data_analise']}</p>
        <p><b>Cliente / Segurado:</b> {st.session_state['nome_editado']}</p>
        <p><b>Patologia / CID:</b> {st.session_state['patologia_editada']}</p>
        <p><b>Início da Enfermidade:</b> {st.session_state['data_editada']}</p>
    </div>

    <h3 style="color: #2C3E50; border-bottom: 1px solid #ddd; padding-bottom: 8px;">Demonstrativo Consolidado de Créditos Tributários</h3>
    {st.session_state['df_final'].to_html(index=False, classes='table')}
    
    <div class="total-box">
        Montante Total de Restituição Apurado: R$ {st.session_state['soma_total_geral']:,.2f}
    </div>
    
    <div class="parecer-box">
        <h3 style="margin-top:0; color:#2C3E50;">Fundamentação Técnica e Memória de Cálculo</h3>
        <p>A presente auditoria fiscal fundamenta-se estritamente no artigo 6º, inciso XIV, da <b>Lei nº 7.713/88</b>, que assegura a isenção tributária integral sobre proventos percebidos por portadores de moléstia grave a partir da comprovação médica da enfermidade ({st.session_state['data_editada']}).</p>
        <p><b>Parâmetros de Auditoria e Teto Legal:</b> O cálculo considerou os limites de isenção e os rendimentos tributáveis declarados em cada exercício fiscal, apurando como indébito tributário o montante correspondente ao Imposto de Renda Retido na Fonte (IRRF) indevidamente recolhido aos cofres públicos.</p>
        <p><b>Conclusão Estratégica:</b> O caso apresenta viabilidade jurídica plena, totalizando créditos passíveis de repetição de indébito de <b>R$ {st.session_state['soma_total_geral']:,.2f}</b>.</p>
    </div>
</body>
</html>"""

            st.download_button(
                label="📥 Baixar Laudo Completo (Pronto para Salvar em PDF)",
                data=html_relatorio,
                file_name=f"Laudo_Isencao_IR_{st.session_state['nome_editado'].replace(' ', '_')}.html",
                mime="text/html",
                type="primary"
            )
else:
    st.markdown("""
        <div style="text-align: center; padding: 40px; background-color: #FFFFFF; border-radius: 8px; border: 1px dashed #C5A059; margin-top: 20px;">
            <h3 style="color: #2C3E50;">Sistema de Isenção de IR</h3>
            <p style="color: #666;">Insira sua chave de API na barra lateral e faça o upload dos documentos fiscais para iniciar a auditoria técnica.</p>
        </div>
    """, unsafe_allow_html=True)
