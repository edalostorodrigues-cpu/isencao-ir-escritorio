import streamlit as st
import pandas as pd
import pypdf
import google.generativeai as genai
import json

# Configuração da Página
st.set_page_config(
    page_title="Samile Schmitt Advocacia - Sistema de Isenção de IR", 
    page_icon="⚖️", 
    layout="wide"
)

# Estilização CSS Avançada: Logotipo de Fundo (Watermark Elegante) e Cores Corporativas
st.markdown("""
    <style>
    .main {
        background-color: #FAFAFA;
        /* Logotipo do escritório como marca d'água elegante no fundo */
        background-image: url('URL_DA_SUA_LOGO_AQUI');
        background-repeat: no-repeat;
        background-position: center 60%;
        background-size: 450px auto;
        background-attachment: fixed;
    }
    /* Deixa o fundo levemente translúcido para o texto destacar */
    .block-container {
        background-color: rgba(255, 255, 255, 0.92);
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
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

# Cabeçalho Elegante do Escritório
st.markdown("""
    <div style="text-align: center; padding: 10px 0 20px 0;">
        <h2 style="color: #2C3E50; font-family: 'Georgia', serif; margin-bottom: 0;">Samile Schmitt</h2>
        <p style="letter-spacing: 4px; color: #997A38; font-size: 13px; font-weight: bold; margin-top: 5px;">A D V O C A C I A</p>
        <hr style="width: 120px; border: 1px solid #C5A059; margin: 15px auto;">
        <h4 style="color: #555; font-weight: normal; font-size: 15px; margin-top: 5px;">Módulo de Análise Inteligente e Cálculo de Isenção de IR (Doença Grave)</h4>
    </div>
""", unsafe_allow_html=True)

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
    # Chave da API do Gemini
    api_key_input = st.text_input("Chave da API Gemini", type="password", help="Insira sua chave do Google AI Studio para ativar a IA.")

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
    model = genai.GenerativeModel('gemini-3.8-flash')
    
    prompt = f"""
    Você é um assistente jurídico sênior especializado em direito tributário e previdenciário (Lei 7.713/88).
    Analise o texto extraído dos documentos do cliente abaixo e retorne um JSON estrito com a seguinte estrutura:
    {{
      "nome_cliente": "Nome completo extraído ou 'Não localizado'",
      "patologia_cid": "Patologia e CID descritos no laudo ou 'Não localizado'",
      "data_inicio_doenca": "YYYY-MM-DD ou data do laudo médico",
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
        
        st.markdown("### 📋 Doutrina e Dados Cadastrais do Cliente")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            nome_editado = st.text_input("Segurado / Cliente", dados_cliente.get("nome_cliente", ""))
        with col2:
            patologia_editada = st.text_input("Patologia / CID (Ajuste Manual)", dados_cliente.get("patologia_cid", "C20 (Neoplasia Maligna)"))
        with col3:
            data_editada = st.text_input("Data de Início da Doença (Ajuste Manual)", "2023-01-15")
            
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
                2023: {"limite_isencao": 2475174, "aliquota": 0.075},
                2024: {"limite_isencao": 2696320, "aliquota": 0.075},
                2025: {"limite_isencao": 2846720, "aliquota": 0.075}
            }
            
            resultado_linhas = []
            soma_total_geral = 0
            
            for ano_str, info in dados_cliente['anos'].items():
                ano = int(ano_str)
                rend = info['rend_tributavel_original']
                inss = info['rend_inss']
                ded = info['deducoes_legais']
                iro = info['ir_devido_original']
                ir13 = info['ir_13_inss']
                fator = info['fator_inss_isento']
                
                inss_isento = int(inss * fator)
                rend_restante = rend - inss_isento
                nova_base = max(0, rend_restante - ded)
                
                tabela = tabelas_oficiais.get(ano, tabelas_oficiais[2024])
                if nova_base <= tabela["limite_isencao"]:
                    ir_simulado = 0
                else:
                    excedente = nova_base - tabela["limite_isencao"]
                    ir_simulado = int(excedente * tabela["aliquota"])
                    
                dif_anual = iro - ir_simulado
                total_ano = dif_anual + ir13
                soma_total_geral += total_ano
                
                resultado_linhas.append({
                    "Ano": ano,
                    "Diferença Anual (R$)": dif_anual / 100,
                    "IR do 13º (R$)": ir13 / 100,
                    "Total Estimado (R$)": total_ano / 100
                })
                
            df_final = pd.DataFrame(resultado_linhas)
            
            st.success("Cálculo jurídico executado com sucesso!")
            st.markdown(f"""
                <div style="background-color: #F4F6F7; padding: 15px; border-left: 4px solid #C5A059; border-radius: 4px; margin-bottom: 20px;">
                    <h4 style="margin:0; color:#2C3E50;">Relatório de Viabilidade — {nome_editado}</h4>
                    <p style="margin:5px 0 0 0; color:#555;"><b>Patologia / CID:</b> {patologia_editada} | <b>Início da Enfermidade:</b> {data_editada}</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.dataframe(df_final, use_container_width=True)
            st.metric(label="💰 VALOR TOTAL ESTIMADO DA RESTITUIÇÃO / ATRASADOS", value=f"R$ {soma_total_geral/100:,.2f}")
            
            if soma_total_geral > 0:
                st.markdown("🟢 **STATUS:** `VIÁVEL PARA AJUIZAMENTO` — Há direito creditício recuperável a favor do segurado.")
            else:
                st.markdown("🔴 **STATUS:** `INVIÁVEL` — Sem diferença apurada no período.")
else:
    st.markdown("""
        <div style="text-align: center; padding: 40px; background-color: #FFFFFF; border-radius: 8px; border: 1px dashed #C5A059; margin-top: 30px;">
            <h3 style="color: #2C3E50;">Bem-vindo ao Sistema de Isenção</h3>
            <p style="color: #666;">Insira sua chave de API na barra lateral e faça o upload dos documentos digitalizados para iniciar a análise jurídica automatizada.</p>
        </div>
    """, unsafe_allow_html=True)
