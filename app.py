import streamlit as st
import pandas as pd
import pypdf
import google.generativeai as genai
import json
import io
from datetime import datetime, timedelta, timezone
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

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
            
            fuso_br = timezone(timedelta(hours=-3))
            st.session_state['data_analise'] = datetime.now(fuso_br).strftime("%d/%m/%Y às %H:%M")

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

            # Geração do PDF Real usando ReportLab
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
            story = []
            
            styles = getSampleStyleSheet()
            style_title = ParagraphStyle('Title', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, textColor=colors.HexColor('#2C3E50'), alignment=1)
            style_subtitle = ParagraphStyle('Subtitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#997A38'), alignment=1, spaceAfter=15)
            style_heading2 = ParagraphStyle('Heading2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#2C3E50'), spaceBefore=10, spaceAfter=5)
            style_body = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=colors.HexColor('#333333'), spaceAfter=6, leading=14)
            
            story.append(Paragraph("Samile Schmitt", style_title))
            story.append(Paragraph("A D V O C A C I A", style_subtitle))
            story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#C5A059'), spaceAfter=15))
            
            story.append(Paragraph("Parecer Tecnico Previdenciario / Tributario - Isencao de IR (Lei 7.713/88)", style_heading2))
            story.append(Paragraph(f"<b>Data da Analise:</b> {st.session_state['data_analise']}", style_body))
            story.append(Paragraph(f"<b>Cliente / Segurado:</b> {st.session_state['nome_editado']}", style_body))
            story.append(Paragraph(f"<b>Patologia / CID:</b> {st.session_state['patologia_editada']}", style_body))
            story.append(Paragraph(f"<b>Inicio da Enfermidade:</b> {st.session_state['data_editada']}", style_body))
            story.append(Spacer(1, 10))
            
            story.append(Paragraph("<b>Demonstrativo Consolidado de Creditos Tributarios</b>", style_heading2))
            
            tabela_dados = [["Ano", "Rend. Tributavel (R$)", "IR Retido (R$)", "Credito Restituivel (R$)"]]
            for row in st.session_state['df_final'].values.tolist():
                tabela_dados.append([str(row[0]), f"R$ {row[1]:,.2f}", f"R$ {row[3]:,.2f}", f"R$ {row[4]:,.2f}"])
                
            t = Table(tabela_dados, colWidths=[50, 160, 140, 190])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2C3E50')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#EAE6DF')),
            ]))
            story.append(t)
            story.append(Spacer(1, 10))
            
            story.append(Paragraph(f"<b>MONTANTE TOTAL DE RESTITUICAO APURADO: R$ {st.session_state['soma_total_geral']:,.2f}</b>", style_heading2))
            story.append(Spacer(1, 5))
            
            story.append(Paragraph("<b>Fundamentacao Tecnica e Memoria de Calculo</b>", style_heading2))
            story.append(Paragraph("A presente auditoria fiscal fundamenta-se estritamente no artigo 6o, inciso XIV, da <b>Lei no 7.713/88</b>, que assegura a isencao tributaria integral sobre proventos percebidos por portadores de molestia grave a partir da comprovacao medica da enfermidade.", style_body))
            
            for item in st.session_state['memoria']:
                texto_mem = f"• <b>Exercicio {item['ano']}</b>: Rendimento de R$ {item['rend']:,.2f} (Teto Legal de Referencia: R$ {item['teto']:,.2f}) — IR Retido Indevido: <b>R$ {item['restituicao']:,.2f}</b>."
                story.append(Paragraph(texto_mem, style_body))
                
            story.append(Spacer(1, 10))
            story.append(Paragraph("<b>Conclusao Estratégica:</b> O caso apresenta viabilidade jurídica plena, totalizando créditos passíveis de repetição de indébito apurados com exatidão.", style_body))
            
            doc.build(story)
            pdf_data = buffer.getvalue()
            
            st.download_button(
                label="📥 Baixar Laudo Oficial em PDF",
                data=pdf_data,
                file_name=f"Laudo_Isencao_IR_{st.session_state['nome_editado'].replace(' ', '_')}.pdf",
                mime="application/pdf",
                type="primary"
            )
else:
    st.markdown("""
        <div style="text-align: center; padding: 40px; background-color: #FFFFFF; border-radius: 8px; border: 1px dashed #C5A059; margin-top: 20px;">
            <h3 style="color: #2C3E50;">Sistema de Isenção de IR</h3>
            <p style="color: #666;">Insira sua chave de API na barra lateral e faça o upload dos documentos fiscais para iniciar a auditoria técnica.</p>
        </div>
    """, unsafe_allow_html=True)
