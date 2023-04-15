# A streamlit ap which askes several question following the following logic:
import streamlit as st
import pandas as pd
from tools import corsano, loaders, jsonbin
from tools.digipall import DigiPall


# ------------------ Initialize session state & chat ------------------
if 'patient_id' not in st.session_state:
    query_params = st.experimental_get_query_params()
    st.session_state['patient_id'] = query_params.get('id', [''])[0]

if 'corsano' not in st.session_state:
    secrets = st.secrets.get(st.session_state['patient_id'])
    st.session_state['corsano'] = loaders.corsano_load(secrets['email'], secrets['password'])

# initialize jsonbin
api_key = st.secrets['jsonbin']['api_key']
bin_id = st.secrets[st.session_state['patient_id']]['bin_id']
bin_api = jsonbin.BinAPI(api_key, bin_id)

if 'digipall' not in st.session_state:
    api_key = st.secrets['jsonbin']['api_key']
    bin_id = st.secrets[st.session_state['patient_id']]['bin_id']
    st.session_state['digipall'] = bin_api.read()

# ------------------ Display app header ------------------
st.set_page_config(page_title='DigiPALL',page_icon='icon.png')
st.title('DigiPall')

if st.session_state['corsano']['success']:
    st.success(f"Corsano: {st.session_state['corsano']['status']}")
else:
    st.error(f"Corsano: {st.session_state['corsano']['status']}")


# make several tabs
chat_tab, history_tab, vips_tab, decision_tree_tab = st.tabs(['Chat', 'Chat history', 'Vital signs', 'Decision tree'])

# ------------------ Get inputs from widgets  ------------------
delete_chat = history_tab.button('Delete chat history', key='delete')

# ------------------ Initiate chat ------------------
with chat_tab:

    dp = DigiPall(st, st.session_state.digipall, 'step_condition_feedback',
                  chat_start=st.session_state['corsano']['chat_opener'],
                  bot_msg_kwargs={'avatar_style': "fun-emoji", 'seed': "Rocky"},
                  user_msg_kwargs={'avatar_style': "personas", 'seed': "Felix"})

    col1, col2 = st.columns(2)

    if st.button('Reset chat', key='reset'):
        dp.reset()

    if delete_chat:
        dp.delete()

    dp.run()

    bin_api.update(dp.state)

# ------------------ Build tabs (other than chat) ------------------

with history_tab:

    chat_history = (pd.DataFrame(dp.state['chat'])[['timestamp', 'who', 'msg', 'step']]
                    .sort_index(ascending=False))
    st.dataframe(chat_history)


with vips_tab:
    # Get query parameters from the URL
    # id generator: https://catonmat.net/tools/generate-random-ascii
    if st.session_state['corsano']['success']:

        # get data
        activity_df = pd.DataFrame(st.session_state['corsano']['activity_data'])
        hr_df = pd.DataFrame(st.session_state['corsano']['heart_rate_data'])

        st.subheader('Steps')
        st.bar_chart(x='date', y='total_steps', data=activity_df, use_container_width=True)

        st.subheader('Heart Rate')
        cols = ['avg_daily_heart_rate','max_daily_heart_rate','rest_daily_heart_rate']
        st.line_chart(hr_df.set_index('date')[cols])


with decision_tree_tab:
    st.image('decisiontreestart.png', use_column_width=True)

