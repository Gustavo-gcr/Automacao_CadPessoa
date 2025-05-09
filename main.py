# import streamlit as st
# import pandas as pd
# import re

# # Função para validar erros em cada campo
# def verificar_erros(row):
#     erros = {}
    
#     # Verifica se os campos estão em maiúsculas (exceto se estiverem vazios ou nulos)
#     for campo, descricao in [('nome_pes', 'Razão Social'), ('NomeFant_Pes', 'Nome Fantasia'), ('Endereco_pend', 'Endereço'), ('Bairro_pend', 'Bairro'), ('Cidade_pend', 'Cidade')]:
#         if pd.notna(row[campo]) and isinstance(row[campo], str) and not row[campo].isupper():
#             erros[descricao] = 'Deve estar em maiúsculas'
             
#     # Verifica o campo Conta_pcb    
#     conta = str(row['Conta_pcb']).strip()
#     if conta is None or str(conta).strip() == "":
#         # Nenhum erro; conta nula ou vazia está correta
#         pass
#     else:
#         # Converte para string e remove espaços ao redor
#         conta = str(conta).strip()
        
#         # 2. Verifica espaços excedentes no meio do valor
#         if ' ' in conta:
#             erros['Conta'] = 'Conta possui espaços excedentes no meio do texto.'
        
            
#     # Verifica se o email está todo em minúsculas (exceto se estiver vazio ou nulo)
#     email = str(row['Email_pes']).strip()
#     if email and email != email.lower():
#         erros['Email'] = 'Email deve estar em minúsculas'
    
#     # Verifica espaços excedentes apenas no início de cada campo (exceto se estiver vazio ou nulo)
#     for campo, descricao in [('cod_pes', 'Código'), ('Email_pes', 'Email'), ('nome_pes', 'Razão Social'), ('NomeFant_Pes', 'Nome Fantasia'), ('Endereco_pend', 'Endereço'), ('Bairro_pend', 'Bairro'), ('Cidade_pend', 'Cidade'), ('Agencia_pcb', 'Agência'), ('Banco_pcb', 'Banco'), ('Conta_pcb', 'Conta')]:
#         if pd.notna(row[campo]) and isinstance(row[campo], str) and row[campo].startswith(' '):
#             erros[descricao] = 'Espaço excedente no início'

#     return erros if erros else None

# # Carregar arquivo e validar
# st.title("Validação de Planilha de Cadastro")

# uploaded_file = st.file_uploader("Carregar arquivo Excel", type=["xlsx"])

# if uploaded_file:
#     df = pd.read_excel(uploaded_file)
#     erros_lista = []
    
#     # Iterar nas linhas e verificar erros
#     for index, row in df.iterrows():
#         erros = verificar_erros(row)
#         if erros:
#             linha_com_erros = row.to_dict()
#             linha_com_erros['Erros'] = erros
#             erros_lista.append(linha_com_erros)
    
#     if erros_lista:
#         # Criar DataFrame com as linhas que contêm erros
#         df_erros = pd.DataFrame(erros_lista)
#         st.write("Linhas com erros encontrados:")
#         st.dataframe(df_erros)

#         # Permitir download da nova planilha com erros
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

# Verifica se há caracteres especiais ou acentos
def contem_acentos_ou_especiais(texto):
    return bool(re.search(r'[çÇáàâãéêíîóôõúûüÁÀÂÃÉÊÍÎÓÔÕÚÛÜ]', texto))

# Função para verificar erros em uma linha da planilha
def verificar_erros(row):
    erros = {}

    # Verifica se os campos estão em maiúsculas
    for campo, descricao in [
        ('nome_pes', 'Razão Social'),
        ('NomeFant_Pes', 'Nome Fantasia'),
        ('Endereco_pend', 'Endereço'),
        ('Bairro_pend', 'Bairro'),
        ('Cidade_pend', 'Cidade')
    ]:
        valor = row.get(campo)
        if pd.notna(valor) and isinstance(valor, str) and not valor.isupper():
            erros[descricao] = 'Deve estar em maiúsculas'

    # Verifica acentos e caracteres especiais em Razão Social e Nome Fantasia
    for campo, descricao in [('nome_pes', 'Razão Social'), ('NomeFant_Pes', 'Nome Fantasia')]:
        valor = row.get(campo)
        if pd.notna(valor) and isinstance(valor, str):
            if contem_acentos_ou_especiais(valor):
                erros[descricao] = 'Contém acento ou caractere especial.'

    # Verifica se o campo Conta possui espaços internos
    conta = str(row.get('Conta_pcb')).strip()
    if conta and ' ' in conta:
        erros['Conta'] = 'Conta possui espaços excedentes no meio do texto.'

    # Verifica se o e-mail está todo em minúsculas
    email = str(row.get('Email_pes')).strip()
    if email and email != email.lower():
        erros['Email'] = 'Email deve estar em minúsculas'

    # Verifica espaços no início de campos
    campos_para_verificar = [
        ('cod_pes', 'Código'), ('Email_pes', 'Email'), ('nome_pes', 'Razão Social'),
        ('NomeFant_Pes', 'Nome Fantasia'), ('Endereco_pend', 'Endereço'),
        ('Bairro_pend', 'Bairro'), ('Cidade_pend', 'Cidade'),
        ('Agencia_pcb', 'Agência'), ('Banco_pcb', 'Banco'), ('Conta_pcb', 'Conta')
    ]

    for campo, descricao in campos_para_verificar:
        valor = row.get(campo)
        if pd.notna(valor) and isinstance(valor, str) and valor.startswith(' '):
            erros[descricao] = 'Espaço excedente no início'

    return erros if erros else None

# Interface do Streamlit
st.title("Validação de Planilha de Cadastro")

uploaded_file = st.file_uploader("Carregar arquivo Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    erros_lista = []

    # Verifica erros linha por linha
    for index, row in df.iterrows():
        erros = verificar_erros(row)
        if erros:
            linha_com_erros = row.to_dict()
            linha_com_erros['Erros'] = erros
            erros_lista.append(linha_com_erros)

    # Exibe e exporta resultados
    if erros_lista:
        df_erros = pd.DataFrame(erros_lista)
        st.write("Linhas com erros encontrados:")
        st.dataframe(df_erros)

        output_file = "erros_planilha.xlsx"
        df_erros.to_excel(output_file, index=False)

        with open(output_file, "rb") as file:
            st.download_button(
                label="Baixar planilha com erros",
                data=file,
                file_name="erros_planilha.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.success("Nenhum erro encontrado na planilha.")
