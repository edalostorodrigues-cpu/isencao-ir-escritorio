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

# Estilização CSS para deixar a interface refinada e corporativa
st.markdown("""
    <style>
    .main {
        background-color: #FDFCFB;
    }
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

# Cabeçalho Principal Limpo e Elegante
st.markdown("""
    <div style="text-align: center; padding: 10px 0 20px 0;">
        <h2 style="color: #2C3E50; font-family: 'Georgia', serif; margin-bottom: 0;">Samile Schmitt</h2>
        <p style="letter-spacing: 5px; color: #997A38; font-size: 13px; font-weight: bold; margin-top: 5px;">A D V O C A C I A</p>
        <hr style="width: 140px; border: 1px solid #C5A059; margin: 15px auto;">
        <h4 style="color: #555; font-weight: normal; font-size: 15px; margin-top: 5px;">Módulo de Análise Inteligente e Cálculo de Isenção de IR (Doença Grave)</h4>
    </div>
""", unsafe_allow_html=True)

# Barra Lateral Profissional
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

# Função para extrair texto dos PDFs enviados
def extrair_texto_pdfs(files):
    texto_total = ""
    for file in files:
        leitor = pypdf.PdfReader(file)
        for pagina in leitor.pages:
            texto_total += pagina.extract_text() + "\n"
    return texto_total

# Função de Leitura Estrita via IA
def analisar_documentos_com_ia(texto_documentos, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.8-flash')
    
    prompt = f"""
    Você é um auditor fiscal especialista em imposto de renda. Extraia estritamente os valores reais encontrados nos documentos do contribuinte abaixo.
    Retorne um JSON puro com esta estrutura exata, convertendo todos os valores financeiros em CENTAVOS (inteiros):
    {{
      "nome_cliente": "Nome completo do contribuinte extraído",
      "patologia_cid": "Não localizado",
      "anos": {{
        "2023": {{"rend_tributavel_original": 0, "rend_inss": 0, "deducoes_legais": 0, "ir_devido_original": 0, "ir_13_inss": 0}},
        "2024": {{"rend_tributavel_original": 0, "rend_inss": 0, "deducoes_legais": 0, "ir_devido_original": 0, "ir_13_inss": 0}},
        "2025": {{"rend_tributavel_original": 0, "rend_inss": 0, "deducoes_legais": 0, "ir_devido_original": 0, "ir_13_inss": 0}}
      }}
    }}
    TEXTO DOS DOCUMENTOS:
    {texto_documentos[:15000]}
    """
    
    try:
        response = model.generate_content(prompt)
        texto_resposta = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(texto_resposta)
    except Exception as e:
        st.error(f"Erro na extração por IA: {e}")
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
    st.success(f"✨ {len(arquivos_pdf)} documento(s) carregado(s) com sucesso na base segura.")
    
    if st.button("🤖 Processar Leitura Inteligente com IA", type="primary"):
        with st.spinner("A Inteligência Artificial está auditando os documentos..."):
            texto_extraido = extrair_texto_pdfs(arquivos_pdf)
            dados_cliente = analisar_documentos_com_ia(texto_extraido, api_key_input)
            st.session_state['dados_cliente'] = dados_cliente

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
            data_editada = st.text_input("Data de Início da Doença (DD/MM/AAAA)", "15/01/2023", help="Digite no formato DD/MM/AAAA")
            
        st.markdown("---")
        st.markdown("#### 📊 Demonstrativo de Valores Originais Extraídos")
        tabela_conf = []
        for ano, info in dados_cliente['anos'].items():
            tabela_conf.append({
                "Ano": ano,
                "Rend. Tributável (R$)": info['rend_tributavel_original'] / 100,
                "INSS (R$)": info['rend_inss'] / 100,
                "Deduções (R$)": info['deducoes_legais'] / 100,
                "IR Original (R$)": info['ir_devido_original'] / 100
            })
        st.dataframe(pd.DataFrame(tabela_conf), use_container_width=True)
        
        if st.button("🚀 Executar Motor de Cálculo Determinístico", type="primary", use_container_width=True):
            tabelas_oficiais = {
                2023: {"limite_isencao_mensal": 190398, "aliquota": 0.15},
                2024: {"limite_isencao_mensal": 211200, "aliquota": 0.15},
                2025: {"limite_isencao_mensal": 225920, "aliquota": 0.15}
            }
            
            resultado_linhas = []
            soma_total_geral = 0
            
            for ano_str, info in dados_cliente['anos'].items():
                ano = int(ano_str)
                rend = info['rend_tributavel_original']
                iro = info['ir_devido_original']
                ir13 = info['ir_13_inss']
                
                tabela = tabelas_oficiais.get(ano, tabelas_oficiais[2024])
                limite_anual = tabela["limite_isencao_mensal"] * 12
                
                base_isenta = min(rend, limite_anual)
                dif_anual = int(base_isenta * tabela["aliquota"])
                dif_anual = min(dif_anual, iro)
                
                total_restituicao_13 = ir13 if ir13 > 0 else int(iro * 0.12)
                
                total_ano = dif_anual + total_restituicao_13
                soma_total_geral += total_ano
                
                resultado_linhas.append({
                    "Ano": ano,
                    "Diferença Anual (R$)": round(dif_anual / 100, 2),
                    "IR do 13º (R$)": round(total_restituicao_13 / 100, 2),
                    "Total Estimado (R$)": round(total_ano / 100, 2)
                })
                
            df_final = pd.DataFrame(resultado_linhas)
            
            if soma_total_geral > 0:
                parecer_didatico = f"""
                <div style="background-color: #FEF9E7; border-left: 5px solid #F39C12; padding: 20px; border-radius: 6px; margin-top: 20px; color: #2C3E50;">
                    <h4 style="margin-top: 0; color: #B7950B;">⚖️ Parecer Técnico e Fundamentação Jurídica</h4>
                    <p><b>Status: HÁ DIREITO AO AJUIZAMENTO (VIÁVEL)</b></p>
                    <p><b>Por que há direito?</b> 
                    Conforme o art. 6º, inciso XIV, da <b>Lei nº 7.713/88</b>, os proventos de aposentadoria, reforma ou pensão recebidos por portadores de doenças graves (como a patologia informada CID <b>{patologia_editada}</b>, diagnosticada em <b>{data_editada}</b>) são isentos do Imposto de Renda.</p>
                    <p><b>O que foi apurado nos cálculos?</b> 
                    Verificou-se que o segurado sofreu retenções indevidas de Imposto de Renda na fonte sobre seus rendimentos previdenciários e sobre o 13º salário nos exercícios analisados. O montante total estimado de créditos tributários passíveis de restituição (respeitando o limite prescricional quinquenal) atinge a quantia de <b>R$ {soma_total_geral/100:,.2f}</b>.</p>
                    <p><b>Conclusão:</b> Recomendam-se a propositura da ação judicial de restituição de indébito tributário cumulada com pedido de tutela antecipada para cessação imediata dos descontos em folha.</p>
                </div>
                """
            else:
                parecer_didatico = f"""
                <div style="background-color: #FADBD8; border-left: 5px solid #E74C3C; padding: 20px; border-radius: 6px; margin-top: 20px; color: #2C3E50;">
                    <h4 style="margin-top: 0; color: #C0392B;">⚖️ Parecer Técnico e Fundamentação Jurídica</h4>
                    <p><b>Status: INVIÁVEL PARA AJUIZAMENTO NO PERÍODO</b></p>
                    <p><b>Por que não há direito creditório apurado?</b> 
                    Apesar da previsão legal de isenção da Lei nº 7.713/88 para a patologia informada, a análise fiscal dos documentos apresentados demonstrou que não houve retenção de Imposto de Renda tributável indébito no período, ou os rendimentos do segurado mantiveram-se integralmente dentro das faixas de isenção/tributação regular sem margem de indébito recuperável.</p>
                    <p><b>Conclusão:</b> O caso não preenche os requisitos financeiros de vantagem econômica para restituição retroativa neste momento.</p>
                </div>
                """

            st.session_state['df_final'] = df_final
            st.session_state['soma_total_geral'] = soma_total_geral / 100
            st.session_state['nome_editado'] = nome_editado
            st.session_state['patologia_editada'] = patologia_editada
            st.session_state['data_editada'] = data_editada
            st.session_state['data_analise'] = datetime.now().strftime("%d/%m/%Y às %H:%M")
            st.session_state['parecer_didatico'] = parecer_didatico

        if 'df_final' in st.session_state:
            st.success("Cálculo jurídico executado com sucesso!")
            st.markdown(f"""
                <div style="background-color: #F4F6F7; padding: 15px; border-left: 4px solid #C5A059; border-radius: 4px; margin-bottom: 20px;">
                    <h4 style="margin:0; color:#2C3E50;">Relatório de Viabilidade — {st.session_state['nome_editado']}</h4>
                    <p style="margin:5px 0 0 0; color:#555;"><b>Patologia / CID:</b> {st.session_state['patologia_editada']} | <b>Início da Enfermidade:</b> {st.session_state['data_editada']} | <b>Análise realizada em:</b> {st.session_state['data_analise']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.dataframe(st.session_state['df_final'], use_container_width=True)
            st.metric(label="💰 VALOR TOTAL ESTIMADO DA RESTITUIÇÃO / ATRASADOS", value=f"R$ {st.session_state['soma_total_geral']:,.2f}")
            
            if st.session_state['soma_total_geral'] > 0:
                st.markdown("🟢 **STATUS:** `VIÁVEL PARA AJUIZAMENTO` — Há direito creditício recuperável a favor do segurado.")
            else:
                st.markdown("🔴 **STATUS:** `INVIÁVEL` — Sem diferença apurada no período.")

            st.markdown(st.session_state['parecer_didatico'], unsafe_allow_html=True)

            # Geração de Relatório em formato HTML elegante para Impressão/PDF direto pelo navegador
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
        <div class="sub">Parecer Técnico de Viabilidade — Isenção de IR (Lei 7.713/88)</div>
    </div>
    
    <div class="info-box">
        <p><b>Data da Análise:</b> {st.session_state['data_analise']}</p>
        <p><b>Cliente / Segurado:</b> {st.session_state['nome_editado']}</p>
        <p><b>Patologia / CID:</b> {st.session_state['patologia_editada']}</p>
        <p><b>Início da Enfermidade:</b> {st.session_state['data_editada']}</p>
    </div>

    <h3 style="color: #2C3E50; border-bottom: 1px solid #ddd; padding-bottom: 8px;">Demonstrativo de Valores a Recuperar</h3>
    {st.session_state['df_final'].to_html(index=False, classes='table')}
    
    <div class="total-box">
        Valor Total Estimado da Restituição: R$ {st.session_state['soma_total_geral']:,.2f}
    </div>
    
    <div class="parecer-box">
        <h3 style="margin-top:0; color:#2C3E50;">Fundamentação Técnica e Jurídica</h3>
        <p>A presente análise foi realizada com base nas diretrizes da <b>Lei nº 7.713/88 (art. 6º, XIV)</b>, que assegura a isenção do Imposto de Renda sobre os proventos de aposentadoria e pensão percebidos por portadores de moléstia grave.</p>
        <p>Constatou-se a existência de direito creditício recuperável em favor do segurado no montante total apurado de <b>R$ {st.session_state['soma_total_geral']:,.2f}</b>, configurando pleno respaldo legal para o ajuizamento da competente ação judicial de restituição de indébito tributário.</p>
    </div>
</body>
</html>"""

            st.download_button(
                label="📥 Baixar Laudo Oficial em HTML/PDF (Pronto para Impressão)",
                data=html_relatorio,
                file_name=f"Laudo_Isencao_IR_{st.session_state['nome_editado'].replace(' ', '_')}.html",
                mime="text/html",
                type="primary"
            )
else:
    st.markdown("""
        <div style="text-align: center; padding: 40px; background-color: #FFFFFF; border-radius: 8px; border: 1px dashed #C5A059; margin-top: 20px;">
            <h3 style="color: #2C3E50;">Bem-vindo ao Sistema de Isenção</h3>
            <p style="color: #666;">Insira sua chave de API na barra lateral e faça o upload dos documentos digitalizados para iniciar a análise jurídica automatizada.</p>
        </div>
    """, unsafe_allow_html=True)
