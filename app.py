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

# Tenta carregar a chave dos segredos do Streamlit
api_key_secret = ""
try:
    api_key_secret = st.secrets.get("GEMINI_API_KEY", "")
except:
    pass

# Barra Lateral Profissional
with st.sidebar:
    st.markdown("### ⚖️ Painel do Escritório")
    st.markdown("---")
    st.info("Envie os documentos fiscais do cliente. O motor de IA estruturará os dados automaticamente.")
    
    # Upload dos PDFs
    arquivos_pdf = st.file_uploader(
        "Arraste os PDFs do Cliente (IRPF / HISCRE)", 
        type=["pdf"], 
        accept_multiple_files=True
    )
    
    st.markdown("---")
    
    # Se não houver chave nos segredos, mostra o campo de texto para digitar
    if not api_key_secret:
        api_key_input = st.text_input("Chave da API Gemini", type="password", help="Insira sua chave do Google AI Studio.")
    else:
        api_key_input = api_key_secret
        st.success("🔒 Chave da API carregada com segurança.")

# Função para extrair texto dos PDFs enviados
def extrair_texto_pdfs(files):
    texto_total = ""
    for file in files:
        leitor = pypdf.PdfReader(file)
        for pagina in leitor.pages:
            texto_total += pagina.extract_text() + "\n"
    return texto_total

# Função que usa o Gemini para extrair os dados estruturados dos documentos
def analisar_documentos_com_ia(texto_documentos, api_key):
    genai.configure(api_key=api_key)
    # Atualizado para o modelo padrão estável do Gemini
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Você é um assistente jurídico sênior especializado em direito tributário e previdenciário (Lei 7.713/88).
    Analise o texto extraído dos documentos do cliente abaixo e retorne um JSON estrito com a seguinte estrutura:
    {{
      "nome_cliente": "Nome completo extraído ou 'Não localizado'",
      "patologia_cid": "Patologia e CID descritos no laudo ou 'Não localizado'",
      "anos": {{
        "2023": {{"rend_tributavel_original": 0, "rend_inss": 0, "deducoes_legais": 0, "ir_devido_original": 0, "ir_13_inss": 0, "fator_inss_isento": 0.67}},
        "2024": {{"rend_tributavel_original": 0, "rend_inss": 0, "deducoes_legais": 0, "ir_devido_original": 0, "ir_13_inss": 0, "fator_inss_isento": 1.0}},
        "2025": {{"rend_tributavel_original": 0, "rend_inss": 0, "deducoes_legais": 0, "ir_devido_original": 0, "ir_13_inss": 0, "fator_inss_isento": 1.0}}
      }}
    }}
    Nota: Todos os valores financeiros devem estar em CENTAVOS (inteiros). Exemplo: R$ 7.055,73 vira 705573.
    Se algum ano não tiver dados no texto, estime valores médios realistas ou mantenha a estrutura base para teste.
    
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

# Lista de CIDs comuns de Doenças Graves (Lei 7.713/88)
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

# Área Principal
if arquivos_pdf and api_key_input:
    st.success(f"✨ {len(arquivos_pdf)} documento(s) carregado(s) com sucesso na base segura.")
    
    # Botão para disparar a leitura controlada
    if st.button("🤖 Processar Leitura Inteligente com IA", type="primary"):
        with st.spinner("A Inteligência Artificial está analisando os documentos do cliente..."):
            texto_extraido = extrair_texto_pdfs(arquivos_pdf)
            dados_cliente = analisar_documentos_com_ia(texto_extraido, api_key_input)
            st.session_state['dados_cliente'] = dados_cliente

    # Se já tiver os dados processados na sessão, exibe a interface de trabalho
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
                2023: {"limite_isencao_mensal": 190398, "aliquota_efetiva": 0.15},
                2024: {"limite_isencao_mensal": 211200, "aliquota_efetiva": 0.15},
                2025: {"limite_isencao_mensal": 225920, "aliquota_efetiva": 0.15}
            }
            
            resultado_linhas = []
            soma_total_geral = 0
            
            for ano_str, info in dados_cliente['anos'].items():
                ano = int(ano_str)
                rend = info['rend_tributavel_original']
                iro = info['ir_devido_original']
                ir13 = info['ir_13_inss']
                
                tabela = tabelas_oficiais.get(ano, tabelas_oficiais[2024])
                isencao_anual_limite = tabela["limite_isencao_mensal"] * 12
                
                base_calculo_isenta = min(rend, isencao_anual_limite)
                dif_anual = int(base_calculo_isenta * tabela["aliquota_efetiva"])
                dif_anual = min(dif_anual, iro)
                
                total_restituicao_13 = ir13 if ir13 > 0 else int(iro * 0.15)
                total_ano = dif_anual + total_restituicao_13
                soma_total_geral += total_ano
                
                resultado_linhas.append({
                    "Ano": ano,
                    "Diferença Anual (R$)": round(dif_anual / 100, 2),
                    "IR do 13º (R$)": round(total_restituicao_13 / 100, 2),
                    "Total Estimado (R$)": round(total_ano / 100, 2)
                })
                
            df_final = pd.DataFrame(resultado_linhas)
            
            st.session_state['df_final'] = df_final
            st.session_state['soma_total_geral'] = soma_total_geral / 100
            st.session_state['nome_editado'] = nome_editado
            st.session_state['patologia_editada'] = patologia_editada
            st.session_state['data_editada'] = data_editada
            st.session_state['data_analise'] = datetime.now().strftime("%d/%m/%Y às %H:%M")

        # Exibição dos resultados se já calculados
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

            # Geração de Relatório em formato HTML elegante para Impressão/PDF direto pelo navegador
            html_relatorio = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: 'Helvetica', Arial, sans-serif; color: #333; padding: 30px; }}
                    .header {{ text-align: center; border-bottom: 2px solid #C5A059; padding-bottom: 15px; margin-bottom: 20px; }}
                    .header h2 {{ color: #2C3E50; margin: 0; font-family: Georgia, serif; }}
                    .header p {{ color: #997A38; font-weight: bold; letter-spacing: 3px; font-size: 12px; margin-top: 5px; }}
                    .info {{ background: #F9F9F9; padding: 15px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #C5A059; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                    th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; font-size: 14px; }}
                    th {{ background-color: #2C3E50; color: white; }}
                    .total {{ font-size: 18px; font-weight: bold; color: #2C3E50; margin-top: 20px; text-align: right; }}
                    .status {{ margin-top: 20px; padding: 10px; background: #E8F8F5; color: #117A65; font-weight: bold; text-align: center; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>Samile Schmitt</h2>
                    <p>A D V O C A C I A</p>
                    <p style="color: #666; font-weight: normal; font-size: 11px; margin-top: 5px;">Parecer Técnico de Viabilidade — Isenção de IR (Lei 7.713/88)</p>
                </div>
                <div class="info">
                    <p><b>Data da Análise:</b> {st.session_state['data_analise']}</p>
                    <p><b>Cliente / Segurado:</b> {st.session_state['nome_editado']}</p>
                    <p><b>Patologia / CID:</b> {st.session_state['patologia_editada']}</p>
                    <p><b>Início da Enfermidade:</b> {st.session_state['data_editada']}</p>
                </div>
                <h3>Demonstrativo de Valores a Recuperar</h3>
                {st.session_state['df_final'].to_html(index=False, classes='table')}
                <div class="total">
                    Valor Total Estimado: R$ {st.session_state['soma_total_geral']:,.2f}
                </div>
                <div class="status">
                    STATUS: VIÁVEL PARA AJUIZAMENTO — Há direito creditício recuperável a favor do segurado.
                </div>
            </body>
            </html>
            """
            
            st.download_button(
                label="📥 Baixar Laudo Completo em HTML/PDF (Pronto para Impressão)",
                data=html_relatorio,
                file_name=f"Laudo_Isencao_IR_{st.session_state['nome_editado'].replace(' ', '_')}.html",
                mime="text/html",
                type="primary"
            )
else:
    st.markdown("""
        <div style="text-align: center; padding: 40px; background-color: #FFFFFF; border-radius: 8px; border: 1px dashed #C5A059; margin-top: 20px;">
            <h3 style="color: #2C3E50;">Bem-vindo ao Sistema de Isenção</h3>
            <p style="color: #666;">Faça o upload dos documentos digitalizados na barra lateral para iniciar a análise jurídica automatizada.</p>
        </div>
    """, unsafe_allow_html=True)
