import json
import os
import subprocess
import sys

import pandas as pd
import requests
import streamlit as st

pd.set_option('display.max_colwidth', -1)

# Start the Jina server
if not hasattr(st, 'already_started_server'):
    # Hack the fact that Python modules (like st) only load once to
    # keep track of whether this file already ran.
    st.already_started_server = True
    os.system('python app.py -t query_restful')

# Create name to code mapper dict
data = pd.read_csv('data/icd10.csv', sep="\[SEP\]", names=['code', 'name'])
code_mapper = {}
for index, row in data.iterrows():
    code_mapper[row['name']] = row['code']

st.title('ICD10 Entity Linker')
st.markdown('Find the nearest ICD10 code for condition')

top_k = st.sidebar.slider('Max no. of results', 1, 20, 10)

def call(method, url, payload=None, headers={'Content-Type': 'application/json'}):
    return getattr(getattr(requests, method)(url, data=json.dumps(payload), headers=headers), 'json')()

@st.cache(suppress_st_warning=True)
def get_results(query, top_k=3):
    output = call('post', 
                'http://0.0.0.0:45678/api/search', 
                payload={'top_k': top_k, 'mode': 'search',  'data': [f'text:{query}']}
                )
    matches = output['search']['docs'][0]['matches']
    return {code_mapper[match['text'].strip()]:match['text'] for match in matches}

query = st.text_input('Query', 'Enteropathic arthropathies, right hip')

result = get_results(query, top_k=top_k)

df = pd.DataFrame(list(result.items()), columns=['Code', 'Name'])
df.Name = df.Name.str.replace('\\n','')
df.index += 1
# df = df.to_html(escape=False)
st.markdown('**Relevant Codes**')
# st.write(df, unsafe_allow_html=True)
st.table(df)