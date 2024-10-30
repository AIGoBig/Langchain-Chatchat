from datetime import datetime
import uuid
from typing import List, Dict

import openai
import streamlit as st
import streamlit_antd_components as sac
from streamlit_chatbox import *
from streamlit_extras.bottom_container import bottom

from chatchat.settings import Settings
from chatchat.server.utils import get_config_models, get_config_platforms, get_default_llm, api_address
from chatchat.webui_pages.dialogue.dialogue import (save_session, restore_session, rerun,
                                                    get_messages_history, upload_temp_docs,
                                                    add_conv, del_conv, clear_conv)
from chatchat.webui_pages.utils import *
from chatchat.webui_pages.agent_app_batch_general import general_webui

from docx import Document

# chat_box = ChatBox(assistant_avatar=get_img_base64("chatchat_icon_blue_square_v2.png"))
chat_box = ChatBox(assistant_avatar=get_img_base64("chatchat_icon_blue_square_v2.png"),
                   user_avatar=get_img_base64("icon-chats.png"))

# chatchat 数据目录，必须通过环境变量设置。如未设置则自动使用当前目录。
CHATCHAT_ROOT = Path(os.environ.get("CHATCHAT_ROOT", ".")).resolve()
FILE_PATH_ROOT = str(CHATCHAT_ROOT / "data/app_files/uploads")
SAVE_PATH_ROOT = str(CHATCHAT_ROOT / "data/app_files/results")
if not os.path.exists(FILE_PATH_ROOT):
    os.makedirs(FILE_PATH_ROOT)
if not os.path.exists(SAVE_PATH_ROOT):
    os.makedirs(SAVE_PATH_ROOT)

def init_widgets():
    st.session_state.setdefault("history_len", Settings.model_settings.HISTORY_LEN)
    st.session_state.setdefault("search_engine", Settings.kb_settings.DEFAULT_SEARCH_ENGINE)
    st.session_state.setdefault("cur_conv_name", chat_box.cur_chat_name)
    st.session_state.setdefault("last_conv_name", chat_box.cur_chat_name)
    st.session_state.setdefault("file_chat_id", None)


def agent_app_batch(api: ApiRequest):
    ctx = chat_box.context
    ctx.setdefault("uid", uuid.uuid4().hex)
    ctx.setdefault("file_chat_id", None)
    ctx.setdefault("llm_model", get_default_llm())
    ctx.setdefault("temperature", Settings.model_settings.TEMPERATURE)
    init_widgets()

    # st.header("创建自动化批量生成任务")

    # AI_NAME = "易扣AI助手"
    # AI_WECHAT = "eCodeAI"
    # with st.chat_message(name="assistant", avatar=get_img_base64("chatchat_icon_blue_square_v2.png")):
    #     w_text = f"""👋Hello，我是{AI_NAME}，欢迎使用Agent自动化批量生成应用，选择任务并开始吧！ \n(问题反馈或帮助请添加`WeChat`: `{AI_WECHAT}`)"""
    #     st.write(w_text)
    #     # st.line_chart(np.random.randn(30, 3))

    # sac on_change callbacks not working since st>=1.34
    if st.session_state.cur_conv_name != st.session_state.last_conv_name:
        save_session(st.session_state.last_conv_name)
        restore_session(st.session_state.cur_conv_name)
        st.session_state.last_conv_name = st.session_state.cur_conv_name

    # st.write(chat_box.cur_chat_name)
    # st.write(st.session_state)

    @st.experimental_dialog("模型配置", width="large")
    def llm_model_setting():
        # 模型
        cols = st.columns(3)
        platforms = ["所有"] + list(get_config_platforms())
        platform = cols[0].selectbox("选择模型平台", platforms, key="platform")
        llm_models = list(
            get_config_models(
                model_type="llm", platform_name=None if platform == "所有" else platform
            )
        )
        llm_models += list(
            get_config_models(
                model_type="image2text", platform_name=None if platform == "所有" else platform
            )
        )
        llm_model = cols[1].selectbox("选择LLM模型", llm_models, key="llm_model")
        temperature = cols[2].slider("Temperature", 0.0, 1.0, key="temperature")
        system_message = st.text_area("System Message:", key="system_message")
        if st.button("OK"):
            rerun()


    # 配置参数
    with st.sidebar:
        tabs = st.tabs(["APP 选择", "会话设置"])
        with tabs[0]:
            dialogue_modes = ["文件翻译生成"]
            dialogue_mode = st.selectbox("请选择APP：",
                                         dialogue_modes,
                                         key="dialogue_mode",
                                         )
            st.divider()
            placeholder = st.empty()
            st.divider()

            api_key = st.text_input("自定义易扣AI Key：([获取地址](http://api.ecodeai.com/token))", value="",
                                    type="password")
            llm_model = ctx.get("llm_model")


    general_webui(dialogue_mode, llm_model, api_key, FILE_PATH_ROOT, SAVE_PATH_ROOT)