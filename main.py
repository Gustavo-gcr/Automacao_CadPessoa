import streamlit as st
import pandas as pd
import re
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Validador de Cadastro", page_icon="✅", layout="wide")

# --- FUNÇÕES DE VALIDAÇÃO ---

def contem_acentos(texto):
    """
    Retorna True APENAS se tiver letras com acento ou cedilha.
    Hifens (-), E comercial (&) e pontos (.) já são ignorados pelo Regex abaixo.
    """
    if not isinstance(texto, str): return False
    # Regex busca apenas: á, à, â, ã, é, ê, í, ó, ô, õ, ú, ü, ç (e maiúsculas)
    return bool(re.search(r'[çÇáàâãéêíîóôõúûüÁÀÂÃÉÊÍÎÓÔÕÚÛÜ]', texto))

def verificar_espacos(texto):
    """Retorna lista de erros de espaçamento (Início, Fim e Duplos)."""
    erros = []
    if not isinstance(texto, str): return erros
    
    # Espaço no início ou fim
    if texto.startswith(' '): erros.append("Espaço no INÍCIO")
    if texto.endswith(' '): erros.append("Espaço no FINAL")
    
    # Espaço duplo (dois ou mais espaços seguidos)
    if re.search(r'\s{2,}', texto): 
        erros.append("Espaço DUPLO")
        
    return erros

def validar_linha(row):
    """
    Analisa a linha e retorna uma STRING com os erros encontrados.
    """
    lista_erros = []

    # --- MAPEAMENTO DE REGRAS ---
    regras_map = [
        ('nome_pes', 'Razão Social', ['upper', 'no_accents']),
        ('NomeFant_Pes', 'Nome Fantasia', ['upper', 'no_accents']),
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
        
        # --- 1. TRATAMENTO DE VALORES NULOS/VAZIOS ---
        val_str = str(val).strip()
        
        # LISTA NEGRA DE NULOS:
        # Se o campo estiver vazio, nulo ou for "nan", o código executa o 'continue'.
        # Isso PULA as validações abaixo. Logo, Nome Fantasia vazio não gera erro.
        if not val_str or val_str.lower() in ['nan', 'none', 'null', 'nat', '']:
            continue 
            
        # --- 2. PREPARAÇÃO DO TEXTO (IGNORAR SIMBOLOS) ---
        # Removemos ponto, hífen e & apenas para checar se é maiúsculo/minúsculo
        val_analise = val_str.replace('-', '').replace('.', '').replace('&', '')

        # --- VALIDAÇÕES ---
        
        # A. Validação de Espaços (Usa o texto original, pois espaço importa)
        erros_espaco = verificar_espacos(val_str)
        if erros_espaco:
            lista_erros.append(f"[{nome_amigavel}]: " + ", ".join(erros_espaco))

        # Verifica se sobrou alguma letra após limpar os símbolos
        tem_letras = any(c.isalpha() for c in val_analise)

        # B. Regra: Maiúsculas (UPPER)
        if 'upper' in regras and tem_letras:
            # Se tiver letras e não for tudo maiúsculo (ignorando símbolos)
            if not val_analise.isupper():
                lista_erros.append(f"[{nome_amigavel}]: Deve ser MAIÚSCULO")
            
        # C. Regra: Minúsculas (LOWER - E-mail)
        if 'lower' in regras and tem_letras:
            if not val_analise.islower():
                lista_erros.append(f"[{nome_amigavel}]: Deve ser minúsculo")
            
        # D. Regra: Sem Acentos (NO_ACCENTS)
        if 'no_accents' in regras and contem_acentos(val_str):
            lista_erros.append(f"[{nome_amigavel}]: Contém acento")
            
        # E. Regra: Sem espaços internos (Conta)
        if 'no_spaces_inner' in regras and ' ' in val_str:
            lista_erros.append(f"[{nome_amigavel}]: Não pode ter espaço interno")

    # Retorna todos os erros da linha separados por "|" ou None se estiver limpo
    return " | ".join(lista_erros) if lista_erros else None

# --- INTERFACE VISUAL (STREAMLIT) ---
st.title("🛡️ Validador de Planilha")
st.markdown("""
**Regras Ativas:**
- `Vazios`: Campos vazios são ignorados (não geram erro).
- `Maiúsculas`: Endereço, Bairro, Cidade, Nomes. **(Ignora hífens, pontos e &)**.
- `Minúsculas`: E-mail.
- `Acentos`: Proibidos em Razão Social e Fantasia.
- `Espaços`: Verifica espaços duplos ou no início/fim.
""")

uploaded_file = st.file_uploader("Carregar arquivo (.xlsx ou .csv)", type=["xlsx", "csv"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, dtype=str, keep_default_na=False)
        else:
            df = pd.read_excel(uploaded_file, dtype=str)

        df.columns = df.columns.str.strip()
        
        with st.spinner('Validando linhas...'):
            df['LOG_VALIDACAO'] = df.apply(validar_linha, axis=1)
            
            df_erros = df[df['LOG_VALIDACAO'].notna()].copy()
            
            total_linhas = len(df)
            qtd_erros = len(df_erros)
            
        st.divider()
        
        col1, col2 = st.columns(2)
        col1.metric("Total de Linhas", total_linhas)
        col2.metric("Linhas com Erros", qtd_erros, delta_color="inverse")

        if qtd_erros > 0:
            st.error(f"Encontramos {qtd_erros} linhas com problemas.")
            
            st.write("### Visualização dos Erros")
            cols_visuais = ['LOG_VALIDACAO'] + [c for c in df_erros.columns if c != 'LOG_VALIDACAO']
            st.dataframe(df_erros[cols_visuais], hide_index=True)
            
            buffer = io.BytesIO()
            
            try:
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_erros.to_excel(writer, index=False, sheet_name='Erros')
            except ModuleNotFoundError:
                st.warning("Aviso: Módulo 'xlsxwriter' não encontrado. Usando gravador padrão.")
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_erros.to_excel(writer, index=False, sheet_name='Erros')
            
            buffer.seek(0)
            
            st.download_button(
                label="⬇️ Baixar Relatório de Erros (.xlsx)",
                data=buffer,
                file_name=f"Relatorio_Erros_{uploaded_file.name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
        else:
            st.balloons()
            st.success("✅ Tudo certo! Nenhuma linha com erro encontrada.")

    except Exception as e:
        st.error(f"Erro fatal ao processar o arquivo: {e}")