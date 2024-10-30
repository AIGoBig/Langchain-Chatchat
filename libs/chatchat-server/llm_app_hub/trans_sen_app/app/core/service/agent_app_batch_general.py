import uuid
import streamlit as st
import os
from docx import Document
from llm_app_hub.trans_sen_app.app.core.service.main import main_schedule as trans_sen_app_main


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

def general_webui(dialogue_mode, llm_model, api_key, FILE_PATH_ROOT, SAVE_PATH_ROOT):
    ### begin
    st.header(dialogue_mode)
    placeholder = st.empty()
    st.divider()

    with placeholder.container():
        pass
        if dialogue_mode == "文件翻译生成":
            st.text("在几分钟内将文档翻译成需要的语言。")
            st.divider()

            language_modes = ["中文", "English"]
            st.subheader("生成配置")
            language_mode = st.selectbox("## 目标语言", language_modes, key="language_mode")

            output_name = st.text_input("## 目标文件名", "result.docx")

    st.subheader("上传文件")
    files = st.file_uploader("选择目标文件后, 点击开始文件上传, 并进行文件预览",
                             # [i for ls in LOADER_DICT.values() for i in ls],
                             ["docx", "doc", "txt", "epub", "pdf"],
                             accept_multiple_files=True,
                             )

    # upload_func = st.columns(2)
    # cols_func = st.columns(2)
    if st.button("开始上传", disabled=len(files) == 0):
        # st.session_state["file_chat_id"] = upload_temp_docs(files, api)
        if len(files) > 1:
            st.error("目前仅支持单文件")
            st.stop()

        st.session_state.uploaded_file = files[-1]  # TODO : fix me

        file_id = uuid.uuid4().hex
        file_name = file_id + "-" + st.session_state.uploaded_file.name
        st.session_state.file_path = os.path.join(FILE_PATH_ROOT, file_name)
        st.session_state.path_save = os.path.join(SAVE_PATH_ROOT, file_name + ".docx")

        with open(st.session_state.file_path, "wb") as f:
            f.write(st.session_state.uploaded_file.getbuffer())

        # 显示文件内容预览
        txt_content = ""
        if st.session_state.file_path.endswith(".txt"):
            with open(st.session_state.file_path, "r", encoding="utf-8") as f:
                txt_content = f.read().decode("utf-8")
        elif st.session_state.file_path.endswith(".docx") or st.session_state.file_path.endswith(".doc"):
            doc = Document(st.session_state.file_path)
            for para in doc.paragraphs:
                txt_content += para.text + "\n"
        elif st.session_state.file_path.endswith(".pdf"):
            txt_content = pdf2txt(st.session_state.file_path)
        elif st.session_state.file_path.endswith(".epub"):
            from epub2txt import epub2txt
            txt_content = epub2txt(st.session_state.file_path)

        with open(st.session_state.file_path + ".txt", "w", encoding="utf-8") as f:
            f.write(txt_content)

        with st.expander("点击查看上传内容预览", expanded=False):
            st.write(txt_content)

            # 使用一个状态变量来跟踪是否在运行处理
            if 'is_processing' not in st.session_state:
                st.session_state.is_processing = False

    st.divider()
    st.subheader("提交运行")
    st.text("上传目标文件后, 点击开始运行, 提交批量生成任务")
    # 显示开始运行按钮，并在处理时禁用
    if st.button('开始运行', disabled=('is_processing' not in st.session_state or st.session_state.is_processing)):
        if api_key and not api_key.startswith("sk-"):
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

                    ans_all = trans_sen_app_main([text], st.session_state.path_save, llm_model,
                                                 api_key, language_mode)  # 假设该函数返回生成的文件路径
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
    if output_name:
        file_name_tmp = output_name
    elif "uploaded_file" in st.session_state:
        file_name_tmp = st.session_state.uploaded_file.name + ".docx"

    st.subheader("预览下载")
    st.text("完成批量生成后, 预览生成结果, 并点击下载结果")
    st.download_button(
        label="下载结果",
        data=data,
        file_name=file_name_tmp,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        disabled=(data == "" or "uploaded_file" not in st.session_state)
    )
    ### end