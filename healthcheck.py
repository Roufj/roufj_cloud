
import streamlit as st
import time

st.set_page_config(page_title="Connection Test")

st.title("Streamlit Connection Test")
st.success("페이지가 정상적으로 로딩되었습니다.")
st.write("현재 서버 시간:", time.strftime("%Y-%m-%d %H:%M:%S"))
