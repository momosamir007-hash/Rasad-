import streamlit as st
def css(): st.markdown('''<style>
.block-container{direction:rtl;padding-top:1.3rem;max-width:1450px}.stApp{background:#f6f8fc}h1,h2,h3,p,label{text-align:right}.hero{padding:1.5rem 1.8rem;border-radius:22px;background:linear-gradient(135deg,#111827,#1d4ed8);color:white;margin-bottom:1rem}.card{background:white;border-radius:18px;padding:1rem;box-shadow:0 4px 18px rgba(0,0,0,.06);border:1px solid #eef2f7}.stButton>button{border-radius:12px;font-weight:700;min-height:42px}.success-box{padding:1rem;border-radius:16px;background:#ecfdf5;border:1px solid #a7f3d0}.stMetric{background:white;padding:.7rem;border-radius:16px;border:1px solid #eef2f7}
</style>''',unsafe_allow_html=True)
def hero(title,subtitle):st.markdown(f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>',unsafe_allow_html=True)
