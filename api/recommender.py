"""
recommender.py - 养老金产品推荐算法模块
包含用户画像分析和产品匹配逻辑
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import json
import os


class PensionProductRecommender:
    """个人养老金产品推荐系统"""

    def __init__(self, analyzer):
        """
        初始化推荐系统
        Args:
            analyzer: PensionProductAnalyzer实例
        """
        self.analyzer = analyzer
        self.user_profiles = {}
        self.recommendation_history = {}
        self.weights = self._get_default_weights()

    def _get_default_weights(self) -> Dict:
        """获取默认权重配置"""
        return {
            'age_match': 0.30,  # 年龄匹配权重
            'income_match': 0.20,  # 收入匹配权重
            'risk_match': 0.20,  # 风险匹配权重
            'retirement_match': 0.15,  # 退休规划匹配权重
            'social_security_match': 0.10,  # 社保匹配权重
            'investment_match': 0.05  # 投资金额匹配权重
        }

    def set_weights(self, weights: Dict):
        """设置推荐权重"""
        # 验证权重总和为1
        total = sum(weights.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"权重总和必须为1.0，当前为{total}")
        self.weights = weights

    def add_user_profile(self, user_id: str, profile: Dict):
        """添加用户画像"""
        # 验证用户画像
        validated_profile = self._validate_user_profile(profile)
        self.user_profiles[user_id] = validated_profile

        # 记录添加时间
        if user_id not in self.recommendation_history:
            self.recommendation_history[user_id] = []

        print(f"用户画像已添加/更新: {user_id}")
        return validated_profile

    def _validate_user_profile(self, profile: Dict) -> Dict:
        """验证用户画像数据"""
        validated = profile.copy()

        # 必需字段
        required_fields = ['age', 'annual_income', 'risk_tolerance', 'social_security_type']
        for field in required_fields:
            if field not in validated:
                raise ValueError(f"缺少必需字段: {field}")

        # 验证年龄
        if not (18 <= validated['age'] <= 70):
            print(f"警告: 年龄{validated['age']}超出常规范围(18-70)")

        # 验证年收入
        if validated['annual_income'] < 0:
            raise ValueError("年收入不能为负数")

        # 验证风险承受能力
        valid_risk_levels = ['低', '中低', '中', '中高', '高']
        if validated['risk_tolerance'] not in valid_risk_levels:
            print(f"警告: 风险承受能力'{validated['risk_tolerance']}'不在标准范围内，已调整为'中'")
            validated['risk_tolerance'] = '中'

        # 验证社保类型
        valid_social_security_types = ['城镇职工', '城乡居民', '无', '其他']
        if validated['social_security_type'] not in valid_social_security_types:
            print(f"警告: 社保类型'{validated['social_security_type']}'不在标准范围内，已调整为'城镇职工'")
            validated['social_security_type'] = '城镇职工'

        # 设置默认值（如果字段缺失）
        defaults = {
            'expected_retirement_age': 60,
            'investment_amount': validated['annual_income'] * 0.5,  # 默认投资金额为年收入的一半
            'location': '全国',
            'investment_horizon': '长期',  # 投资期限
            'liquidity_needs': '中等',  # 流动性需求
            'health_status': '良好',  # 健康状况
            'family_status': '未婚无子女'  # 家庭状况
        }

        for key, default_value in defaults.items():
            if key not in validated:
                validated[key] = default_value

        return validated

    def _calculate_age_match_score(self, user_age: int, product_min_age: Optional[int],
                                   product_max_age: Optional[int]) -> float:
        """计算年龄匹配分数"""
        if product_min_age is None and product_max_age is None:
            return 0.5  # 年龄信息缺失，给中等分数

        if product_min_age is None:
            product_min_age = 0
        if product_max_age is None:
            product_max_age = 100

        # 检查是否在年龄范围内
        if product_min_age <= user_age <= product_max_age:
            # 在范围内，根据离范围中心的距离计算分数
            center = (product_min_age + product_max_age) / 2
            distance = abs(user_age - center)
            range_width = product_max_age - product_min_age

            if range_width == 0:
                return 1.0  # 年龄要求严格匹配
            else:
                # 距离越近分数越高
                return max(0, 1.0 - (distance / range_width))
        else:
            # 不在范围内，根据距离计算分数
            if user_age < product_min_age:
                distance = product_min_age - user_age
            else:
                distance = user_age - product_max_age

            # 距离越大分数越低
            return max(0, 1.0 - (distance / 20))  # 每差20岁扣1分

    def _calculate_income_match_score(self, user_income: float, product_min_premium: float,
                                      product_payment_type: str) -> float:
        """计算收入匹配分数"""
        if product_min_premium <= 0:
            return 0.5  # 保费信息缺失

        # 将年收入转换为元
        user_income_yuan = user_income * 10000

        # 合理的保费比例 (建议不超过年收入的15%)
        reasonable_ratio = 0.15
        reasonable_premium = user_income_yuan * reasonable_ratio

        # 根据缴费类型调整合理保费
        if product_payment_type == '趸交':
            # 趸交可以承受更高的一次性支出
            reasonable_premium *= 2
        elif product_payment_type in ['月缴', '季缴']:
            # 月缴/季缴压力较小
            reasonable_premium *= 1.2

        # 计算匹配分数
        if product_min_premium <= reasonable_premium:
            # 保费在合理范围内
            if product_min_premium <= reasonable_premium * 0.3:
                return 1.0  # 保费很低，非常合适
            else:
                # 保费适中，根据比例计算分数
                ratio = product_min_premium / reasonable_premium
                return max(0.6, 1.0 - (ratio - 0.3) * 0.5)
        else:
            # 保费超出合理范围
            excess_ratio = product_min_premium / reasonable_premium
            return max(0, 1.0 - (excess_ratio - 1.0) * 0.5)

    def _calculate_risk_match_score(self, user_risk: str, product_risk: str) -> float:
        """计算风险匹配分数"""
        # 风险等级映射到数值
        risk_levels = {
            '低': 1,
            '中低': 2,
            '中': 3,
            '中高': 4,
            '高': 5,
            '未知': 3  # 默认中等风险
        }

        user_level = risk_levels.get(user_risk, 3)
        product_level = risk_levels.get(product_risk, 3)

        # 计算差异
        diff = abs(user_level - product_level)

        # 差异越大分数越低
        if diff == 0:
            return 1.0  # 完全匹配
        elif diff == 1:
            return 0.8  # 相差一级
        elif diff == 2:
            return 0.5  # 相差两级
        elif diff == 3:
            return 0.3  # 相差三级
        else:
            return 0.1  # 相差太多

    def _calculate_retirement_match_score(self, user_retirement_age: int, product_coverage_age: Optional[int],
                                          product_coverage_years: Optional[int]) -> float:
        """计算退休规划匹配分数"""
        if product_coverage_age is None and product_coverage_years is None:
            return 0.5  # 保障期限信息缺失

        if product_coverage_age is not None:
            # 产品保障至特定年龄
            age_diff = abs(product_coverage_age - user_retirement_age)
            if age_diff <= 5:
                return 1.0  # 非常匹配
            elif age_diff <= 10:
                return 0.7  # 比较匹配
            elif age_diff <= 15:
                return 0.4  # 一般匹配
            else:
                return 0.1  # 不匹配
        elif product_coverage_years is not None:
            # 产品保障固定年限
            # 假设用户从当前年龄开始投保
            expected_coverage_years = user_retirement_age - 30  # 简化计算
            if expected_coverage_years <= 0:
                expected_coverage_years = 20

            years_diff = abs(product_coverage_years - expected_coverage_years)
            if years_diff <= 5:
                return 0.8  # 比较匹配
            elif years_diff <= 10:
                return 0.5  # 一般匹配
            else:
                return 0.2  # 不匹配

        return 0.5

    def _calculate_social_security_match_score(self, user_ss_type: str, product_type: str,
                                               product_features: List[str]) -> float:
        """计算社保匹配分数"""
        # 根据社保类型调整推荐策略
        if user_ss_type == '无':
            # 无社保用户需要更全面的保障
            if '养老' in product_type or '年金' in product_type:
                if '保证' in product_features or '保本' in product_features:
                    return 1.0  # 无社保用户适合有保证的养老产品
                else:
                    return 0.7
            elif '医疗' in product_features or '健康' in product_features:
                return 0.9  # 无社保用户需要医疗保障
            else:
                return 0.3

        elif user_ss_type == '城乡居民':
            # 城乡居民社保水平较低，需要补充
            if '补充' in product_features or '附加' in product_features:
                return 0.9
            elif '养老' in product_type:
                return 0.7
            else:
                return 0.5

        elif user_ss_type == '城镇职工':
            # 城镇职工社保较全面，可以追求更高收益
            if '分红' in product_type or '万能' in product_type:
                return 0.8
            elif '养老' in product_type:
                return 0.6
            else:
                return 0.4

        else:
            # 其他情况
            return 0.5

    def _calculate_investment_match_score(self, user_investment: float, product_min_premium: float) -> float:
        """计算投资金额匹配分数"""
        if product_min_premium <= 0:
            return 0.5

        # 将投资金额转换为元
        user_investment_yuan = user_investment * 10000

        # 计算匹配度
        if user_investment_yuan >= product_min_premium * 3:
            return 1.0  # 投资金额充足
        elif user_investment_yuan >= product_min_premium:
            ratio = user_investment_yuan / product_min_premium
            return 0.5 + (ratio - 1) * 0.25  # 在1-3倍之间线性插值
        else:
            # 投资金额不足
            ratio = user_investment_yuan / product_min_premium
            return max(0.1, ratio * 0.5)  # 最低0.1分

    def _generate_recommendation_reasons(self, scores: Dict, product: Dict, user_profile: Dict) -> List[str]:
        """生成推荐理由"""
        reasons = []

        # 年龄匹配理由
        age_score = scores.get('age_score', 0)
        if age_score >= 0.8:
            reasons.append(f"年龄{user_profile['age']}岁非常适合此产品")
        elif age_score >= 0.6:
            reasons.append(f"年龄{user_profile['age']}岁在适合范围内")

        # 收入匹配理由
        income_score = scores.get('income_score', 0)
        if income_score >= 0.8:
            reasons.append("保费在您的合理承受范围内")
        elif income_score >= 0.6:
            reasons.append("保费与您的收入水平匹配")

        # 风险匹配理由
        risk_score = scores.get('risk_score', 0)
        if risk_score >= 0.8:
            reasons.append(f"风险等级({product['risk_level']})与您的风险偏好({user_profile['risk_tolerance']})匹配")

        # 退休规划理由
        retirement_score = scores.get('retirement_score', 0)
        if retirement_score >= 0.7:
            if product.get('coverage_age'):
                reasons.append(f"保障至{product['coverage_age']}岁，与您的退休规划契合")
            elif product.get('coverage_years'):
                reasons.append(f"保障{product['coverage_years']}年，适合您的长期规划")

        # 社保匹配理由
        ss_score = scores.get('ss_score', 0)
        if ss_score >= 0.8:
            if user_profile['social_security_type'] == '无':
                reasons.append("适合无社保用户，提供全面保障")
            else:
                reasons.append(f"适合{user_profile['social_security_type']}社保用户")

        # 如果没有足够的理由，添加通用理由
        if len(reasons) < 2:
            if '养老' in product['insurance_type']:
                reasons.append("这是一款养老产品，适合长期退休规划")
            if product['risk_level'] == '低':
                reasons.append("低风险产品，资金安全有保障")
            if '分红' in product['insurance_type']:
                reasons.append("分红型产品，有机会获得额外收益")

        return reasons[:3]  # 返回最多3个理由

    def get_recommendations(self, user_id: str, top_n: int = 5, filter_criteria: Dict = None) -> Dict:
        """
        获取推荐产品
        Args:
            user_id: 用户ID
            top_n: 返回前N个推荐
            filter_criteria: 过滤条件，如{'insurance_type': '养老年金', 'risk_level': '低'}

        Returns:
            推荐结果字典
        """
        if user_id not in self.user_profiles:
            return {"error": "用户不存在", "recommendations": []}

        if self.analyzer.processed_df is None:
            return {"error": "数据未处理", "recommendations": []}

        user_profile = self.user_profiles[user_id]

        print(f"为用户 {user_id} 生成推荐...")
        print(f"用户画像: 年龄{user_profile['age']}岁, 年收入{user_profile['annual_income']}万元, "
              f"风险偏好{user_profile['risk_tolerance']}, 社保类型{user_profile['social_security_type']}")

        # 获取所有产品或根据过滤条件筛选
        if filter_criteria:
            products_df = self._filter_products(filter_criteria)
        else:
            products_df = self.analyzer.processed_df.copy()

        if products_df.empty:
            return {"error": "没有找到符合条件的产品", "recommendations": []}

        # 计算每个产品的匹配分数
        scored_products = []

        for _, product in products_df.iterrows():
            try:
                scores = {}

                # 计算各项分数
                scores['age_score'] = self._calculate_age_match_score(
                    user_profile['age'], product['min_age'], product['max_age']
                )

                scores['income_score'] = self._calculate_income_match_score(
                    user_profile['annual_income'], product['min_premium'], product['payment_type']
                )

                scores['risk_score'] = self._calculate_risk_match_score(
                    user_profile['risk_tolerance'], product['risk_level']
                )

                scores['retirement_score'] = self._calculate_retirement_match_score(
                    user_profile.get('expected_retirement_age', 60),
                    product['coverage_age'], product['coverage_years']
                )

                scores['ss_score'] = self._calculate_social_security_match_score(
                    user_profile['social_security_type'],
                    product['insurance_type'],
                    product.get('feature_keywords', [])
                )

                scores['investment_score'] = self._calculate_investment_match_score(
                    user_profile.get('investment_amount', user_profile['annual_income'] * 0.5),
                    product['min_premium']
                )

                # 计算加权总分
                total_score = 0
                for key, weight in self.weights.items():
                    score_key = key.replace('_match', '_score')
                    if score_key in scores:
                        total_score += scores[score_key] * weight

                # 生成推荐理由
                reasons = self._generate_recommendation_reasons(scores, product.to_dict(), user_profile)

                # 构建推荐结果
                recommendation = {
                    'product_id': product['product_id'],
                    'product_name': product['product_name'],
                    'insurance_company': product['insurance_company'],
                    'match_score': round(total_score * 100, 1),  # 转换为百分制
                    'age_range': product['age_range_str'],
                    'insurance_type': product['insurance_type'],
                    'payment_type': product['payment_type'],
                    'min_premium': product['min_premium_str'],
                    'risk_level': product['risk_level'],
                    'coverage': product['coverage_str'],
                    'recommendation_reasons': reasons,
                    'detailed_scores': {k: round(v, 3) for k, v in scores.items()},
                    'product_details': product.to_dict()
                }

                scored_products.append(recommendation)

            except Exception as e:
                print(f"计算产品 {product.get('product_name', '未知')} 分数时出错: {e}")
                continue

        # 按匹配分数排序
        scored_products.sort(key=lambda x: x['match_score'], reverse=True)

        # 获取前N个推荐
        top_recommendations = scored_products[:top_n]

        # 记录推荐历史
        recommendation_record = {
            'timestamp': datetime.now().isoformat(),
            'user_profile': user_profile,
            'recommendations': top_recommendations,
            'total_products_evaluated': len(scored_products)
        }

        self.recommendation_history[user_id].append(recommendation_record)

        # 构建返回结果
        result = {
            "user_id": user_id,
            "user_age": user_profile['age'],
            "user_income": user_profile['annual_income'],
            "user_risk_tolerance": user_profile['risk_tolerance'],
            "user_social_security_type": user_profile['social_security_type'],
            "total_products_evaluated": len(scored_products),
            "recommendation_count": len(top_recommendations),
            "recommendations": top_recommendations,
            "recommendation_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        print(f"推荐完成: 评估了{len(scored_products)}个产品，推荐{len(top_recommendations)}个")
        return result

    def _filter_products(self, criteria: Dict) -> pd.DataFrame:
        """根据条件过滤产品"""
        if self.analyzer.processed_df is None:
            return pd.DataFrame()

        df = self.analyzer.processed_df.copy()

        # 保险类型过滤
        if 'insurance_type' in criteria:
            df = df[df['insurance_type'] == criteria['insurance_type']]

        # 风险等级过滤
        if 'risk_level' in criteria:
            df = df[df['risk_level'] == criteria['risk_level']]

        # 缴费方式过滤
        if 'payment_type' in criteria:
            df = df[df['payment_type'] == criteria['payment_type']]

        # 保险公司过滤
        if 'insurance_company' in criteria:
            df = df[df['insurance_company'] == criteria['insurance_company']]

        # 年龄过滤
        if 'min_age' in criteria:
            df = df[df['min_age'] <= criteria['min_age']]
        if 'max_age' in criteria:
            df = df[df['max_age'] >= criteria['max_age']]

        # 最低保费过滤
        if 'max_premium' in criteria:
            df = df[df['min_premium'] <= criteria['max_premium']]

        return df

    def get_recommendation_history(self, user_id: str) -> List[Dict]:
        """获取用户的推荐历史"""
        return self.recommendation_history.get(user_id, [])

    def clear_user_history(self, user_id: str):
        """清除用户的推荐历史"""
        if user_id in self.recommendation_history:
            self.recommendation_history[user_id] = []

    def save_recommendation_history(self, filepath: str = 'recommendation_history.json'):
        """保存推荐历史到文件"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.recommendation_history, f, ensure_ascii=False, indent=2)
            print(f"推荐历史已保存到: {filepath}")
            return True
        except Exception as e:
            print(f"保存推荐历史失败: {e}")
            return False

    def load_recommendation_history(self, filepath: str = 'recommendation_history.json'):
        """从文件加载推荐历史"""
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.recommendation_history = json.load(f)
                print(f"推荐历史已从 {filepath} 加载")
                return True
            except Exception as e:
                print(f"加载推荐历史失败: {e}")
                return False
        return False

    def generate_comparison_table(self, product_ids: List[str]) -> List[Dict]:
        """生成产品对比表"""
        comparison_data = []

        for product_id in product_ids:
            product = self.analyzer.get_product_details(product_id)
            if product:
                comparison_data.append(product)

        if not comparison_data:
            return []

        # 定义对比字段
        comparison_fields = [
            ('product_name', '产品名称'),
            ('insurance_company', '保险公司'),
            ('age_range_str', '适合年龄'),
            ('insurance_type', '保险类型'),
            ('payment_type', '缴费方式'),
            ('payment_periods_str', '缴费年限'),
            ('min_premium_str', '最低保费'),
            ('risk_level', '风险等级'),
            ('coverage_str', '保障期限'),
            ('sales_channel', '销售渠道'),
            ('sales_scope', '销售范围')
        ]

        # 构建对比结果
        comparison_result = []
        for field_key, field_name in comparison_fields:
            row = {'feature': field_name}
            for i, product in enumerate(comparison_data):
                row[f'product_{i + 1}'] = product.get(field_key, 'N/A')
            comparison_result.append(row)

        return comparison_result

    def get_personalized_advice(self, user_id: str) -> Dict:
        """获取个性化建议"""
        if user_id not in self.user_profiles:
            return {"error": "用户不存在"}

        user_profile = self.user_profiles[user_id]
        advice = {
            "user_id": user_id,
            "advice_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "general_advice": [],
            "product_type_recommendations": [],
            "risk_management_advice": [],
            "next_steps": []
        }

        # 根据用户画像生成建议
        age = user_profile['age']
        income = user_profile['annual_income']
        risk_tolerance = user_profile['risk_tolerance']
        ss_type = user_profile['social_security_type']

        # 通用建议
        advice["general_advice"].append("个人养老金产品是退休规划的重要组成部分，建议尽早规划。")

        if age < 30:
            advice["general_advice"].append("您还年轻，可以考虑风险稍高但长期收益更好的产品。")
            advice["product_type_recommendations"].append("考虑分红型或万能型产品，追求长期增值。")
        elif age < 50:
            advice["general_advice"].append("这是规划养老的关键时期，建议建立稳定的养老金积累计划。")
            advice["product_type_recommendations"].append("养老年金保险和两全保险都是不错的选择。")
        else:
            advice["general_advice"].append("临近退休，应注重资金安全和稳定收益。")
            advice["product_type_recommendations"].append("推荐低风险的养老年金产品或终身寿险。")

        # 收入相关建议
        if income < 10:
            advice["general_advice"].append("收入水平适中，建议选择缴费灵活、门槛较低的产品。")
        elif income < 30:
            advice["general_advice"].append("收入良好，可以适当配置不同风险等级的产品进行组合。")
        else:
            advice["general_advice"].append("收入较高，可以考虑配置多种产品实现多元化养老规划。")

        # 风险承受建议
        if risk_tolerance in ['低', '中低']:
            advice["risk_management_advice"].append("您的风险承受能力较低，建议选择保本型或保证收益的产品。")
            advice["product_type_recommendations"].append("传统养老年金保险或低风险两全保险适合您。")
        elif risk_tolerance == '中':
            advice["risk_management_advice"].append("您可以承受中等风险，分红型产品可能带来更好收益。")
        else:
            advice["risk_management_advice"].append("您能承受较高风险，可以考虑万能型或投资连结型产品。")

        # 社保相关建议
        if ss_type == '无':
            advice["general_advice"].append("您没有社保，养老金规划尤为重要，建议优先考虑保障全面的产品。")
            advice["product_type_recommendations"].append("需要重点关注产品的保障范围和稳定性。")

        # 下一步建议
        advice["next_steps"].append("查看系统推荐的产品列表")
        advice["next_steps"].append("比较3-5个感兴趣的产品")
        advice["next_steps"].append("咨询专业理财顾问获取更详细建议")
        advice["next_steps"].append("考虑税收优惠政策，合理规划缴费")

        return advice


# 测试函数
def test_recommender():
    """测试推荐系统"""
    print("测试推荐系统...")

    # 导入数据处理器
    from data_processor import PensionProductAnalyzer

    # 创建数据处理器
    analyzer = PensionProductAnalyzer()
    analyzer.create_demo_data()
    analyzer.process_data()

    # 创建推荐器
    recommender = PensionProductRecommender(analyzer)

    # 创建测试用户
    test_user_profile = {
        'age': 35,
        'annual_income': 20.0,  # 20万元
        'risk_tolerance': '中',
        'social_security_type': '城镇职工',
        'expected_retirement_age': 60,
        'investment_amount': 10.0,  # 10万元
        'location': '北京'
    }

    user_id = "test_user_001"
    recommender.add_user_profile(user_id, test_user_profile)

    # 获取推荐
    print("\n获取推荐产品...")
    recommendations = recommender.get_recommendations(user_id, top_n=3)

    if "error" in recommendations:
        print(f"错误: {recommendations['error']}")
    else:
        print(f"推荐完成! 共评估{recommendations['total_products_evaluated']}个产品")
        print(f"推荐{recommendations['recommendation_count']}个产品:")

        for i, rec in enumerate(recommendations['recommendations'], 1):
            print(f"\n{i}. {rec['product_name']}")
            print(f"   保险公司: {rec['insurance_company']}")
            print(f"   匹配度: {rec['match_score']}%")
            print(f"   适合年龄: {rec['age_range']}")
            print(f"   保险类型: {rec['insurance_type']}")
            print(f"   风险等级: {rec['risk_level']}")
            print(f"   最低保费: {rec['min_premium']}")
            print(f"   推荐理由: {' | '.join(rec['recommendation_reasons'])}")

    # 测试产品对比
    print("\n测试产品对比...")
    if recommendations['recommendations']:
        product_ids = [rec['product_id'] for rec in recommendations['recommendations'][:2]]
        comparison = recommender.generate_comparison_table(product_ids)
        print(f"产品对比表 ({len(comparison)}个对比项目)")

    # 测试个性化建议
    print("\n测试个性化建议...")
    advice = recommender.get_personalized_advice(user_id)
    print(f"个性化建议生成时间: {advice['advice_time']}")
    print("通用建议:")
    for item in advice['general_advice']:
        print(f"  - {item}")

    print("\n推荐系统测试完成!")


if __name__ == "__main__":
    test_recommender()