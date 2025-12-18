"""
data_processor.py - 养老金产品数据处理模块
负责读取、解析和预处理养老保险产品数据
"""

import pandas as pd
import numpy as np
import re
import json
from typing import Dict, List, Optional, Tuple, Any
import warnings

warnings.filterwarnings('ignore')
import os


class PensionProductAnalyzer:
    """个人养老金产品分析器"""

    def __init__(self, excel_path: str = None):
        """
        初始化分析器
        Args:
            excel_path: Excel文件路径
        """
        self.excel_path = excel_path
        self.df = None
        self.processed_df = None
        self.products_by_id = {}
        self.products_by_company = {}

        # 如果没有提供路径，尝试自动查找
        if excel_path is None:
            self.excel_path = self.find_excel_file()

        if self.excel_path:
            # 尝试加载数据
            success = self.load_data()
            if not success:
                print("警告: Excel文件读取失败，请检查文件格式或sheet名称")
                print("将尝试使用演示数据...")
                self.create_demo_data()
        else:
            print("警告: 未找到Excel文件，将使用演示数据")
            self.create_demo_data()

    def find_excel_file(self):
        """查找Excel文件"""
        possible_paths = [
            'insurance.xlsx',  # 当前目录
            'pension_product_tool/data/insurance.xlsx',  # data子目录
            '../insurance.xlsx',  # 上级目录
            os.path.join(os.path.dirname(__file__), 'insurance.xlsx'),  # 脚本所在目录
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'insurance.xlsx')
        ]

        for path in possible_paths:
            if os.path.exists(path):
                print(f"找到Excel文件: {path}")
                return path

        print("未找到养老保险.xlsx文件")
        print("请将文件放在以下位置之一:")
        for path in possible_paths[:3]:
            print(f"  - {path}")
        return None

    def load_data(self):
        """加载Excel数据"""
        try:
            # 尝试读取Excel文件
            print(f"正在加载数据文件: {self.excel_path}")

            # 尝试不同的sheet名称
            sheet_names = ['养老保险', 'Sheet1', 'Sheet2', 'Sheet3', '产品数据', '数据']

            for sheet_name in sheet_names:
                try:
                    self.df = pd.read_excel(self.excel_path, sheet_name=sheet_name)
                    print(f"成功从'{sheet_name}' sheet加载数据，共 {len(self.df)} 条记录")
                    print(f"数据列：{list(self.df.columns)}")
                    return True
                except Exception as e:
                    continue

            # 如果以上sheet名称都失败，尝试第一个sheet
            try:
                self.df = pd.read_excel(self.excel_path, sheet_name=0)
                print(f"成功从第一个sheet加载数据，共 {len(self.df)} 条记录")
                print(f"数据列：{list(self.df.columns)}")
                return True
            except Exception as e:
                print(f"读取第一个sheet也失败: {e}")
                return False

        except Exception as e:
            print(f"加载Excel文件失败: {e}")
            return False

    def create_demo_data(self):
        """创建演示数据（如果无法读取Excel）"""
        print("正在创建演示数据...")

        # 基于提供的Excel内容创建演示数据
        data = {
            '证券代码': [
                '76100558', '76100560', '76100681', '76100719', '76100747',
                '76100749', '76100758', '76100759', '76100764', '76100767',
                '76100778', '76100790', '76100797', '76100801', '76100821',
                '76100822', '76100824', '76100831', '76100832', '76100836',
                '76100837', '76100838', '76100840', '76100841', '76100842',
                '76100843', '76100844'
            ],
            '证券名称': [
                '中宏人寿:中宏安享团体年金保险(万能型)',
                '华泰人寿:金鑫延年年金保险(分红型)',
                '长生人寿:金福来团体养老年金保险(万能型)',
                '幸福人寿:幸福财富养老年金保险(分红型)',
                '光大永明人寿:光大永明福运百年养老年金保险(分红型)',
                '国泰人寿:国泰长瑞年年年金保险(分红型)',
                '海康人寿:[安享无忧]两全保险(分红型)',
                '海康人寿:海康『海纳福利』年金保险(分红型)(停售)',
                '海康人寿:海康[串串红]两全保险(C款)(分红型)',
                '交银康联:交银康联金色人生养老两全保险(分红型)',
                '英大人寿:英大元利团体年金保险(万能型)',
                '光大永明人寿:光大永明金保顺B两全保险(分红型)',
                '建信人寿:补充养老团体年金保险(万能型)B款',
                '中荷人寿:中荷岁岁红团体年金保险(分红型)',
                '太平人寿:太平团体年金保险(分红型)',
                '太平人寿:太平团体退休金保险(分红型)(停售)',
                '太平人寿:太平财富成长型年金保险(分红型)',
                '中英人寿:中英团体年金保险(分红型)',
                '中英人寿:中英团体年金保险B款(分红型)',
                '太平人寿:太平寿比南山附加养老两全保险(分红型)(停售)',
                '太平人寿:太平一诺千金终身寿险(分红型)',
                '太平人寿:太平成长型年金保险(分红型)',
                '太平人寿:太平福寿连连两全保险(分红型)(停售)',
                '太平人寿:太平福祥一生终身寿险(分红型)',
                '太平人寿:太平团体终身寿险(分红型)',
                '英大人寿:英大金元宝两全保险A款(分红型)',
                '英大人寿:英大金元宝两全保险B款(分红型)'
            ],
            '适合年龄(BXLC)': [
                '--',
                '被保险人0周岁（出生满30天）至50周岁（年金领取年龄55周岁）',
                '被保险人：机关、企业、事业单位和社会团体的团体成员，经本公司1审核同意，可作为本合同的被保险人。本合同接受的团体成员的投保年龄为十六周岁以上。',
                '出生满30天(含)至60周岁(含)',
                '出生满60天至64岁',
                '出生满30天至60周岁',
                '7 天至59岁',
                '18-55周岁',
                '出生满30天至65周岁',
                '本合同接受的最小投保年龄为18周岁，最大投保年龄为男性60周岁，女性50周岁',
                '--',
                '18至65周岁',
                '二、被保险人：团体所属成员中凡年龄在十六周岁以上、六十五周岁以下的，可作为被保险人参加本合同。',
                '被保险人所在团体可作为投保人，为其成员向本公司投保本保险。本合同接受的被保险人的投保年龄为十六至六十五周岁。',
                '16周岁至65周岁',
                '年满16周岁，身体健康，能正常工作或劳动的在职员工',
                '出生满60天—50周岁',
                '--',
                '--',
                '为出生满60天至65周岁',
                '出生满60天至65周岁',
                '45周岁至70周岁',
                '出生满60天至55周岁',
                '出生满60天至50周岁',
                '16周岁至65周岁',
                '零周岁（指出生满三十天且已健康出院的婴儿）至六十五周岁。',
                '零周岁（指出生满三十天且已健康出院的婴儿）至六十五周岁。'
            ],
            '产品特色(BXLC)': [
                '本产品为团体养老年金保险，并有保本型账户可供投资选择...',
                '投保简单灵活 生存返还快捷...',
                '--',
                '年年递增、提前领取、高额身价、八八祝寿...',
                '老有所养,长寿无忧...',
                '1、保证领取二十年，理财安全收入丰...',
                '安享健康生活 规划无忧晚年...',
                '年年领取 关爱备至...',
                '一、满期给付 稳健收益...',
                '产品特色：保证年金，倍感安心...',
                '产品特色：1、养老、投资双重功能...',
                '产品特色：快速返还，年年得利...',
                '产品特色：缴费灵活自由 领取便利多样...',
                '险种特色：1、养老规划，运筹帷幄...',
                '产品特色：专属养老，特别福利...',
                '产品特色:退休养老，特别福利...',
                '计划特色：年金成长，节节攀高...',
                '产品特色：资金稳健增值，共享经营成果...',
                '产品特色：资金增值保证，共享经营成果...',
                '产品特色：领取灵活多变，晚年生活安逸...',
                '产品特色：一诺千金，5大保证...',
                '产品特色：一诺千金，5大保证...',
                '隔年给付，快速返还...',
                '高额身故保障，更有双倍赔付...',
                '产品特色：保费经济、保障充分...',
                '产品特色：1、点滴积累 规划未来...',
                '产品特色：1、点滴积累 规划未来...'
            ],
            '保费说明(BXLC)': [
                '期缴',
                '3年、5年、10年、15年、20年，以保险单载明为准。',
                '投保人及被保险人可以定期或不定期、定额或不定额地交纳保险费。投保人及被保险人交纳保险费须符合本公司最低保险费交纳额度的规定。',
                '交费期间:1次交清、 3年交、5年交、10年交、15年交、20年交。保险费要求:选择一次交情时,每单保险费不得低于5000元;选择期交时,每单保险费不得低于3000元。投保要求:每单基本保险金额不得低于1000元,1000元以上部分应为1000元的整数倍。',
                '交费方式:一次交清,分3、5、10、20、30年交或交至领取年龄',
                '交费方式：趸交、年交、半年交、季交、月交\n交费年期：趸交、5年期、10年期、20年期',
                '缴费期间: 趸缴、3年、5年、10年、15年、20年或缴费至被保险人年满55、60、65周岁。',
                '缴费期限：5年、10年、15年、20年、年交',
                '趸交，保费限制：10,000元起购，且为1,000元的整数倍',
                '--',
                '本合同的保险费由投保人交纳或由投保人和被保险人共同交纳。在投保人首次交纳保险费后、被保险人开始领取养老保险金之前，投保人和被保险人可以不定期、不定额地交纳保险费，但被保险人每次交纳的保险费应不低于当时本公司规定的最低交费金额。',
                '按份出售，每份保费1000元',
                '--',
                '本合同的保险费由投保人承担或由投保人和被保险人共同承担。在年金领取开始日之前，经本公司同意，投保人或被保险人可以不定期、不定额地向本公司缴纳保险费。',
                '趸缴、期缴',
                '--',
                '交费期：5年交或10年交',
                '保险费由投保人交纳或投保人和被保险人共同交纳，交费方式为不定期不定额交费。投保人也可和本公司约定按照年交方式或月交方式进行交费。',
                '--',
                '--',
                '本合同保险费的交费方式和交费期限由您和我们约定，并在保险单或批注上列明。您可以选择趸交或分期交纳保险费。选择分期交纳保险费的，您在交纳了首期保险费后，应按本合同的约定在每个保险费到期日交纳余下各期的保险费。',
                '趸交',
                '期缴',
                '期缴',
                '趸缴、期缴',
                '本合同保险费的交费方式为年交，交费期间为三年',
                '在本合同保险期间内且本合同有效，我们承担下列保险责任：...'
            ],
            '保险公司全称(BXLC)': [
                '中宏人寿保险有限公司',
                '华泰人寿保险股份有限公司',
                '长生人寿保险有限公司',
                '幸福人寿保险股份有限公司',
                '光大永明人寿保险有限公司',
                '国泰人寿保险有限责任公司',
                '同方全球人寿保险有限公司',
                '同方全球人寿保险有限公司',
                '同方全球人寿保险有限公司',
                '交银康联人寿保险有限公司',
                '英大泰和人寿保险股份有限公司',
                '光大永明人寿保险有限公司',
                '建信人寿保险有限公司',
                '中荷人寿保险有限公司',
                '太平人寿保险有限公司',
                '太平人寿保险有限公司',
                '太平人寿保险有限公司',
                '中英人寿保险有限公司',
                '中英人寿保险有限公司',
                '太平人寿保险有限公司',
                '太平人寿保险有限公司',
                '太平人寿保险有限公司',
                '太平人寿保险有限公司',
                '太平人寿保险有限公司',
                '太平人寿保险有限公司',
                '英大泰和人寿保险股份有限公司',
                '英大泰和人寿保险股份有限公司'
            ],
            '缴费方式(BXLC)': [
                '--', '年交', '--', '--', '--', '--', '--', '年交', '--', '--', '--', '年交', '--', '--', '--', '--',
                '年交', '--', '--', '--', '--', '趸交', '--', '--', '--', '年交', '年交'
            ],
            '销售渠道(BXLC)': [
                '--', '个人营销', '--', '银保产品', '个人营销', '个人营销', '个人营销', '个人营销', '银保产品', '--',
                '--', '银保产品', '团体直销', '公司直销', '--', '团体直销', '银保产品', '团体直销', '团体直销', '--',
                '个人营销', '个人营销', '个人营销', '个人营销', '--', '银保产品', '银保产品'
            ],
            '销售范围(BXLC)': [
                '--', '全国', '--', '全国', '全国', '--', '--', '--', '--', '全国', '全国', '全国', '--', '--', '全国',
                '--', '--', '全国', '全国', '--', '全国', '全国', '全国', '全国', '--', '全国', '全国'
            ],
            '保障期限(BXLC)': [
                '--',
                '保险期间自合同生效日开始，至被保险人年满90周岁后的首个保险单周年日止。',
                '本合同的保险期间自生效日的零时起至本合同约定满期日的零时止。',
                '保险期限:按年限,88年',
                '保障至被保险人100岁',
                '终身',
                '至70周岁',
                '至被保险人75周岁',
                '5年',
                '至被保险人年满80周岁',
                '--',
                '交费3年，保险期间为8年；交费5年，保险期间为10年',
                '--',
                '--',
                '--',
                '--',
                '--',
                '--',
                '--',
                '--',
                '--',
                '--',
                '至被保险人88周岁后的首个保险单周年日',
                '至被保险人105周岁后的首个保险单周年日',
                '终身',
                '保险期间为十年',
                '保险期间为十年'
            ]
        }

        self.df = pd.DataFrame(data)
        print(f"创建演示数据完成，共 {len(self.df)} 条记录")

    def extract_age_range(self, age_str: str) -> Tuple[Optional[int], Optional[int]]:
        """
        从年龄描述中提取最小和最大年龄
        Args:
            age_str: 年龄描述字符串
        Returns:
            (min_age, max_age): 最小年龄和最大年龄
        """
        if pd.isna(age_str) or age_str == '--' or age_str == '':
            return None, None

        age_str = str(age_str).strip()

        # 常见模式匹配
        patterns = [
            # 模式: X周岁至Y周岁
            r'(\d+)[\s\-]*周岁.*至.*(\d+)[\s\-]*周岁',
            # 模式: 出生满X天至Y岁
            r'出生满[\s\d天]+至.*?(\d+)[\s岁周岁]+',
            # 模式: X岁至Y岁
            r'(\d+)\s*岁.*至.*(\d+)\s*岁',
            # 模式: X到Y周岁
            r'(\d+).*?(\d+)\s*周岁',
            # 模式: X-Y周岁
            r'(\d+)[\-\~](\d+)\s*周岁',
            # 模式: 单个年龄
            r'(\d+)[\s\-]*岁',
            # 模式: X周岁
            r'(\d+)\s*周岁',
            # 模式: 年龄范围如18-55
            r'(\d+)[\-\~](\d+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, age_str)
            if matches:
                try:
                    if len(matches[0]) == 2:
                        min_age = int(matches[0][0])
                        max_age = int(matches[0][1])
                        # 验证合理性
                        if 0 <= min_age <= 100 and 0 <= max_age <= 100 and min_age <= max_age:
                            return min_age, max_age
                    elif len(matches[0]) == 1:
                        age = int(matches[0][0])
                        if 0 <= age <= 100:
                            return age, age
                except (ValueError, IndexError):
                    continue

        # 特殊处理出生天数
        if '出生满' in age_str or '天' in age_str or '婴儿' in age_str:
            return 0, None

        # 处理十六周岁以上等描述
        if '十六周岁以上' in age_str or '16周岁以上' in age_str:
            return 16, None

        # 处理年龄范围如"16至65"
        if '至' in age_str:
            parts = age_str.split('至')
            if len(parts) == 2:
                try:
                    min_age = int(re.search(r'\d+', parts[0]).group())
                    max_age = int(re.search(r'\d+', parts[1]).group())
                    if 0 <= min_age <= 100 and 0 <= max_age <= 100 and min_age <= max_age:
                        return min_age, max_age
                except:
                    pass

        # 最后尝试提取所有数字
        numbers = re.findall(r'\d+', age_str)
        if len(numbers) >= 2:
            try:
                min_age = int(numbers[0])
                max_age = int(numbers[1])
                if 0 <= min_age <= 100 and 0 <= max_age <= 100 and min_age <= max_age:
                    return min_age, max_age
            except:
                pass
        elif len(numbers) == 1:
            try:
                age = int(numbers[0])
                if 0 <= age <= 100:
                    return age, age
            except:
                pass

        return None, None

    def extract_insurance_type(self, name: str) -> str:
        """提取保险类型"""
        if pd.isna(name):
            return '未知'

        name_str = str(name).lower()

        type_mapping = {
            '年金保险': ['年金保险', '年金险'],
            '养老年金': ['养老', '退休金', '养老年金'],
            '两全保险': ['两全保险', '两全险'],
            '万能型': ['万能型', '万能险'],
            '分红型': ['分红型', '分红险'],
            '团体保险': ['团体', '团体年金', '团体养老'],
            '终身寿险': ['终身寿险'],
            '附加险': ['附加']
        }

        for ins_type, keywords in type_mapping.items():
            for keyword in keywords:
                if keyword in name_str:
                    return ins_type

        # 根据名称中的关键词判断
        if '年金' in name_str:
            return '年金保险'
        elif '养老' in name_str:
            return '养老年金'
        elif '两全' in name_str:
            return '两全保险'

        return '其他'

    def extract_premium_info(self, premium_str: str) -> Dict:
        """提取保费信息"""
        if pd.isna(premium_str) or premium_str == '--' or premium_str == '':
            return {'payment_type': '未知', 'min_amount': 0, 'periods': []}

        premium_info = {'payment_type': '未知', 'min_amount': 0, 'periods': []}
        premium_lower = str(premium_str).lower()

        # 缴费类型
        payment_types = {
            '趸交': ['趸交', '一次交清', '趸缴', '一次性'],
            '期缴': ['期缴', '年交', '分期', '定期'],
            '月缴': ['月交', '月缴', '每月'],
            '季缴': ['季交', '季缴', '每季'],
            '半年缴': ['半年交', '半年缴']
        }

        for p_type, keywords in payment_types.items():
            for keyword in keywords:
                if keyword in premium_lower:
                    premium_info['payment_type'] = p_type
                    break
            if premium_info['payment_type'] != '未知':
                break

        # 提取缴费年限
        period_patterns = [
            r'(\d+)\s*年交',
            r'交费期间[：:]\s*(\d+)年',
            r'缴费[：:]\s*(\d+)年',
            r'(\d+)年期',
            r'分\s*(\d+)\s*年',
            r'(\d+)\s*年'
        ]

        all_periods = []
        for pattern in period_patterns:
            periods = re.findall(pattern, premium_lower)
            if periods:
                for p in periods:
                    if p.isdigit():
                        period = int(p)
                        if 1 <= period <= 50:  # 合理的缴费年限范围
                            all_periods.append(period)

        # 去重并排序
        premium_info['periods'] = sorted(list(set(all_periods)))

        # 提取最低保费
        amount_patterns = [
            r'(\d+,?\d*)\s*元',
            r'不低于\s*(\d+,?\d*)\s*元',
            r'每单保险费不得低于\s*(\d+,?\d*)',
            r'(\d+,?\d*)\s*元起',
            r'保费\s*(\d+,?\d*)\s*元',
            r'(\d+,?\d*)\s*元/份'
        ]

        for pattern in amount_patterns:
            amounts = re.findall(pattern, premium_lower)
            if amounts:
                try:
                    amount_str = amounts[0].replace(',', '')
                    amount = int(amount_str)
                    if amount > 0:
                        premium_info['min_amount'] = amount
                        break
                except (ValueError, IndexError):
                    continue

        # 如果没有找到具体金额，根据产品类型设置默认值
        if premium_info['min_amount'] == 0:
            # 根据产品类型设置默认最低保费
            if premium_info['payment_type'] == '趸交':
                premium_info['min_amount'] = 10000  # 趸交通常1万元起
            else:
                premium_info['min_amount'] = 1000  # 期交通常1000元起

        return premium_info

    def extract_coverage_period(self, period_str: str) -> Dict:
        """提取保障期限信息"""
        if pd.isna(period_str) or period_str == '--' or period_str == '':
            return {'type': '未知', 'age': None, 'years': None, 'description': ''}

        period_info = {'type': '未知', 'age': None, 'years': None, 'description': str(period_str)}
        period_lower = str(period_str).lower()

        # 提取年龄
        age_patterns = [
            r'至.*?(\d+)\s*周岁',
            r'满.*?(\d+)\s*周岁',
            r'(\d+)\s*周岁',
            r'(\d+)\s*岁',
            r'年满\s*(\d+)\s*周岁',
            r'至\s*(\d+)\s*岁'
        ]

        for pattern in age_patterns:
            ages = re.findall(pattern, period_lower)
            if ages:
                try:
                    age = int(ages[0])
                    if 0 <= age <= 120:  # 合理的年龄范围
                        period_info['age'] = age
                        period_info['type'] = '至特定年龄'
                        break
                except (ValueError, IndexError):
                    continue

        # 提取年限
        year_patterns = [
            r'(\d+)\s*年',
            r'期限[：:]\s*(\d+)年',
            r'保险期间\s*(\d+)\s*年',
            r'(\d+)年保险期间'
        ]

        for pattern in year_patterns:
            years = re.findall(pattern, period_lower)
            if years:
                try:
                    years_val = int(years[0])
                    if 1 <= years_val <= 100:  # 合理的年限范围
                        period_info['years'] = years_val
                        if period_info['type'] == '未知':
                            period_info['type'] = '固定年限'
                        break
                except (ValueError, IndexError):
                    continue

        # 判断保障类型
        if '终身' in period_lower:
            period_info['type'] = '终身'
            period_info['age'] = 100  # 终身通常按100岁计算
        elif '至被保险人' in period_lower or '至' in period_lower:
            if period_info['type'] == '未知':
                period_info['type'] = '至特定年龄'
        elif '年' in period_lower and period_info['type'] == '未知':
            period_info['type'] = '固定年限'

        return period_info

    def extract_risk_level(self, product_name: str, features: str) -> str:
        """提取产品风险等级"""
        name_str = str(product_name).lower()
        features_str = str(features).lower() if not pd.isna(features) else ''

        # 根据产品类型判断风险
        if '万能型' in name_str or '万能险' in name_str:
            return '中高'  # 万能型产品有一定风险
        elif '分红型' in name_str or '分红险' in name_str:
            return '中'  # 分红型产品中等风险
        elif '投连险' in name_str or '投资连结' in name_str:
            return '高'  # 投连险风险较高
        elif '两全保险' in name_str or '两全险' in name_str:
            return '中低'  # 两全保险相对稳健
        elif '养老年金' in name_str or '年金保险' in name_str:
            # 根据描述进一步判断
            if '保本' in features_str or '保证' in features_str:
                return '低'
            else:
                return '中低'
        elif '终身寿险' in name_str:
            return '低'  # 终身寿险风险较低
        else:
            return '中'  # 默认中等风险

    def extract_product_features(self, features_str: str) -> List[str]:
        """提取产品特色关键词"""
        if pd.isna(features_str) or features_str == '--' or features_str == '':
            return []

        features = str(features_str)
        feature_keywords = []

        # 常见养老金产品特色关键词
        keywords = [
            '养老', '退休', '年金', '生存金', '养老金', '祝寿金',
            '分红', '红利', '收益', '增值', '保本', '保证',
            '灵活', '多种选择', '领取灵活', '缴费灵活',
            '保障', '身故', '全残', '意外', '医疗保障',
            '长期', '短期', '终身', '定期',
            '团体', '企业', '员工福利',
            '累积生息', '复利', '利息'
        ]

        for keyword in keywords:
            if keyword in features:
                feature_keywords.append(keyword)

        return feature_keywords[:10]  # 返回前10个关键词

    def process_data(self):
        """处理数据，提取关键信息"""
        print("开始处理数据...")

        if self.df is None:
            print("错误: 数据未加载")
            return None

        processed_data = []

        for idx, row in self.df.iterrows():
            try:
                # 提取年龄范围
                min_age, max_age = self.extract_age_range(row.get('适合年龄(BXLC)', ''))

                # 提取保险类型
                insurance_type = self.extract_insurance_type(row.get('证券名称', ''))

                # 提取保费信息
                premium_info = self.extract_premium_info(row.get('保费说明(BXLC)', ''))

                # 提取保障期限
                coverage_info = self.extract_coverage_period(row.get('保障期限(BXLC)', ''))

                # 提取产品特色
                features_text = row.get('产品特色(BXLC)', '')
                feature_keywords = self.extract_product_features(features_text)

                # 提取风险等级
                risk_level = self.extract_risk_level(
                    row.get('证券名称', ''),
                    features_text
                )

                # 构建处理后的记录
                processed_record = {
                    'product_id': row.get('证券代码', f'ID_{idx}'),
                    'product_name': row.get('证券名称', '未知产品'),
                    'insurance_company': row.get('保险公司全称(BXLC)', '未知公司'),
                    'min_age': min_age,
                    'max_age': max_age,
                    'age_range_str': f"{min_age if min_age is not None else '不限'}-{max_age if max_age is not None else '不限'}岁",
                    'insurance_type': insurance_type,
                    'payment_type': premium_info['payment_type'],
                    'payment_periods': premium_info['periods'],
                    'payment_periods_str': '、'.join([str(p) for p in premium_info['periods']]) if premium_info[
                        'periods'] else '多种可选',
                    'min_premium': premium_info['min_amount'],
                    'min_premium_str': f"{premium_info['min_amount']:,}元",
                    'coverage_type': coverage_info['type'],
                    'coverage_age': coverage_info['age'],
                    'coverage_years': coverage_info['years'],
                    'coverage_str': self._format_coverage_str(coverage_info),
                    'sales_channel': row.get('销售渠道(BXLC)', '未知'),
                    'sales_scope': row.get('销售范围(BXLC)', '未知'),
                    'risk_level': risk_level,
                    'feature_keywords': feature_keywords,
                    'features': features_text[:200] + '...' if len(str(features_text)) > 200 else str(features_text),
                    'original_age_desc': str(row.get('适合年龄(BXLC)', '')),
                    'original_premium_desc': str(row.get('保费说明(BXLC)', '')),
                    'original_coverage_desc': str(row.get('保障期限(BXLC)', ''))
                }

                processed_data.append(processed_record)

            except Exception as e:
                print(f"处理第 {idx} 行数据时出错: {e}")
                continue

        self.processed_df = pd.DataFrame(processed_data)

        # 建立索引
        self._build_indexes()

        print(f"数据处理完成，有效记录: {len(self.processed_df)} 条")
        return self.processed_df

    def _format_coverage_str(self, coverage_info: Dict) -> str:
        """格式化保障期限字符串"""
        if coverage_info['type'] == '终身':
            return '终身保障'
        elif coverage_info['type'] == '至特定年龄' and coverage_info['age']:
            return f"保障至{coverage_info['age']}周岁"
        elif coverage_info['type'] == '固定年限' and coverage_info['years']:
            return f"保障{coverage_info['years']}年"
        else:
            return coverage_info.get('description', '未知')[:50]

    def _build_indexes(self):
        """建立产品索引"""
        if self.processed_df is None:
            return

        # 按产品ID索引
        self.products_by_id = {}
        for _, row in self.processed_df.iterrows():
            self.products_by_id[row['product_id']] = row.to_dict()

        # 按保险公司索引
        self.products_by_company = {}
        for _, row in self.processed_df.iterrows():
            company = row['insurance_company']
            if company not in self.products_by_company:
                self.products_by_company[company] = []
            self.products_by_company[company].append(row.to_dict())

        print(f"已建立索引: {len(self.products_by_id)} 个产品, {len(self.products_by_company)} 家保险公司")

    def get_product_details(self, product_id: str) -> Optional[Dict]:
        """获取产品详细信息"""
        if product_id in self.products_by_id:
            return self.products_by_id[product_id]
        return None

    def get_products_by_company(self, company_name: str) -> List[Dict]:
        """获取指定保险公司的产品"""
        if company_name in self.products_by_company:
            return self.products_by_company[company_name]
        return []

    def get_all_companies(self) -> List[str]:
        """获取所有保险公司列表"""
        if self.processed_df is not None:
            return sorted(self.processed_df['insurance_company'].unique().tolist())
        return []

    def get_products_by_age(self, age: int) -> pd.DataFrame:
        """获取适合指定年龄的产品"""
        if self.processed_df is None:
            return pd.DataFrame()

        # 筛选适合该年龄的产品
        mask = (
                       (self.processed_df['min_age'].isna()) | (self.processed_df['min_age'] <= age)
               ) & (
                       (self.processed_df['max_age'].isna()) | (self.processed_df['max_age'] >= age)
               )

        return self.processed_df[mask].copy()

    def get_products_by_risk(self, risk_level: str) -> pd.DataFrame:
        """获取指定风险等级的产品"""
        if self.processed_df is None:
            return pd.DataFrame()

        return self.processed_df[self.processed_df['risk_level'] == risk_level].copy()

    def save_processed_data(self, filepath: str = 'processed_products.json'):
        """保存处理后的数据到JSON文件"""
        if self.processed_df is not None:
            self.processed_df.to_json(filepath, orient='records', force_ascii=False)
            print(f"数据已保存到: {filepath}")
            return True
        return False

    def load_processed_data(self, filepath: str = 'processed_products.json'):
        """从JSON文件加载处理后的数据"""
        if os.path.exists(filepath):
            try:
                self.processed_df = pd.read_json(filepath, orient='records')
                self._build_indexes()
                print(f"从 {filepath} 加载处理后的数据成功")
                return True
            except Exception as e:
                print(f"加载处理后的数据失败: {e}")
                return False
        return False

    def get_summary_statistics(self) -> Dict:
        """获取数据统计摘要"""
        if self.processed_df is None:
            return {}

        summary = {
            'total_products': len(self.processed_df),
            'total_companies': len(self.processed_df['insurance_company'].unique()),
            'age_stats': {
                'has_min_age': self.processed_df['min_age'].notna().sum(),
                'has_max_age': self.processed_df['max_age'].notna().sum(),
                'avg_min_age': self.processed_df['min_age'].mean() if self.processed_df[
                    'min_age'].notna().any() else None,
                'avg_max_age': self.processed_df['max_age'].mean() if self.processed_df[
                    'max_age'].notna().any() else None,
            },
            'risk_distribution': self.processed_df['risk_level'].value_counts().to_dict(),
            'type_distribution': self.processed_df['insurance_type'].value_counts().to_dict(),
            'payment_type_distribution': self.processed_df['payment_type'].value_counts().to_dict(),
            'top_companies': self.processed_df['insurance_company'].value_counts().head(10).to_dict()
        }

        return summary

    def search_products(self, keyword: str) -> pd.DataFrame:
        """搜索产品"""
        if self.processed_df is None:
            return pd.DataFrame()

        keyword = keyword.lower()
        mask = (
                self.processed_df['product_name'].str.lower().str.contains(keyword, na=False) |
                self.processed_df['insurance_company'].str.lower().str.contains(keyword, na=False) |
                self.processed_df['insurance_type'].str.lower().str.contains(keyword, na=False) |
                self.processed_df['features'].str.lower().str.contains(keyword, na=False)
        )

        return self.processed_df[mask].copy()


# 测试函数
def test_data_processor():
    """测试数据处理模块"""
    print("测试数据处理模块...")

    # 创建分析器
    analyzer = PensionProductAnalyzer()

    # 创建演示数据
    analyzer.create_demo_data()

    # 处理数据
    processed_data = analyzer.process_data()

    if processed_data is not None:
        print(f"\n处理后的数据形状: {processed_data.shape}")
        print(f"\n数据列: {list(processed_data.columns)}")
        print(f"\n前3条记录:")
        print(processed_data[['product_name', 'insurance_company', 'age_range_str', 'risk_level']].head(3))

        # 测试获取产品详情
        if not processed_data.empty:
            product_id = processed_data.iloc[0]['product_id']
            details = analyzer.get_product_details(product_id)
            print(f"\n产品详情示例:")
            print(f"产品名称: {details['product_name']}")
            print(f"保险公司: {details['insurance_company']}")
            print(f"适合年龄: {details['age_range_str']}")
            print(f"风险等级: {details['risk_level']}")

        # 获取统计摘要
        summary = analyzer.get_summary_statistics()
        print(f"\n数据统计摘要:")
        print(f"总产品数: {summary.get('total_products', 0)}")
        print(f"保险公司数: {summary.get('total_companies', 0)}")
        print(f"风险分布: {summary.get('risk_distribution', {})}")

        # 测试搜索功能
        search_results = analyzer.search_products('养老')
        print(f"\n搜索'养老'的结果: {len(search_results)} 条记录")

    print("\n数据处理模块测试完成!")


if __name__ == "__main__":
    test_data_processor()