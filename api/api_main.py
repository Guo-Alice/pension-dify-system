"""
养老金产品推荐API - Dify工具专用
整合了你的数据处理和推荐算法
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import json
import os
import sys
from datetime import datetime

# 添加当前目录到路径，导入你的模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入你的数据处理和推荐模块
from data_processor import PensionProductAnalyzer
from recommender import PensionProductRecommender

app = Flask(__name__)
CORS(app)

# 全局变量，避免重复加载
analyzer = None
recommender = None


def initialize_system():
    """初始化系统，加载数据"""
    global analyzer, recommender

    print("正在初始化养老金产品推荐系统...")

    # 初始化数据处理器
    analyzer = PensionProductAnalyzer()

    # 尝试加载Excel数据，如果失败则使用演示数据
    if analyzer.df is None:
        analyzer.create_demo_data()

    # 处理数据
    if analyzer.processed_df is None:
        analyzer.process_data()

    # 初始化推荐器
    recommender = PensionProductRecommender(analyzer)

    print(f"系统初始化完成，共加载 {len(analyzer.processed_df) if analyzer.processed_df is not None else 0} 个产品")
    return analyzer, recommender


# 应用启动时初始化
analyzer, recommender = initialize_system()


@app.route('/')
def home():
    """API主页"""
    return jsonify({
        "service": "养老金产品推荐系统API",
        "version": "3.0",
        "description": "基于真实养老保险数据的智能推荐系统，专为Dify工作流设计",
        "endpoints": {
            "POST /recommend": "获取养老金产品推荐",
            "GET /health": "健康检查",
            "GET /stats": "系统统计",
            "GET /companies": "保险公司列表"
        },
        "status": "运行中",
        "data_info": {
            "total_products": len(analyzer.df) if analyzer.df is not None else 0,
            "processed_products": len(analyzer.processed_df) if analyzer.processed_df is not None else 0,
            "companies": len(analyzer.get_all_companies()) if analyzer else 0
        }
    })


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system_initialized": analyzer is not None and recommender is not None,
        "data_loaded": analyzer.df is not None if analyzer else False,
        "memory_usage": f"{sys.getsizeof(analyzer) if analyzer else 0 / 1024 / 1024:.2f} MB"
    })


@app.route('/stats', methods=['GET'])
def get_statistics():
    """获取系统统计信息"""
    if analyzer is None:
        return jsonify({"error": "系统未初始化"}), 500

    try:
        summary = analyzer.get_summary_statistics()
        return jsonify({
            "success": True,
            "statistics": summary,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/companies', methods=['GET'])
def get_companies():
    """获取所有保险公司列表"""
    if analyzer is None:
        return jsonify({"error": "系统未初始化"}), 500

    companies = analyzer.get_all_companies()
    return jsonify({
        "success": True,
        "companies": companies,
        "count": len(companies)
    })


@app.route('/recommend', methods=['POST'])
def recommend_products():
    """
    主推荐接口 - Dify工作流调用
    接收用户信息，返回推荐产品

    请求体JSON格式:
    {
        "age": 35,                    # 年龄（必需）
        "annual_income": 25.0,        # 年收入（万元，必需）
        "risk_tolerance": "中",       # 风险偏好（必需）：低/中低/中/中高/高
        "location": "北京",           # 所在地区（可选）
        "social_security": "城镇职工", # 社保类型（可选）
        "retirement_age": 60,         # 计划退休年龄（可选）
        "investment_amount": 12.0,    # 计划投资金额（万元，可选）
        "top_n": 5,                   # 返回推荐数量（可选，默认5）
        "filter_criteria": {          # 过滤条件（可选）
            "insurance_type": "养老年金",
            "risk_level": "中"
        }
    }
    """
    try:
        # 获取请求数据
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "请求体必须为JSON格式",
                "required_fields": ["age", "annual_income", "risk_tolerance"]
            }), 400

        # 必需字段检查
        required_fields = ['age', 'annual_income', 'risk_tolerance']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return jsonify({
                "success": False,
                "error": f"缺少必需字段: {', '.join(missing_fields)}"
            }), 400

        # 验证年龄范围
        age = data['age']
        if not isinstance(age, (int, float)) or age < 0 or age > 120:
            return jsonify({
                "success": False,
                "error": "年龄必须在0-120岁之间"
            }), 400

        # 验证年收入
        income = data['annual_income']
        if not isinstance(income, (int, float)) or income < 0:
            return jsonify({
                "success": False,
                "error": "年收入必须为非负数"
            }), 400

        # 验证风险偏好
        valid_risk_levels = ['低', '中低', '中', '中高', '高']
        risk_tolerance = data['risk_tolerance']
        if risk_tolerance not in valid_risk_levels:
            return jsonify({
                "success": False,
                "error": f"风险偏好必须是: {', '.join(valid_risk_levels)}"
            }), 400

        # 构建用户画像
        user_profile = {
            'age': int(age),
            'annual_income': float(income),
            'risk_tolerance': risk_tolerance,
            'social_security_type': data.get('social_security', '城镇职工'),
            'expected_retirement_age': data.get('retirement_age', 60),
            'investment_amount': data.get('investment_amount', income * 0.5),  # 默认投资金额为年收入的一半
            'location': data.get('location', '全国')
        }

        # 可选字段
        if 'family_status' in data:
            user_profile['family_status'] = data['family_status']
        if 'health_status' in data:
            user_profile['health_status'] = data['health_status']
        if 'liquidity_needs' in data:
            user_profile['liquidity_needs'] = data['liquidity_needs']

        # 创建用户ID（基于时间戳）
        import hashlib
        user_id = hashlib.md5(f"{datetime.now().isoformat()}{age}{income}{risk_tolerance}".encode()).hexdigest()[:12]

        # 添加用户画像到推荐器
        recommender.add_user_profile(user_id, user_profile)

        # 获取过滤条件
        filter_criteria = data.get('filter_criteria', None)
        top_n = data.get('top_n', 5)

        # 获取推荐结果
        recommendations = recommender.get_recommendations(
            user_id=user_id,
            top_n=top_n,
            filter_criteria=filter_criteria
        )

        # 格式化响应，便于Dify的LLM处理
        formatted_response = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "api_version": "3.0",
            "user_profile": user_profile,
            "total_products_evaluated": recommendations.get("total_products_evaluated", 0),
            "recommendation_count": len(recommendations.get("recommendations", [])),
            "recommendations": []
        }

        # 格式化每个推荐产品
        for rec in recommendations.get("recommendations", []):
            formatted_rec = {
                "product_id": rec.get("product_id"),
                "product_name": rec.get("product_name"),
                "insurance_company": rec.get("insurance_company"),
                "match_score": rec.get("match_score"),  # 百分制匹配度
                "match_percentage": f"{rec.get('match_score')}%",
                "age_range": rec.get("age_range"),
                "insurance_type": rec.get("insurance_type"),
                "payment_type": rec.get("payment_type"),
                "min_premium": rec.get("min_premium"),
                "risk_level": rec.get("risk_level"),
                "coverage": rec.get("coverage"),
                "recommendation_reasons": rec.get("recommendation_reasons", []),
                "key_features": rec.get("product_details", {}).get("feature_keywords", []),
                "sales_channel": rec.get("product_details", {}).get("sales_channel", "未知"),
                "sales_scope": rec.get("product_details", {}).get("sales_scope", "未知")
            }
            formatted_response["recommendations"].append(formatted_rec)

        # 添加个性化建议
        personalized_advice = recommender.get_personalized_advice(user_id)
        formatted_response["personalized_advice"] = {
            "general_advice": personalized_advice.get("general_advice", []),
            "product_type_recommendations": personalized_advice.get("product_type_recommendations", []),
            "next_steps": personalized_advice.get("next_steps", [])
        }

        return jsonify(formatted_response)

    except Exception as e:
        app.logger.error(f"推荐接口异常: {str(e)}")
        return jsonify({
            "success": False,
            "error": "服务器内部错误",
            "detail": str(e)
        }), 500


@app.route('/product/<product_id>', methods=['GET'])
def get_product_detail(product_id):
    """获取产品详细信息"""
    if analyzer is None:
        return jsonify({"error": "系统未初始化"}), 500

    try:
        product_details = analyzer.get_product_details(product_id)
        if product_details:
            return jsonify({
                "success": True,
                "product": product_details
            })
        else:
            return jsonify({
                "success": False,
                "error": f"未找到产品ID: {product_id}"
            }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/search', methods=['GET'])
def search_products():
    """搜索产品"""
    if analyzer is None:
        return jsonify({"error": "系统未初始化"}), 500

    try:
        keyword = request.args.get('keyword', '')
        limit = int(request.args.get('limit', 10))

        if not keyword:
            return jsonify({
                "success": False,
                "error": "请提供搜索关键词"
            }), 400

        results_df = analyzer.search_products(keyword)
        results = results_df.head(limit).to_dict('records')

        return jsonify({
            "success": True,
            "keyword": keyword,
            "count": len(results),
            "results": results
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# 测试接口
@app.route('/test', methods=['GET'])
def test_endpoint():
    """测试接口，返回示例推荐"""
    test_user_data = {
        "age": 35,
        "annual_income": 25.0,
        "risk_tolerance": "中",
        "location": "北京",
        "social_security": "城镇职工",
        "retirement_age": 60,
        "investment_amount": 12.0
    }

    # 模拟POST请求
    with app.test_client() as client:
        response = client.post('/recommend', json=test_user_data)
        return response.data


if __name__ == '__main__':
    print("=" * 60)
    print("养老金产品推荐系统API启动中...")
    print("版本: 3.0 (整合式架构)")
    print("本地访问: http://localhost:5000")
    print("API端点: POST http://localhost:5000/recommend")
    print("=" * 60)

    # 启动前重新初始化确保数据加载
    initialize_system()

    app.run(debug=True, host='0.0.0.0', port=5000)
else:
    # Vercel部署时
    print("养老金推荐API模块已导入，准备在Vercel上运行...")
    initialize_system()
