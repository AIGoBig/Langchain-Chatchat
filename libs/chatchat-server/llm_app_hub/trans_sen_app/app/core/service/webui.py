import copy
import os
from pathlib import Path
from agent_app_batch_general import general_webui
import streamlit as st
from app.common.config.app_config import read_json_as_dict, update_model_config
from datetime import datetime
import json
import streamlit_antd_components as sac
import importlib


# 用户名和密码的默认值
DEFAULT_USER = {
    "admin": "adminadmin",
    "custom82002": "custom82002"
    }

no_logged_in_flag = False  # 免登录

if no_logged_in_flag:
    st.session_state.logged_in = True

# 检查会话状态中是否有登录状态，如果没有，初始化为 False
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False


def login_page():
    with st.form("login_form"):
        st.title("AI大模型应用平台")
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


def trans_sen_page():
    # chatchat 数据目录，必须通过环境变量设置。如未设置则自动使用当前目录。
    CHATCHAT_ROOT = Path(os.environ.get("CHATCHAT_ROOT", ".")).resolve()
    FILE_PATH_ROOT = str(CHATCHAT_ROOT / "data/app_files/uploads")
    SAVE_PATH_ROOT = str(CHATCHAT_ROOT / "data/app_files/results")
    if not os.path.exists(FILE_PATH_ROOT):
        os.makedirs(FILE_PATH_ROOT)
    if not os.path.exists(SAVE_PATH_ROOT):
        os.makedirs(SAVE_PATH_ROOT)

    with st.sidebar:
        st.title(
            f"""文件翻译生成""",
        )

        selected_page = sac.menu(
            [
                sac.MenuItem("文件翻译生成", icon="app"),
                sac.MenuItem("配置更新发布", icon="database"),
            ],
            key="selected_page",
            open_index=0,
        )

        sac.divider()

    if selected_page == "文件翻译生成":
        general_webui(selected_page, None, None, FILE_PATH_ROOT, SAVE_PATH_ROOT)
    elif selected_page == "配置更新发布":
        if not st.session_state.logged_in:
            # 如果用户未登录，则显示登录页面
            login_page()
        else:
            model_config = read_json_as_dict()  # TODO check
            model_config_update = st.text_area("应用配置: ", json.dumps(model_config, indent=4, ensure_ascii=False), height=600)
            st.markdown("""
            ### 配置说明：
            
- _comment: 对参数的说明或注意事项。提示用户可以在指定网站更新或获取新的 api_key。
- api_key: 用于访问 API 的密钥，需要从 http://api.ecodeai.com 进行获取或更新。
- model_name: 使用的模型名称。例如，模型名称为 qwen-max。
- data_files_path: 输入数据文件的路径。例如，路径是 data/input/word/。
- data_files_out: 输出数据文件的路径。例如，路径是 data/output/word/。
- sen_list: 一个包含若干字符串的列表，用于指定敏感词或特殊处理的词语。
- prompt: 提示模板配置。配置中的{{query}}用于填入待翻译问题输入, 配置中的{{language}}用于填入待翻译目标语言 (当指令中不存在language配置时, 则默认为通过大模型判断目标翻译语言)。

这些配置项用于控制翻译系统的行为，包括如何访问 API、数据路径、使用的模型、敏感词列表以及翻译提示模板等。        
            """)
            if st.button("修改配置"):
                # try:
                #     # model_config.update(json.loads(model_config_update))
                #     if model_config_update != model_config:
                #         print("model_config_update:", model_config_update)
                #         st.success("修改成功")
                #
                #
                #
                #     # with open(""):
                #     #     json.dumps(model_config_update)
                # except:
                #     st.warning("修改失败")

                # 检查是否输入了有效的JSON字符串
                if model_config_update:
                    json_data = json.loads(model_config_update)
                    try:
                        if json_data != model_config:
                            # 尝试解析JSON字符串
                            # from app.common.config.app_config import model_config  # TODO check
                            update_model_config("model_config_bak_{}.json".format(datetime.now().strftime("%Y%m%d_%H%M%S")), model_config) # bak
                            update_model_config("model_config.json", json_data)
                            model_config = json_data
                            # importlib.reload(model_config)
                            st.success("修改成功")
                            st.write('更新后的配置为:', model_config)
                            # st.json(json_data)
                        else:
                            st.warning('没有进行任何修改')
                    except json.JSONDecodeError:
                        st.error('输入的不是有效的JSON格式')
                else:
                    st.write('请输入JSON数据')

if __name__ == "__main__":
    trans_sen_page()