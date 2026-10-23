from flask import Flask, jsonify
from flask_cors import CORS #新增跨域依赖

app = Flask(__name__)
CORS(app)  # 允许Next.js前端跨域访问后端

# 定义接口路由
@app.route("/api/hello", methods=["GET"])
def hello():
    return jsonify({"msg":"成功访问Flask后端"})

if __name__ == "__main__":
    app.run(debug=True)
