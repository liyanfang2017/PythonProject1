# main.py
from fastapi import FastAPI, UploadFile, File
import os
from datetime import datetime

app = FastAPI(title="文件上传Demo")

# 文件保存根目录
UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    # 获取文件元数据
    filename = file.filename
    content_type = file.content_type

    # 读取文件二进制内容
    file_bytes = await file.read()
    file_size = len(file_bytes)

    # 生成唯一文件名，防止同名覆盖
    suffix = filename.split(".")[-1] if "." in filename else ""
    save_name = f"{datetime.now().timestamp()}.{suffix}"
    save_path = os.path.join(UPLOAD_DIR, save_name)

    # 写入本地磁盘
    with open(save_path, "wb") as f:
        f.write(file_bytes)

    # --------------------------
    # 此处元数据入库示例（伪代码）
    # db.insert({
    #     "origin_name": filename,
    #     "save_filename": save_name,
    #     "store_path": save_path,
    #     "content_type": content_type,
    #     "file_size": file_size,
    #     "create_time": datetime.now()
    # })
    # --------------------------

    return {
        "origin_name": filename,
        "save_filename": save_name,
        "store_path": save_path,
        "content_type": content_type,
        "file_size_bytes": file_size
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("uploadfile:app", host="0.0.0.0", port=8001)
