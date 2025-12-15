# import streamlit as st
# import pandas as pd
# import re

# # Verifica se há caracteres especiais ou acentos
# def contem_acentos_ou_especiais(texto):
#     return bool(re.search(r'[çÇáàâãéêíîóôõúûüÁÀÂÃÉÊÍÎÓÔÕÚÛÜ]', texto))

# # Função para verificar erros em uma linha da planilha
# def verificar_erros(row):
#     erros = {}

#     # Verifica se os campos estão em maiúsculas
#     for campo, descricao in [
#         ('nome_pes', 'Razão Social'),
#         ('NomeFant_Pes', 'Nome Fantasia'),
#         ('Endereco_pend', 'Endereço'),
#         ('Bairro_pend', 'Bairro'),
#         ('Cidade_pend', 'Cidade')
#     ]:
#         valor = row.get(campo)
#         if pd.notna(valor) and isinstance(valor, str) and not valor.isupper():
#             erros[descricao] = 'Deve estar em maiúsculas'

#     # Verifica acentos e caracteres especiais em Razão Social e Nome Fantasia
#     for campo, descricao in [('nome_pes', 'Razão Social'), ('NomeFant_Pes', 'Nome Fantasia')]:
#         valor = row.get(campo)
#         if pd.notna(valor) and isinstance(valor, str):
#             if contem_acentos_ou_especiais(valor):
#                 erros[descricao] = 'Contém acento ou caractere especial.'

#     # Verifica se o campo Conta possui espaços internos
#     conta = str(row.get('Conta_pcb')).strip()
#     if conta and ' ' in conta:
#         erros['Conta'] = 'Conta possui espaços excedentes no meio do texto.'

#     # Verifica se o e-mail está todo em minúsculas
#     email = str(row.get('Email_pes')).strip()
#     if email and email != email.lower():
#         erros['Email'] = 'Email deve estar em minúsculas'

#     # Verifica espaços no início de campos
#     campos_para_verificar = [
#         ('cod_pes', 'Código'), ('Email_pes', 'Email'), ('nome_pes', 'Razão Social'),
#         ('NomeFant_Pes', 'Nome Fantasia'), ('Endereco_pend', 'Endereço'),
#         ('Bairro_pend', 'Bairro'), ('Cidade_pend', 'Cidade'),
#         ('Agencia_pcb', 'Agência'), ('Banco_pcb', 'Banco'), ('Conta_pcb', 'Conta')
#     ]

#     for campo, descricao in campos_para_verificar:
#         valor = row.get(campo)
#         if pd.notna(valor) and isinstance(valor, str) and valor.startswith(' '):
#             erros[descricao] = 'Espaço excedente no início'

#     return erros if erros else None

# # Interface do Streamlit
# st.title("Validação de Planilha de Cadastro")

# uploaded_file = st.file_uploader("Carregar arquivo Excel", type=["xlsx"])

# if uploaded_file:
#     df = pd.read_excel(uploaded_file)
#     erros_lista = []

#     # Verifica erros linha por linha
#     for index, row in df.iterrows():
#         erros = verificar_erros(row)
#         if erros:
#             linha_com_erros = row.to_dict()
#             linha_com_erros['Erros'] = erros
#             erros_lista.append(linha_com_erros)

#     # Exibe e exporta resultados
#     if erros_lista:
#         df_erros = pd.DataFrame(erros_lista)
#         st.write("Linhas com erros encontrados:")
#         st.dataframe(df_erros)

#         output_file = "erros_planilha.xlsx"
#         df_erros.to_excel(output_file, index=False)

#         with open(output_file, "rb") as file:
#             st.download_button(
#                 label="Baixar planilha com erros",
#                 data=file,
#                 file_name="erros_planilha.xlsx",
#                 mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#             )
#     else:
#         st.success("Nenhum erro encontrado na planilha.")
import streamlit as st
import pandas as pd
import re
import io

# --- CONFIGURAÇÃO SIMPLES ---
st.set_page_config(page_title="Validador Ajustado", page_icon="✅", layout="wide")

# --- REGRAS DE NEGÓCIO ---

def verificar_caracteres_proibidos(texto):
    """
    Retorna True se contiver caracteres PROIBIDOS.
    Regra: 
    - Aceita: Letras (com acentos), Números, Espaços e Ponto (.).
    - Rejeita: Hífen (-), @, !, #, $, %, etc.
    """
    if not isinstance(texto, str): return False
    
    # Regex Explicado:
    # [^ ... ] = Significa "Qualquer coisa que NÃO seja..."
    # a-zA-Z0-9 = Letras e Números
    # \s\. = Espaços e Pontos
    # áàâã... = Acentos comuns em português (para não dar erro em "Comércio")
    # Se encontrar algo fora dessa lista (como o Hífen), retorna True (Erro).
    padrao = r'[^a-zA-Z0-9\s\.áàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ]'
    
    return bool(re.search(padrao, texto))

def verificar_espacos(texto):
    """Retorna lista de erros de espaçamento."""
    erros = []
    if not isinstance(texto, str): return erros
    
    # Validações
    if texto.startswith(' '): erros.append("Espaço no INÍCIO")
    if texto.endswith(' '): erros.append("Espaço no FINAL")
    
    # Regex para pegar 2 ou mais espaços seguidos em qualquer lugar
    if re.search(r'\s{2,}', texto): 
        erros.append("Espaço DUPLO (ou múltiplo)")
        
    return erros

def validar_linha(row):
    """
    Analisa a linha e retorna uma STRING única com todos os erros encontrados.
    """
    lista_erros = []

    # Mapeamento: (Coluna Excel, Nome Amigável, [Regras])
    regras_map = [
        ('nome_pes', 'Razão Social', ['upper', 'no_special']),
        ('NomeFant_Pes', 'Nome Fantasia', ['upper', 'no_special']),
        ('Endereco_pend', 'Endereço', ['upper']),
        ('Bairro_pend', 'Bairro', ['upper']),
        ('Cidade_pend', 'Cidade', ['upper']),
        ('Email_pes', 'Email', ['lower']),
        ('Conta_pcb', 'Conta', ['no_spaces_inner']),
        ('Agencia_pcb', 'Agência', []),
        ('Banco_pcb', 'Banco', []),
        ('cod_pes', 'Código', [])
    ]
    
    for col, nome_amigavel, regras in regras_map:
        val = row.get(col)
        
        # --- REGRA DE NULOS/VAZIOS ---
        # Converte para string e remove espaços das pontas
        val_str = str(val).strip() if not pd.isna(val) else ""

        # SE ESTIVER VAZIO, IGNORA (Não é erro, conforme solicitado)
        if not val_str or val_str.lower() == 'nan':
            continue 
            
        # Daqui para baixo, validamos apenas quem tem conteúdo escrito
        
        # 1. Checagem de Espaços (Início, Fim e Duplos)
        erros_espaco = verificar_espacos(val_str)
        if erros_espaco:
            lista_erros.append(f"[{nome_amigavel}]: " + ", ".join(erros_espaco))

        # 2. Regras Específicas
        if 'upper' in regras and not val_str.isupper():
            lista_erros.append(f"[{nome_amigavel}]: Deve ser MAIÚSCULO")
            
        if 'lower' in regras and not val_str.islower():
            lista_erros.append(f"[{nome_amigavel}]: Deve ser minúsculo")
            
        if 'no_special' in regras and verificar_caracteres_proibidos(val_str):
            lista_erros.append(f"[{nome_amigavel}]: Caractere proibido (Hífen ou Símbolo)")
            
        if 'no_spaces_inner' in regras and ' ' in val_str:
            lista_erros.append(f"[{nome_amigavel}]: Não pode ter espaço interno")

    # Retorna erros concatenados ou None se estiver tudo limpo
    return " | ".join(lista_erros) if lista_erros else None

# --- INTERFACE ---
st.title("🛡️ Validador de Planilha (Atualizado)")
st.markdown("Validações ativas: `Espaços Duplos`, `Hífens/Símbolos` e `Caixa Alta/Baixa`.")

uploaded_file = st.file_uploader("Selecione sua planilha (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        # Lê o arquivo tratando tudo como texto para evitar conversão automática de números
        df = pd.read_excel(uploaded_file, dtype=str)
        
        # Remove espaços em branco dos nomes das colunas (segurança extra)
        df.columns = df.columns.str.strip()
        
        with st.spinner('Processando validações...'):
            df['LOG_VALIDACAO'] = df.apply(validar_linha, axis=1)
            
            # Filtra APENAS linhas com erro
            df_erros = df[df['LOG_VALIDACAO'].notna()].copy()
            
            total_linhas = len(df)
            qtd_erros = len(df_erros)
            
        st.divider()
        
        c1, c2 = st.columns(2)
        c1.metric("Total Analisado", total_linhas)
        c2.metric("Linhas com Erros", qtd_erros, delta_color="inverse")

        if qtd_erros > 0:
            st.error(f"Encontramos {qtd_erros} linhas com problemas.")
            
            st.write("Visualização dos Erros:")
            # Move LOG_VALIDACAO para a primeira posição visualmente
            cols = ['LOG_VALIDACAO'] + [c for c in df_erros.columns if c != 'LOG_VALIDACAO']
            st.dataframe(df_erros[cols], hide_index=True)
            
            # Buffer para download
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_erros.to_excel(writer, index=False, sheet_name='Erros_Encontrados')
            
            buffer.seek(0)
            
            st.download_button(
                label="⬇️ Baixar Planilha de Erros",
                data=buffer,
                file_name=f"Relatorio_Erros_{uploaded_file.name}",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
        else:
            st.balloons()
            st.success("Tudo certo! Nenhuma linha com erro encontrada.")

    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")