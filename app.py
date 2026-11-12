import streamlit as st
import pandas as pd
import pypdf
import google.generativeai as genai
import json

# Configuração da Página
st.set_page_config(page_title="Sistema de Isenção de IR - Doença Grave", layout="wide")

st.title("⚖️ Sistema Interno do Escritório")
st.subheader("Análise Automatizada de Isenção de IR com Leitura de PDFs por IA")

with st.sidebar:
    st.header("📂 Importação de Documentos")
    st.info("Envie os PDFs (Laudo Médico, IRPF e HISCRE do INSS).")
    
    # Upload dos PDFs
    arquivos_pdf = st.file_uploader(
        "Arraste os PDFs do Cliente Aqui", 
        type=["pdf"], 
        accept_multiple_files=True
    )
    
    # Chave da API do Gemini
    api_key_input = st.text_input("Chave da API Gemini (Google AI Studio)", type="password", help="Insira sua chave para ativar a extração automática por IA.")

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
    Você é um assistente jurídico especializado em direito tributário e previdenciário (Lei 7.713/88).
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
    st.success(f"{len(arquivos_pdf)} documento(s) carregado(s) com sucesso!")
    
    # Botão para disparar a leitura controlada
    if st.button("🤖 Iniciar Leitura Automática com IA", type="primary"):
        with st.spinner("A Inteligência Artificial está lendo os documentos... Aguarde um instante."):
            texto_extraido = extrair_texto_pdfs(arquivos_pdf)
            dados_cliente = analisar_documentos_com_ia(texto_extraido, api_key_input)
            
            # Guarda os dados na sessão do Streamlit
            st.session_state['dados_cliente'] = dados_cliente

    # Se já tiver os dados processados na sessão, exibe a tela de conferência e cálculo
    if 'dados_cliente' in st.session_state and st.session_state['dados_cliente']:
        dados_cliente = st.session_state['dados_cliente']
        
        st.markdown("### 📋 Dados Identificados Automaticamente pela IA")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Segurado", dados_cliente.get("nome_cliente", ""))
        with col2:
            st.metric("Patologia / CID", dados_cliente.get("patologia_cid", ""))
        with col3:
            st.metric("Início da Doença", dados_cliente.get("data_inicio_doenca", ""))
            
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
            
            st.success("Análise concluída com sucesso!")
            st.dataframe(df_final, use_container_width=True)
            st.metric(label="💰 VALOR TOTAL ESTIMADO DA RESTITUIÇÃO / ATRASADOS", value=f"R$ {soma_total_geral/100:,.2f}")
            
            if soma_total_geral > 0:
                st.markdown("🟢 **STATUS:** `VIÁVEL PARA AJUIZAMENTO` — Há direito creditício recuperável.")
            else:
                st.markdown("🔴 **STATUS:** `INVIÁVEL` — Sem diferença apurada no período.")
else:
    st.info("👈 Insira sua Chave da API do Gemini na barra lateral e faça o upload dos PDFs do cliente para iniciar.")
