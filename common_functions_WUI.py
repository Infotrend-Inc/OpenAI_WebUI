import os

import common_functions as cf

import streamlit as st


def get_runid():
    if 'webui_runid' not in st.session_state:
        st.session_state['webui_runid'] = cf.get_timeUTC()

    runid = st.session_state['webui_runid']
    return runid

#####

def show_history(hist, allow_history_deletion, last_prompt_key, last_query_key):
    hk = [x for x in hist.keys() if cf.isNotBlank(x)]
    hk = sorted(hk, reverse=True)
    hk_opt = [hist[x][0] for x in hk]
    hk_q = {hist[x][0]: hist[x][1] for x in hk}
    prev = st.selectbox("Prompt History (most recent first)", options=hk_opt, index=0, key="history")
    if st.button("Load Selected Prompt", key="load_history"):
        st.session_state[last_prompt_key] = prev
        st.session_state[last_query_key] = hk_q[prev]
    if allow_history_deletion:
        if st.button("Delete Selected Prompt", key="delete_history"):
            if cf.isNotBlank(prev):
                dir = os.path.dirname(hk_q[prev])
                err = cf.directory_rmtree(dir)
                if cf.isNotBlank(err):
                    st.error(f"While deleting {dir}: {err}")
                else:
                    if os.path.exists(dir):
                        st.error(f"Directory {dir} still exists")
                    else:
                        st.success(f"Deleted")
            else:
                st.error("Please select a prompt to delete")