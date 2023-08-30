import streamlit as st
import pandas as pd
from tools import corsano, loaders, jsonbin
from tools.digipall import DigiPall

st.set_page_config(page_title='DigiPALL',page_icon='icon.png')
st.title('DigiPALL')

# ------------------ check for id, secrets and donwload data ------------------
patient_id = st.experimental_get_query_params().get('id', [''])[0]
if 'id' in st.experimental_get_query_params():
    patient_id = st.experimental_get_query_params()['id'][0]
else:
    st.error('No patient id provided')
    st.stop()

if patient_id in st.secrets:
    patient_secrets = st.secrets[patient_id]
else:
    st.error('Patient id not known')
    st.stop()

for key in ['email', 'password', 'bin_id']:
    if key not in patient_secrets:
        st.error(f'Missing patient secrets')
        st.stop()

if 'jsonbin' not in st.secrets:
    st.error(f'Missing jsonbin secrets')
    st.stop()
elif 'api_key' not in st.secrets['jsonbin']:
    st.error(f'Missing jsonbin api key')
    st.stop()
else:
    jsonbin_api_key = st.secrets['jsonbin']['api_key']

# initialize jsonbin
bin_api = jsonbin.BinAPI(jsonbin_api_key, patient_secrets['bin_id'])

# initialize digipall on first start of the app
if 'digipall' not in st.session_state:
    st.session_state['digipall'] = bin_api.read()

# donwlodad data from corsano on first start of the app
if 'corsano' not in st.session_state:
    st.session_state['corsano'] = loaders.corsano_load(patient_secrets['email'], patient_secrets['password'])

# show status of corsano data
if st.session_state['corsano']['success']:
    st.success(f"Corsano: {st.session_state['corsano']['status']}")
else:
    st.error(f"Corsano: {st.session_state['corsano']['status']}")

# ------------------ Initiate tabs ------------------

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
        cols = ['avg_daily_heart_rate', 'max_daily_heart_rate','rest_daily_heart_rate']
        st.line_chart(hr_df.set_index('date')[cols])


with decision_tree_tab:
    st.image('decisiontreestart.png', use_column_width=True)

