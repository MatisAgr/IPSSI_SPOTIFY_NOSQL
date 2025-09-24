import streamlit as st

st.title("Upload a Song")
st.text_input('Artiste')
st.text_input('Nom de l\'album')
st.number_input('Popularité')
st.number_input('Durée (ms)')
st.selectbox('Explicite', ['Oui', 'Non'])
st.slider('Danceabilité', 0, 1000, 500, step=1, format="%d") / 1000
st.slider('Energie', 0, 1000, 500, step=1, format="%d") / 1000
st.number_input('Clé')
st.slider('Intensité', -60.0, 0.0, -30.0, step=0.1, format="%.1f")
st.selectbox('Mode', [0, 1])
st.slider('Parole', 0, 1000, 500, step=1, format="%d") / 1000
st.slider('Acoustique', 0, 1000, 500, step=1, format="%d") / 1000
st.slider('Instrumental', 0, 1000, 500, step=1, format="%d") / 1000
st.slider('Vivacité', 0, 1000, 500, step=1, format="%d") / 1000
st.slider('Valence', 0, 1000, 500, step=1, format="%d") / 1000
st.number_input('Tempo')
st.number_input('Time Signature')
st.text_input('Genre de la piste')
# bouton de soumission
if st.button('Uploader'):
    st.success('Son uploadé avec succès!')
else:
    st.error('Erreur lors de l\'upload du son.')