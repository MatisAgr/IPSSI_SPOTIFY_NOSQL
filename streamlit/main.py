import streamlit as st
st.write("Hello")

st.sidebar.title("SPOTIFY DATASET")
# bouton de redirection vers upload_song.py
if st.sidebar.button("Upload a Song"):
    st.switch_page("pages/upload_song.py")
