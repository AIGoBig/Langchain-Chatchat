import sys

import streamlit as st
import streamlit_antd_components as sac

from chatchat import __version__
from chatchat.server.utils import api_address
from chatchat.webui_pages.dialogue.dialogue import  dialogue_page
from chatchat.webui_pages.kb_chat import kb_chat
from chatchat.webui_pages.knowledge_base.knowledge_base import knowledge_base_page
from chatchat.webui_pages.utils import *

from chatchat.webui_pages.agent_app_chat import agent_app_chat

# 用户名和密码的默认值
DEFAULT_USER = {
    "admin": "adminadmin",
    "custom_921": "custom_921"
    }
api = ApiRequest(base_url=api_address())

no_logged_in_flag = True  # 免登录

if no_logged_in_flag:
    st.session_state.logged_in = True

# 检查会话状态中是否有登录状态，如果没有，初始化为 False
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False


def login_page():
    with st.form("login_form"):
        st.title("易扣AI大模型应用平台")
        username = st.text_input("用户名", value="")
        password = st.text_input("密码", value="", type="password")
        submit = st.form_submit_button("登录")

        if submit:
            if username in DEFAULT_USER.keys() and password == DEFAULT_USER[username]:
                st.success(f"登录成功,欢迎你 {username}！")
                # 更新会话状态为已登录
                st.session_state.logged_in = True
                st.experimental_rerun()  # 重新运行脚本以显示主页面
            else:
                st.error("用户名或密码错误，请重新输入。")


if __name__ == "__main__":
    is_lite = "lite" in sys.argv  # TODO: remove lite mode

    st.set_page_config(
        "Chat.eCodeAI",
        get_img_base64("chatchat_icon_blue_square_v2.png"),
        initial_sidebar_state="expanded",
        menu_items={
            # "Get Help": "https://github.com/chatchat-space/Langchain-Chatchat",
            # "Report a bug": "https://github.com/chatchat-space/Langchain-Chatchat/issues",
            # "About": f"""欢迎使用 Langchain-Chatchat WebUI {__version__}！""",
            "Get Help": "http://www.ecode.cc",
            # "Get Help": "wechat: eCodeAI",
            "About": f"""欢迎使用 chat.eCodeAI.com, WeChat: eCodeAI""",
        },
        layout="centered",
    )

    if not st.session_state.logged_in:
        # 如果用户未登录，则显示登录页面
        login_page()
    else:
        # use the following code to set the app to wide mode and the html markdown to increase the sidebar width
        st.markdown(
            """
            <style>
            [data-testid="stSidebarUserContent"] {
                padding-top: 20px;
            }
            .block-container {
                padding-top: 25px;
            }
            [data-testid="stBottomBlockContainer"] {
                padding-bottom: 20px;
            }
            """,
            unsafe_allow_html=True,
        )

        with st.sidebar:
            st.image(
                get_img_base64("logo-ecodeai-min.png"), use_column_width=True
            )
            st.caption(
                f"""<p align="right">专注于企业级大模型算法落地</p>""",
                unsafe_allow_html=True,
            )

            selected_page = sac.menu(
                [
                    sac.MenuItem("APP Agent 应用", icon="app"),
                    sac.MenuItem("Tool Agent 对话", icon="chat"),
                    sac.MenuItem("RAG LLM 问答", icon="database"),
                    sac.MenuItem("知识库管理", icon="hdd-stack"),
                ],
                key="selected_page",
                open_index=0,
            )

            sac.divider()

        if selected_page == "知识库管理":
            knowledge_base_page(api=api, is_lite=is_lite)
        elif selected_page == "RAG LLM 问答":
            kb_chat(api=api)
        elif selected_page == "APP Agent 应用":
            agent_app_chat(api=api)
        else:
            dialogue_page(api=api, is_lite=is_lite)
