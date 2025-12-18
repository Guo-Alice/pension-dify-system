"""
最小化测试 API - 验证部署是否成功
"""
from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "养老金推荐API部署成功！",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "python_version": "3.11"
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/test')
def test():
    return jsonify({
        "success": True,
        "message": "API测试成功",
        "data": {
            "version": "1.0.0",
            "author": "Pension System",
            "description": "养老金产品推荐API"
        }
    })

# Vercel 需要这个
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
else:
    print(" API 已启动（Vercel 环境）")
    print(f" 启动时间: {datetime.now().isoformat()}")
