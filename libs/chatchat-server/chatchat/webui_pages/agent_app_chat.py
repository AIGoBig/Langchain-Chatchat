from datetime import datetime
import uuid
from typing import List, Dict

import openai
import streamlit as st
import streamlit_antd_components as sac
from streamlit_chatbox import *
from streamlit_extras.bottom_container import bottom

from chatchat.settings import Settings
from chatchat.server.knowledge_base.utils import LOADER_DICT
from chatchat.server.utils import get_config_models, get_config_platforms, get_default_llm, api_address
from chatchat.webui_pages.dialogue.dialogue import (save_session, restore_session, rerun,
                                                    get_messages_history, upload_temp_docs,
                                                    add_conv, del_conv, clear_conv)
from chatchat.webui_pages.utils import *

from docx import Document
from llm_app_hub.trans_sen_app.app.core.service.main import main_schedule as trans_sen_app_main


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
    st.session_state.setdefault("selected_kb", Settings.kb_settings.DEFAULT_KNOWLEDGE_BASE)
    st.session_state.setdefault("kb_top_k", Settings.kb_settings.VECTOR_SEARCH_TOP_K)
    st.session_state.setdefault("se_top_k", Settings.kb_settings.SEARCH_ENGINE_TOP_K)
    st.session_state.setdefault("score_threshold", Settings.kb_settings.SCORE_THRESHOLD)
    st.session_state.setdefault("search_engine", Settings.kb_settings.DEFAULT_SEARCH_ENGINE)
    st.session_state.setdefault("return_direct", False)
    st.session_state.setdefault("cur_conv_name", chat_box.cur_chat_name)
    st.session_state.setdefault("last_conv_name", chat_box.cur_chat_name)
    st.session_state.setdefault("file_chat_id", None)


def pdf2txt(file_name):
    import pdfplumber
    p = pdfplumber.open(file_name + ".pdf")
    ans_text = ""
    page_num = len(p.pages)
    with pdfplumber.open(file_name + ".pdf") as pdf:
        for i in range(page_num):
            page = pdf.pages[i]
            text = page.extract_text()
            if text != None:
                ans_text += text + "\n"
    return ans_text


def agent_app_chat(api: ApiRequest):
    ctx = chat_box.context
    ctx.setdefault("uid", uuid.uuid4().hex)
    ctx.setdefault("file_chat_id", None)
    ctx.setdefault("llm_model", get_default_llm())
    ctx.setdefault("temperature", Settings.model_settings.TEMPERATURE)
    init_widgets()

    AI_NAME = "易扣AI助手"
    AI_WECHAT = "eCodeAI"
    with st.chat_message(name="assistant", avatar=get_img_base64("chatchat_icon_blue_square_v2.png")):
        w_text = f"""👋Hello，我是{AI_NAME}，请在对话框中告诉我您的需求或问题，我们开始吧！ \n(问题反馈或帮助请添加`WeChat`: `{AI_WECHAT}`)"""
        st.write(w_text)
        # TODO 在此加入能力图。
        # st.line_chart(np.random.randn(30, 3))

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

    @st.experimental_dialog("重命名会话")
    def rename_conversation():
        name = st.text_input("会话名称")
        if st.button("OK"):
            chat_box.change_chat_name(name)
            restore_session()
            st.session_state["cur_conv_name"] = name
            rerun()

    # 配置参数
    with st.sidebar:
        tabs = st.tabs(["APP 选择", "会话设置"])
        with tabs[0]:
            dialogue_modes = ["文件翻译生成",
                              ]
            dialogue_mode = st.selectbox("请选择APP：",
                                         dialogue_modes,
                                         key="dialogue_mode",
                                         )
            st.divider()
            placeholder = st.empty()
            st.divider()
            # prompt_templates_kb_list = list(Settings.prompt_settings.rag)
            # prompt_name = st.selectbox(
            #     "请选择Prompt模板：",
            #     prompt_templates_kb_list,
            #     key="prompt_name",
            # )
            prompt_name="default"
            history_len = st.number_input("历史对话轮数：", 0, 20, key="history_len")
            # kb_top_k = st.number_input("匹配知识条数：", 1, 20, key="kb_top_k")
            # ## Bge 模型会超过1
            # score_threshold = st.slider("知识匹配分数阈值：", 0.0, 2.0, step=0.01, key="score_threshold")
            # return_direct = st.checkbox("仅返回检索结果", key="return_direct")
            kb_top_k = 3
            ## Bge 模型会超过1
            score_threshold = 2
            return_direct = False

            with placeholder.container():
                # if dialogue_mode == "文件翻译生成":

                # files = st.file_uploader("上传知识文件：",
                #                         [i for ls in LOADER_DICT.values() for i in ls],
                #                         accept_multiple_files=True,
                #                         )

                # st.text("知识库设置：")
                # st.warning("自动化批量生成")
                st.subheader("自动化批量生成")

                api_key = st.text_input("填入易扣AI Key：([获取地址](http://api.ecodeai.com/token))", value="",
                                              type="password")
                llm_model = ctx.get("llm_model")

                # model_name = st.text_input("易扣AI Key：([模型列表](http://api.ecodeai.com/pricing))")

                files = st.file_uploader("上传文件自动化生成：",
                                        # [i for ls in LOADER_DICT.values() for i in ls],
                                        ["docx", "doc", "txt", "epub", "pdf"],
                                        accept_multiple_files=True,
                                        )
                if st.button("开始上传", disabled=len(files) == 0):
                    # st.session_state["file_chat_id"] = upload_temp_docs(files, api)
                    if len(files) > 1:
                        st.error("目前仅支持单文件")
                        st.stop()

                    st.session_state.uploaded_file = files[-1] # TODO : fix me

                    file_id = uuid.uuid4().hex
                    file_name = file_id+"-"+st.session_state.uploaded_file.name
                    st.session_state.file_path = os.path.join(FILE_PATH_ROOT, file_name)
                    st.session_state.path_save = os.path.join(SAVE_PATH_ROOT, file_name+".docx")

                    with open(st.session_state.file_path, "wb") as f:
                        f.write(st.session_state.uploaded_file.getbuffer())

                    # 显示文件内容预览
                    txt_content = ""
                    if st.session_state.file_path.endswith(".txt"):
                        pass
                    elif st.session_state.file_path.endswith(".docx") or st.session_state.file_path.endswith(".doc"):
                        doc = Document(st.session_state.file_path)
                        for para in doc.paragraphs:
                            txt_content += para.text + "\n"
                    elif st.session_state.file_path.endswith(".pdf"):
                        txt_content = pdf2txt(file_name)
                    elif st.session_state.file_path.endswith(".epub"):
                        from epub2txt import epub2txt
                        txt_content = epub2txt(st.session_state.file_path)

                    with open(st.session_state.file_path + ".txt", "w", encoding = "utf-8") as f:
                        f.write(txt_content)

                    with st.expander("点击查看上传内容预览", expanded=False):
                        st.write(txt_content)

                        # 使用一个状态变量来跟踪是否在运行处理
                        if 'is_processing' not in st.session_state:
                            st.session_state.is_processing = False

                # 显示开始运行按钮，并在处理时禁用
                run_button_disabled = 'is_processing' not in st.session_state or st.session_state.is_processing
                if st.button('开始运行', disabled=run_button_disabled):
                    if not api_key or not api_key.startswith("sk-"):
                        st.error("请输入正确的 易扣AI Key")
                        st.stop()

                    # 设置处理状态为 True，禁用按钮
                    st.session_state.is_processing = True

                    # 显示处理中的状态
                    with st.spinner("处理文件中，请稍候..."):
                        # 运行主处理逻辑
                        # doc = Document(st.session_state.file_path)
                        with open(st.session_state.file_path + ".txt", "r") as f:  # 打开文件
                            txt_content = f.read()  # 读取文件

                        with st.expander("点击查看生成结果内容", expanded=False):
                            for text in txt_content.split('\n'):
                                # data_l.append(paragraph.text)
                                if text.strip() == "":
                                    continue
                                # if not sum([1 if u'\u4e00' <= i <= u'\u9fff' else 0 for i in text.strip()])>0:
                                #     continue

                                ans_all = trans_sen_app_main([text], st.session_state.path_save, llm_model, api_key)  # 假设该函数返回生成的文件路径
                                st.session_state.output_path = st.session_state.path_save

                                # # 检查生成的文件是否存在
                                # if os.path.exists(st.session_state.output_path):
                                #     # 显示生成结果的预览
                                #     generated_doc = Document(st.session_state.output_path)

                                st.write(ans_all + "\n")
                                # 处理完成后重置状态
                            st.session_state.is_processing = False
                            # else:
                            #     st.error("生成结果文件不存在，请检查运行步骤。")
                            #     st.session_state.is_processing = False
                    st.success("完成生成")

                # 始终显示下载生成结果按钮
                data = ""
                if 'output_path' in st.session_state and st.session_state.output_path:
                    output_path = st.session_state.output_path
                    if os.path.exists(output_path):
                        with open(output_path, "rb") as f:
                            data = f.read()
                    else:
                        st.warning("文件还在处理或未生成。")
                # else:
                #     st.warning("请请上传文件后进行自动化生成。")
                if "uploaded_file" in st.session_state:
                    st.download_button(
                        label="下载结果",
                        data=data,
                        file_name=st.session_state.uploaded_file.name+".docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        disabled=(data == "")
                    )
        with tabs[1]:
            # 会话
            cols = st.columns(3)
            conv_names = chat_box.get_chat_names()

            def on_conv_change():
                print(conversation_name, st.session_state.cur_conv_name)
                save_session(conversation_name)
                restore_session(st.session_state.cur_conv_name)

            conversation_name = sac.buttons(
                conv_names,
                label="当前会话：",
                key="cur_conv_name",
                on_change=on_conv_change,
            )
            chat_box.use_chat_name(conversation_name)
            conversation_id = chat_box.context["uid"]
            if cols[0].button("新建", on_click=add_conv):
                ...
            if cols[1].button("重命名"):
                rename_conversation()
            if cols[2].button("删除", on_click=del_conv):
                ...

    # Display chat messages from history on app rerun
    chat_box.output_messages()
    chat_input_placeholder = "请输入对话内容，换行请使用Shift+Enter。"

    llm_model = ctx.get("llm_model")

    # chat input
    with bottom():
        cols = st.columns([1, 0.2, 15,  1])
        if cols[0].button(":gear:", help="模型配置"):
            widget_keys = ["platform", "llm_model", "temperature", "system_message"]
            chat_box.context_to_session(include=widget_keys)
            llm_model_setting()
        if cols[-1].button(":wastebasket:", help="清空对话"):
            chat_box.reset_history()
            rerun()
        # with cols[1]:
        #     mic_audio = audio_recorder("", icon_size="2x", key="mic_audio")
        prompt = cols[2].chat_input(chat_input_placeholder, key="prompt")
    if prompt:
        history = get_messages_history(ctx.get("history_len", 3))
        messages = history + [{"role": "user", "content": prompt}]
        chat_box.user_say(prompt)

        extra_body = dict(
            top_k=kb_top_k,
            score_threshold=score_threshold,
            temperature=ctx.get("temperature"),
            prompt_name=prompt_name,
            return_direct=return_direct,
        )

        if dialogue_mode == "文件翻译生成":
            # client = openai.Client(base_url=f"{api_url}/knowledge_base/temp_kb/{knowledge_id}", api_key="NONE")
            client = openai.Client(base_url=f"{api_address()}/chat", api_key="NONE")
            # chat_box.ai_say([
            #     Markdown("...", in_expander=True, title="正在文件轮询", state="running", expanded=return_direct),
            #     f"正在文件轮询 ...",
            # ])
            chat_box.ai_say(f"{AI_NAME}正在思考...")

            if "uploaded_file" not in st.session_state or st.session_state.uploaded_file is None:
                # st.error("请先上传文件")
                st.warning("请上传文件使用自动化生成功能")
                # st.stop()

        text = ""
        # first = True

        try:
            for d in client.chat.completions.create(messages=messages, model=llm_model, stream=True, extra_body=extra_body):
                # if first:
                #     chat_box.update_msg("\n\n".join(d.docs), element_index=0, streaming=False, state="complete")
                #     chat_box.update_msg("", streaming=False)
                #     first = False
                #     continue
                text += d.choices[0].delta.content or ""
                chat_box.update_msg(text.replace("\n", "\n\n"), streaming=True)
            chat_box.update_msg(text, streaming=False)
            # TODO: 搜索未配置API KEY时产生报错
        except Exception as e:
            st.error(e)

    now = datetime.now()
    with tabs[1]:
        cols = st.columns(2)
        export_btn = cols[0]
        if cols[1].button(
            "清空对话",
            use_container_width=True,
        ):
            chat_box.reset_history()
            rerun()

    export_btn.download_button(
        "导出记录",
        "".join(chat_box.export2md()),
        file_name=f"{now:%Y-%m-%d %H.%M}_对话记录.md",
        mime="text/markdown",
        use_container_width=True,
    )

    # st.write(chat_box.history)
