import datetime
import time
import os
import json

import tqdm
from pathlib import Path
import re
# pip install python-docx
from docx import Document
import sys

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
root_path = str(Path(__file__).parent.parent.parent.parent)

from app.common.config.app_config import read_json_as_dict
from app.common.utils.langfunc import langen

# 将生成的问答对写入.txt文件
def write_to_file(content):
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = os.path.join(root_path, f"data/output/new_file_{timestamp}.txt")
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(content)
    print("File 'new_file.txt' has been created and written.")

#
# def cut_sen(text):
#     def normal_cut_sentence(text):
#         text = re.sub('([。！？\?])([^’”])', r'\1\n\2', text)  # 普通断句符号且后面没有引号
#         text = re.sub('(\.{6})([^’”])', r'\1\n\2', text)  # 英文省略号且后面没有引号
#         text = re.sub('(\…{2})([^’”])', r'\1\n\2', text)  # 中文省略号且后面没有引号
#         text = re.sub('([.。！？\?\.{6}\…{2}][’”])([^’”])', r'\1\n\2', text)  # 断句号+引号且后面没有引号
#         return text.split("\n")
#
#     def cut_sentence_with_quotation_marks(text):
#         p = re.compile("“.*?”")
#         list = []
#         index = 0
#         length = len(text)
#         for i in p.finditer(text):
#             temp = ''
#             start = i.start()
#             end = i.end()
#             for j in range(index, start):
#                 temp += text[j]
#             if temp != '':
#                 temp_list = normal_cut_sentence(temp)
#                 list += temp_list
#             temp = ''
#             for k in range(start, end):
#                 temp += text[k]
#             if temp != ' ':
#                 list.append(temp)
#             index = end
#         return list
#
#     return cut_sentence_with_quotation_marks(text)


def split_sentences(line):
    sentences = re.split(r'([。！；？，])', line.strip())
    line_split = ["".join(i) for i in zip(sentences[0::2], sentences[1::2])]
    line_split = [line.strip() for line in line_split if
                  line.strip() not in ['。', '！', '？', '；', '，'] and len(line.strip()) > 1]
    return line_split

def trans_func(sen_list, language):
    model_config = read_json_as_dict()
    ans_func = ""
    # for ind, e in tqdm.tqdm(enumerate(sen_list)):
    for e in sen_list:
        if not e:
            continue
        for i in range(5):
            regen = False
            try:
                user_prompt = model_config["prompt"].replace("{{query}}", e).replace("{{language}}", language)
                ans = langen(model_config=model_config, user_prompt=user_prompt)
                for se in model_config["sen_list"]:
                    if se in ans:
                        regen = True
                        break

            except Exception as error:
                # print("error: ", error)
                ans = " <|sen|> "
                regen = True
            if not regen:
                break
        if regen:
            ans = " <|sen|> "
        ans_func += ans + " "
        print(ans, end='')
    return ans_func


def main():
    model_config = read_json_as_dict()
    files_tmp = os.listdir(os.path.join(root_path, model_config["data_files_path"]))
    docx_files = [file for file in files_tmp if (file.endswith(".docx") and not file.startswith("~$"))]
    print("开始...")
    print(docx_files)

    for file in docx_files:
        path = os.path.join(root_path, model_config["data_files_path"], file)
        path_save = os.path.join(root_path, model_config["data_files_out"], file)
        if os.path.exists(path_save):
            continue
        print("path_save", path_save)
        doc = Document(path)
        data_l = []

        for paragraph in doc.paragraphs:
            data_l.append(paragraph.text)
            # print(data_l)

        ans_all = ""
        # data_l = data.split('\n')
        for ind, data in tqdm.tqdm(enumerate(data_l)):
            if not data:
                continue
            ans_func = trans_func([data], language)
            if ans_func == " <|sen|> ":
                print("(regen)")
                sen_list = split_sentences(data)
                if not sen_list:
                    continue
                ans_func = trans_func(sen_list)
            ans_func.replace("\\", '')
            ans_all += ans_func + "\n" + data + "\n\n"
            print("\n", data, "\n\n")
        ans_all = re.sub(r'\\', '', ans_all)
        document = Document()
        document.add_paragraph(ans_all)
        document.save(path_save, encodings="utf-8")

# def main_pipeline(path, path_save, model_name=None, api_key=None):
#
#     print("path_save", path_save)
#     doc = Document(path)
#     data_l = []
#
#     for paragraph in doc.paragraphs:
#         data_l.append(paragraph.text)
#
#     return main_schedule(data_l, path_save)

def main_schedule(data_l, path_save, model_name=None, api_key=None, language="English"):
    model_config = read_json_as_dict()
    print("model_config: ", model_config)
    model_config["api_key"] = api_key if api_key else model_config["api_key"]
    model_config["model_name"] = model_name if model_name else model_config["model_name"]

    ans_all = ""
    # data_l = data.split('\n')
    # for ind, data in tqdm.tqdm(enumerate(data_l)):
    for ind, data in tqdm.tqdm(enumerate(data_l)):
        if not data:
            continue
        ans_func = trans_func([data], language)
        if ans_func == " <|sen|> ":
            print("(regen)")
            sen_list = split_sentences(data)
            if not sen_list:
                continue
            ans_func = trans_func(sen_list, language)
        ans_func.replace("\\", '')
        ans_all += ans_func + "\n\n" + data + "\n\n"
        print("\n", data, "\n\n")
    ans_all = re.sub(r'\\', '', ans_all)
    if os.path.exists(path_save):
        document = Document(path_save)
    else:
        document = Document()
    document.add_paragraph(ans_all)
    document.save(path_save)
    return ans_all

if __name__ == '__main__':
    main()
