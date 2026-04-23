import streamlit as st

st.title("Login SIGAM (Prueba)")

email = st.text_input("Correo")
password = st.text_input("Contraseña", type="password")

if st.button("Login"):
    st.success(f"Intentando login con {email}")