import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
root_path = str(Path(__file__).parent.parent.parent.parent)

from app.common.config.app_config import model_config
from app.common.utils.langfunc import langen

user_prompt = "你好,你是谁?"
# model_config["model_name"] = "qwen-turbo"
model_config["model_name"] = "gemini-1.5-pro-latest"

# 压力测试
for i in range(10):
    ans = langen(model_config=model_config, user_prompt=user_prompt)
    print(ans)