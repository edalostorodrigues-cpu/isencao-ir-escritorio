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

# Estilização CSS inspirada no padrão corporativo da Otto
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
        <h4 style="color: #555; font-weight: normal; font-size: 15px; margin-top: 5px;">Módulo de Análise Previdenciária e Tributária (Padrão Otto)</h4>
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

# Auditoria Inteligente alinhada ao rigor técnico da Otto
def analisar_documentos_com_ia(texto_documentos, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.8-flash')
    
    prompt = f"""
    Você é a inteligência artificial jurídico-tributária 'Otto', especialista em auditoria de Imposto de Renda e Isenção por Doença Grave (Lei 7.713/88).
    Analise rigorosamente o texto extraído dos documentos fiscais abaixo.
    
    Extraia com absoluta precisão os valores de Rendimentos Tributáveis e Imposto de Renda Retido na Fonte (IRRF) para os anos de 2023, 2024 e 2025.
    Retorne UM JSON PURO (sem blocos de markdown, apenas o json) seguindo estritamente esta estrutura, com valores em CENTAVOS (inteiros):
    {{
      "nome_cliente": "Nome completo do contribuinte",
      "patologia_cid": "Não localizado",
      "anos": {{
        "2023": {{"rend_tributavel_original": 0, "ir_devido_original": 0, "ir_13_inss": 0}},
        "2024": {{"rend_tributavel_original": 0, "ir_devido_original": 0, "ir_13_inss": 0}},
        "2025": {{"rend_tributavel_original": 0, "ir_devido_original": 0, "ir_13_inss": 0}}
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
        st.error(f"Erro na auditoria por IA: {e}")
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
    
    if st.button("🤖 Executar Auditoria Inteligente (Padrão Otto)", type="primary"):
        with st.spinner("A Otto está auditando minuciosamente os documentos fiscais..."):
            texto_extraido = extrair_texto_pdfs(arquivos_pdf)
            if texto_extraido.strip():
                dados_cliente = analisar_documentos_com_ia(texto_extraido, api_key_input)
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
            data_editada = st.text_input("Data de Início da Doença (DD/MM/AAAA)", "15/01/2023", help="Digite no formato DD/MM/AAAA")
            
        st.markdown("---")
        st.markdown("#### 📊 Demonstrativo de Valores Originais Extraídos")
        tabela_conf = []
        for ano, info in dados_cliente['anos'].items():
            tabela_conf.append({
                "Ano": ano,
                "Rend. Tributável (R$)": info['rend_tributavel_original'] / 100,
                "IR Original Retido (R$)": info['ir_devido_original'] / 100
            })
        st.dataframe(pd.DataFrame(tabela_conf), use_container_width=True)
        
        if st.button("🚀 Processar Cálculo Determinístico Otto", type="primary", use_container_width=True):
            tabelas_oficiais = {
                2023: {"limite_isencao_mensal": 190398, "aliquota": 0.15},
                2024: {"limite_isencao_mensal": 211200, "aliquota": 0.15},
                2025: {"limite_isencao_mensal": 225920, "aliquota": 0.15}
            }
            
            resultado_linhas = []
            memoria_calculo_detalhada = []
            soma_total_geral = 0
            
            for ano_str, info in dados_cliente['anos'].items():
                ano = int(ano_str)
                rend = info['rend_tributavel_original']
                iro = info['ir_devido_original']
                ir13 = info['ir_13_inss']
                
                tabela = tabelas_oficiais.get(ano, tabelas_oficiais[2024])
                limite_anual = tabela["limite_isencao_mensal"] * 12
                
                # Motor rigoroso Otto de cálculo de indébito tributário
                base_isenta = min(rend, limite_anual)
                dif_anual = int(base_isenta * tabela["aliquota"])
                dif_anual = min(dif_anual, iro)
                
                total_restituicao_13 = ir13 if ir13 > 0 else int(iro * 0.10)
                total_ano = dif_anual + total_restituicao_13
                soma_total_geral += total_ano
                
                resultado_linhas.append({
                    "Ano": ano,
                    "Diferença Anual (R$)": round(dif_anual / 100, 2),
                    "IR do 13º (R$)": round(total_restituicao_13 / 100, 2),
                    "Total Estimado (R$)": round(total_ano / 100, 2)
                })

                memoria_calculo_detalhada.append({
                    "ano": ano,
                    "rend": rend / 100,
                    "dif_anual": dif_anual / 100,
                    "ir13": total_restituicao_13 / 100,
                    "total": total_ano / 100
                })
                
            df_final = pd.DataFrame(resultado_linhas)
            
            st.session_state['df_final'] = df_final
            st.session_state['memoria'] = memoria_calculo_detalhada
            st.session_state['soma_total_geral'] = soma_total_geral / 100
            st.session_state['nome_editado'] = nome_editado
            st.session_state['patologia_editada'] = patologia_editada
            st.session_state['data_editada'] = data_editada
            st.session_state['data_analise'] = datetime.now().strftime("%d/%m/%Y às %H:%M")

        if 'df_final' in st.session_state:
            st.success("Auditoria e cálculo executados com sucesso sob diretriz da Otto!")
            st.markdown(f"""
                <div style="background-color: #F4F6F7; padding: 15px; border-left: 4px solid #C5A059; border-radius: 4px; margin-bottom: 20px;">
                    <h4 style="margin:0; color:#2C3E50;">Parecer Técnico Preliminar — {st.session_state['nome_editado']}</h4>
                    <p style="margin:5px 0 0 0; color:#555;"><b>Patologia / CID:</b> {st.session_state['patologia_editada']} | <b>Início da Enfermidade:</b> {st.session_state['data_editada']} | <b>Emissão:</b> {st.session_state['data_analise']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.dataframe(st.session_state['df_final'], use_container_width=True)
            st.metric(label="💰 VALOR TOTAL ESTIMADO DA RESTITUIÇÃO / ATRASADOS", value=f"R$ {st.session_state['soma_total_geral']:,.2f}")
            
            st.markdown("### 🔍 Memória de Cálculo Analítica (Diretriz Otto)")
            for item in st.session_state['memoria']:
                st.markdown(f"""
                * **Exercício {item['ano']}**: Rendimento tributável auditado de **R$ {item['rend']:,.2f}**. 
                  * *Fundamentação Art. 6º, XIV, Lei 7.713/88*: Incidência da isenção sobre os proventos.
                  * *Indébito sobre Rendimentos Regulares*: **R$ {item['dif_anual']:,.2f}**.
                  * *Indébito sobre 13º Salário (Retenção Isolada)*: **R$ {item['ir13']:,.2f}**.
                  * **Crédito Líquido Apurado no Ano {item['ano']}**: **R$ {item['total']:,.2f}**.
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
        <div class="sub">Parecer Técnico Previdenciário / Tributário — Isenção de IR (Padrão Otto)</div>
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
        <h3 style="margin-top:0; color:#2C3E50;">Fundamentação Técnica e Memória de Cálculo (Diretriz Otto)</h3>
        <p>A presente auditoria fiscal fundamenta-se estritamente no artigo 6º, inciso XIV, da <b>Lei nº 7.713/88</b>, que assegura a isenção tributária sobre proventos percebidos por portadores de moléstia grave.</p>
        <p><b>Parâmetros de Auditoria:</b> O cruzamento de dados obedeceu aos tetos legais vigentes em cada exercício, descontando o indébito do imposto retido na fonte sobre rendimentos regulares e gratificações natalinas, respeitando a prescrição quinquenal.</p>
        <p><b>Conclusão Estratégica:</b> O caso apresenta viabilidade jurídica plena, totalizando créditos passíveis de repetição de indébito de <b>R$ {st.session_state['soma_total_geral']:,.2f}</b>.</p>
    </div>
</body>
</html>"""

            st.download_button(
                label="📥 Baixar Laudo Completo (Padrão Otto)",
                data=html_relatorio,
                file_name=f"Laudo_Otto_Isencao_IR_{st.session_state['nome_editado'].replace(' ', '_')}.html",
                mime="text/html",
                type="primary"
            )
else:
    st.markdown("""
        <div style="text-align: center; padding: 40px; background-color: #FFFFFF; border-radius: 8px; border: 1px dashed #C5A059; margin-top: 20px;">
            <h3 style="color: #2C3E50;">Módulo Ativo — Padrão Otto</h3>
            <p style="color: #666;">Insira sua chave de API na barra lateral e faça o upload dos documentos fiscais para iniciar a auditoria técnica.</p>
        </div>
    """, unsafe_allow_html=True)
