import streamlit as st
import pandas as pd
import json
import os

# --- NOME DO ARQUIVO PARA SALVAR AS COMBINAÇÕES ---
SAVE_FILE = 'saved_selections_web.json'

# --- Função para carregar e processar os dados do Excel (versão completa) ---
@st.cache_data # Cache para performance
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
    IGNORE_KEYWORDS = ["opções", "dieta", "refeição", "alimento"]
    for _, row in df.iterrows():
        if len(row) < 7: continue
        meal_name_raw = row[0]
        if pd.notna(meal_name_raw) and isinstance(meal_name_raw, str):
            meal_name = meal_name_raw.strip()
            if meal_name and not any(keyword in meal_name.lower() for keyword in IGNORE_KEYWORDS):
                refeicoes_planilha[meal_name] = {'Gordura': 0, 'Carboidrato': 0, 'Proteína': 0, 'Calorias': 0, 'Items': []}

    current_meal_valid = None
    for _, row in df.iterrows():
        meal_name_raw = row[0]
        if pd.notna(meal_name_raw) and isinstance(meal_name_raw, str):
            meal_name = meal_name_raw.strip()
            if meal_name in refeicoes_planilha:
                current_meal_valid = meal_name
        
        if current_meal_valid:
            food_name_raw, quantity_raw = row[1], row[2]
            if pd.notna(food_name_raw) and isinstance(food_name_raw, str) and food_name_raw.strip():
                item_str = f"- {quantity_raw or ''} {food_name_raw.strip()}"
                substitution_str = None
                if len(row) > 7 and pd.notna(row[7]) and isinstance(row[7], str):
                    substitution_str = row[7].strip()
                item_data = {'item': item_str, 'sub': substitution_str}
                refeicoes_planilha[current_meal_valid]['Items'].append(item_data)

            try:
                g, c, p, k = float(row[3]), float(row[4]), float(row[5]), float(row[6])
                if pd.notna(g): refeicoes_planilha[current_meal_valid]['Gordura'] += g
                if pd.notna(c): refeicoes_planilha[current_meal_valid]['Carboidrato'] += c
                if pd.notna(p): refeicoes_planilha[current_meal_valid]['Proteína'] += p
                if pd.notna(k): refeicoes_planilha[current_meal_valid]['Calorias'] += k
            except (ValueError, TypeError, IndexError):
                continue
    
    ORDER_KEY = ["Café", "Treino", "Almoço", "Lanche", "Janta", "Ceia"]
    def sort_key(meal_name):
        for i, key in enumerate(ORDER_KEY):
            if key in meal_name: return (i, meal_name)
        return (len(ORDER_KEY), meal_name)
    
    return dict(sorted(refeicoes_planilha.items(), key=lambda item: sort_key(item[0])))

# --- Funções para carregar e salvar combinações ---
def load_saved_selections():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_selections_to_file(selections):
    with open(SAVE_FILE, 'w') as f:
        json.dump(selections, f, indent=4)

# --- Interface do Aplicativo Web ---
st.set_page_config(layout="wide", page_title="Calculadora de Dieta")
st.title("📱 Calculadora de Dieta Completa")

# Carrega os dados da planilha
meal_data = load_meal_data('Dieta.xlsx')

if meal_data:
    lista_de_refeicoes = list(meal_data.keys())

    # --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
    if 'saved_selections' not in st.session_state:
        st.session_state.saved_selections = load_saved_selections()
    if 'current_selection' not in st.session_state:
        st.session_state.current_selection = []

    # --- PAINEL LATERAL (SIDEBAR) PARA SALVAR/CARREGAR ---
    with st.sidebar:
        st.header("Combinações Salvas")
        
        saved_options = list(st.session_state.saved_selections.keys())
        if not saved_options:
            st.write("Nenhuma combinação salva.")
        
        # Carregar combinação
        selected_to_load = st.selectbox("Carregar uma combinação:", saved_options, index=None, placeholder="Escolha para carregar...")
        if st.button("Carregar", use_container_width=True) and selected_to_load:
            st.session_state.current_selection = st.session_state.saved_selections[selected_to_load]
            st.rerun()

        # Salvar combinação
        st.write("---")
        save_name = st.text_input("Nome para salvar a seleção atual:")
        if st.button("Salvar", use_container_width=True) and save_name:
            if st.session_state.current_selection:
                st.session_state.saved_selections[save_name] = st.session_state.current_selection
                save_selections_to_file(st.session_state.saved_selections)
                st.success(f"'{save_name}' salva!")
            else:
                st.warning("Selecione algumas refeições primeiro!")
        
        # Excluir combinação
        st.write("---")
        selected_to_delete = st.selectbox("Excluir uma combinação:", saved_options, index=None, placeholder="Escolha para excluir...")
        if st.button("Excluir", type="primary", use_container_width=True) and selected_to_delete:
            del st.session_state.saved_selections[selected_to_delete]
            save_selections_to_file(st.session_state.saved_selections)
            st.success(f"'{selected_to_delete}' excluída!")
            st.rerun()


    # --- PAINEL PRINCIPAL ---
    st.header("Selecione suas Refeições:")
    
    refeicoes_selecionadas = st.multiselect(
        label="Escolha as refeições para somar os macros:",
        options=lista_de_refeicoes,
        default=st.session_state.current_selection, # Usa o estado da sessão para definir o padrão
        label_visibility="collapsed"
    )
    # Atualiza o estado da sessão com a seleção atual do usuário
    st.session_state.current_selection = refeicoes_selecionadas
    
    st.write("---")

    if refeicoes_selecionadas:
        totals = {'Gordura': 0, 'Carboidrato': 0, 'Proteína': 0, 'Calorias': 0}
        individual_macros = []

        for meal_name in refeicoes_selecionadas:
            macros = meal_data[meal_name]
            totals['Gordura'] += macros['Gordura']
            totals['Carboidrato'] += macros['Carboidrato']
            totals['Proteína'] += macros['Proteína']
            totals['Calorias'] += macros['Calorias']
            individual_macros.append({
                'Refeição': meal_name,
                'Calorias': macros['Calorias'],
                'Carboidratos': macros['Carboidrato'],
                'Proteínas': macros['Proteína'],
                'Gorduras': macros['Gordura']
            })

        st.header("📊 Totais da sua Seleção:")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🔥 Calorias", f"{totals['Calorias']:.1f} kcal")
        col2.metric("🍞 Carboidratos", f"{totals['Carboidrato']:.1f} g")
        col3.metric("🥩 Proteínas", f"{totals['Proteína']:.1f} g")
        col4.metric("🥑 Gorduras", f"{totals['Gordura']:.1f} g")
        
        st.write("---")

        # --- PAINEL DE MACROS INDIVIDUAIS ---
        st.header("📋 Macros por Refeição:")
        df_individual = pd.DataFrame(individual_macros)
        st.dataframe(df_individual.style.format("{:.1f}", subset=['Calorias', 'Carboidratos', 'Proteínas', 'Gorduras']), use_container_width=True)

        # --- PAINEL DE PRÉ-VISUALIZAÇÃO DE ALIMENTOS ---
        st.header("🥗 Alimentos da Seleção:")
        with st.expander("Clique aqui para ver os detalhes dos alimentos"):
            for meal_name in refeicoes_selecionadas:
                st.subheader(f"{meal_name}")
                items = meal_data[meal_name].get('Items', [])
                if items:
                    for item_data in items:
                        main_item = item_data['item']
                        sub_item = item_data.get('sub')
                        if sub_item:
                            # Usa a sintaxe de markdown do Streamlit para o itálico
                            st.markdown(f"{main_item}  / *{sub_item}*")
                        else:
                            st.markdown(main_item)
                else:
                    st.write("Nenhum alimento detalhado.")
                st.write("") # Adiciona um espaço

    else:
        st.info("⬅️ Selecione uma ou mais refeições ou carregue uma combinação na barra lateral.")