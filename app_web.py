import streamlit as st
import pandas as pd

# --- Função para carregar e processar os dados do Excel (a mesma de antes) ---
@st.cache_data # Adiciona cache para não recarregar o arquivo toda hora
def load_meal_data(filename):
    try:
        df = pd.read_excel(filename, sheet_name='Planilha1', header=None)
    except FileNotFoundError:
        st.error(f"Erro: Arquivo '{filename}' não encontrado! Coloque-o na mesma pasta do aplicativo.")
        return None
    except Exception as e:
        st.error(f"Erro de Leitura: Não foi possível ler o arquivo Excel.\nErro: {e}")
        return None

    refeicoes_planilha = {}
    refeicao_atual = None
    for _, row in df.iterrows():
        if len(row) < 7: continue
        nome_refeicao = row[0]
        if pd.notna(nome_refeicao) and isinstance(nome_refeicao, str) and len(nome_refeicao.strip()) > 0:
            refeicao_atual = nome_refeicao.strip()
            if refeicao_atual not in refeicoes_planilha:
                refeicoes_planilha[refeicao_atual] = {'Gordura': 0, 'Carboidrato': 0, 'Proteína': 0, 'Calorias': 0}
        if refeicao_atual:
            try:
                gordura, carbo, prot, cal = float(row[3]), float(row[4]), float(row[5]), float(row[6])
                if pd.notna(gordura): refeicoes_planilha[refeicao_atual]['Gordura'] += gordura
                if pd.notna(carbo): refeicoes_planilha[refeicao_atual]['Carboidrato'] += carbo
                if pd.notna(prot): refeicoes_planilha[refeicao_atual]['Proteína'] += prot
                if pd.notna(cal): refeicoes_planilha[refeicao_atual]['Calorias'] += cal
            except (ValueError, TypeError, IndexError):
                continue
    return refeicoes_planilha

# --- Interface do Aplicativo Web ---
st.set_page_config(layout="wide")
st.title("📱 Calculadora de Dieta")

meal_data = load_meal_data('Dieta.xlsx')

if meal_data:
    lista_de_refeicoes = list(meal_data.keys())
    
    st.header("Selecione suas Refeições:")
    
    # Cria uma caixa de seleção múltipla
    refeicoes_selecionadas = st.multiselect(
        label="Escolha as refeições para somar os macros:",
        options=lista_de_refeicoes,
        label_visibility="collapsed" # Esconde o texto do label de cima
    )
    
    st.write("---") # Linha divisória

    if refeicoes_selecionadas:
        totals = {'Gordura': 0, 'Carboidrato': 0, 'Proteína': 0, 'Calorias': 0}
        for meal_name in refeicoes_selecionadas:
            macros = meal_data[meal_name]
            totals['Gordura'] += macros['Gordura']
            totals['Carboidrato'] += macros['Carboidrato']
            totals['Proteína'] += macros['Proteína']
            totals['Calorias'] += macros['Calorias']

        st.header("Totais da sua Seleção:")
        
        # Exibe os resultados em colunas
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🔥 Calorias", f"{totals['Calorias']:.1f} kcal")
        col2.metric("🍞 Carboidratos", f"{totals['Carboidrato']:.1f} g")
        col3.metric("🥩 Proteínas", f"{totals['Proteína']:.1f} g")
        col4.metric("🥑 Gorduras", f"{totals['Gordura']:.1f} g")
    else:
        st.info("Selecione uma ou mais refeições acima para ver o resultado.")