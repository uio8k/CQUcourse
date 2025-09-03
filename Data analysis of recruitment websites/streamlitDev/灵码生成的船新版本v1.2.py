# streamlit_app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体和图表清晰度
plt.rcParams['figure.dpi'] = 200
plt.rcParams['savefig.dpi'] = 200
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Songti SC', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 预编译正则表达式
SALARY_REGEX_K = re.compile(r'(\d+\.?\d*)-?(\d+\.?\d*)K')
SALARY_REGEX_DAY = re.compile(r'(\d+)-(\d+)元/天')
SALARY_REGEX_HOUR = re.compile(r'(\d+)-(\d+)元/时')
SALARY_REGEX_SINGLE_DAY = re.compile(r'(\d+)元/天')
SALARY_REGEX_SINGLE_HOUR = re.compile(r'(\d+)元/时')
SALARY_REGEX_PLAIN = re.compile(r'(\d+\.?\d*)-?(\d+\.?\d*)')


@st.cache_data
def load_data():
    """加载并预处理数据"""
    try:
        df = pd.read_csv(r'E:\计算机技术学习\2025年8月大二实训\招聘网站数据分析\数据集\data3.4.csv')

        # 处理空值
        df['工作经验'] = df['工作经验'].fillna('经验不限')
        df['学历'] = df['学历'].fillna('学历不限')
        df['公司规模'] = df['公司规模'].fillna('未公布')
        df['福利列表'] = df['福利列表'].fillna('[]')

        return df
    except FileNotFoundError:
        st.error("错误：未找到 data3.4.csv 文件，请确认文件是否存在")
        return None
    except Exception as e:
        st.error(f"读取数据时发生错误：{str(e)}")
        return None


def process_salary(salary):
    """处理薪资数据"""
    if not isinstance(salary, str):
        return None

    salary = salary.strip()

    if '元/天' in salary:
        match = SALARY_REGEX_DAY.search(salary)
        if match:
            low, high = int(match.group(1)), int(match.group(2))
            return (low + high) / 2 * 30
        else:
            match = SALARY_REGEX_SINGLE_DAY.search(salary)
            if match:
                return int(match.group(1)) * 30

    elif '元/时' in salary:
        match = SALARY_REGEX_HOUR.search(salary)
        if match:
            low, high = int(match.group(1)), int(match.group(2))
            return (low + high) / 2 * 8 * 22
        else:
            match = SALARY_REGEX_SINGLE_HOUR.search(salary)
            if match:
                return int(match.group(1)) * 8 * 22

    elif '万/年' in salary:
        match = SALARY_REGEX_HOUR.search(salary)
        if match:
            low, high = int(match.group(1)), int(match.group(2))
            return (low + high) / 2 * 8 * 22 * 12
        else:
            match = SALARY_REGEX_SINGLE_HOUR.search(salary)
            if match:
                return int(match.group(1)) * 8 * 22 * 12

    else:
        base_salary = salary.split('·')[0]
        match = SALARY_REGEX_K.search(base_salary)
        if match:
            low = float(match.group(1))
            high = float(match.group(2)) if match.group(2) else low
            return (low + high) / 2 * 1000

        match = SALARY_REGEX_PLAIN.search(base_salary)
        if match:
            low = float(match.group(1))
            high = float(match.group(2)) if match.group(2) else low
            return (low + high) / 2

    return None


def extract_skills_and_tags(df):
    """提取技能和标签数据（参数改为筛选后的df）"""
    all_skills = []
    all_tags = []

    for _, row in df.iterrows():
        # 处理技能要求
        skills_str = str(row['技能要求'])
        if skills_str != '[]' and skills_str != 'nan':
            skills = skills_str.replace('[', '').replace(']', '').replace("'", "").split(', ')
            all_skills.extend([skill.strip() for skill in skills if skill.strip()])

        # 处理工作标签
        tags_str = str(row['工作标签'])
        if tags_str != '[]' and tags_str != 'nan':
            tags = tags_str.replace('[', '').replace(']', '').replace("'", "").split(', ')
            all_tags.extend([tag.strip() for tag in tags if tag.strip()])

    return all_skills, all_tags


def categorize_industry(row):
    """分类行业"""
    position = str(row['职位']).lower()
    skills = str(row['技能要求']).lower()
    tags = str(row['工作标签']).lower()

    if any(keyword in position + skills + tags for keyword in
           ['ai', '机器学习', '深度学习', 'nlp', '计算机视觉', 'llm', 'aigc']):
        return '人工智能'
    elif any(keyword in position + skills + tags for keyword in
             ['python', 'java', 'c++', '前端', '后端', '全栈', '开发', '软件']):
        return '软件开发'
    elif any(keyword in position + skills + tags for keyword in ['数据', '大数据', '数据分析', '数据挖掘']):
        return '数据分析'
    elif any(keyword in position + skills + tags for keyword in ['嵌入式', '硬件', '单片机', '物联网', '芯片', 'ic']):
        return '硬件/嵌入式'
    elif any(keyword in position + skills + tags for keyword in ['销售', '市场', '商务', 'bd']):
        return '销售/市场'
    elif any(keyword in position + skills + tags for keyword in ['教育', '培训', '教师']):
        return '教育培训'
    elif any(keyword in position + skills + tags for keyword in ['客服']):
        return '客服'
    elif any(keyword in position + skills + tags for keyword in ['运营']):
        return '运营'
    else:
        return '其他'


def escape_special_chars(text):
    """转义正则表达式特殊字符"""
    special_chars = r'\.^$*+?{}[]|()'
    escaped_text = ''
    for char in text:
        if char in special_chars:
            escaped_text += '\\' + char
        else:
            escaped_text += char
    return escaped_text


def main():
    # 修改为（选择一个你喜欢的图标）：
    st.set_page_config(page_title="招聘数据分析平台", layout="wide", page_icon=r"C:\Users\Chou HuaiTao\Pictures\Saved Pictures\白枪呆骑马cos.png")

    # 页面标题和介绍
    st.title(" 招聘数据分析平台")
    st.markdown("""
    欢迎使用招聘数据分析平台！本平台基于真实的招聘数据，为您提供：
    - 薪资水平分析
    - 技能需求洞察
    - 行业发展趋势
    - 城市就业机会
    """)

    # 加载数据
    df = load_data()
    if df is None:
        return

    # 处理薪资数据（仅初始化行业，技能提取移到筛选后）
    with st.spinner('正在处理数据...'):
        df['平均薪资'] = df['期待薪资'].apply(process_salary)
        df['行业'] = df.apply(categorize_industry, axis=1)
        # 【变更1】注释原始全量技能提取，改为筛选后提取
        # all_skills, all_tags = extract_skills_and_tags(df)

    # 侧边栏筛选器
    st.sidebar.header("🔍 筛选条件")

    # 城市筛选
    cities = ["全国"] + sorted(df['城市'].dropna().unique().tolist())
    selected_city = st.sidebar.selectbox("选择城市", cities, index=0)

    # 行业筛选
    industries = ["全部"] + sorted(df['行业'].dropna().unique().tolist())
    selected_industry = st.sidebar.selectbox("选择行业", industries, index=0)

    # 学历筛选
    educations = ["全部"] + sorted(df['学历'].dropna().unique().tolist())
    selected_education = st.sidebar.selectbox("选择学历要求", educations, index=0)

    # 工作经验筛选
    experiences = ["全部"] + sorted(df['工作经验'].dropna().unique().tolist())
    selected_experience = st.sidebar.selectbox("选择工作经验", experiences, index=0)
    # 用户自定义岗位搜索
    st.sidebar.markdown("---")
    st.sidebar.header("🔎 岗位搜索")

    # 搜索输入框
    search_query = st.sidebar.text_input("输入职位关键词", placeholder="例如：Python、Java、数据分析师...")

    # 根据筛选条件过滤数据
    df_filtered = df.copy()

    if selected_city != "全国":
        df_filtered = df_filtered[df_filtered['城市'] == selected_city]

    if selected_industry != "全部":
        df_filtered = df_filtered[df_filtered['行业'] == selected_industry]

    if selected_education != "全部":
        df_filtered = df_filtered[df_filtered['学历'] == selected_education]

    if selected_experience != "全部":
        df_filtered = df_filtered[df_filtered['工作经验'] == selected_experience]

    # 如果用户输入了搜索关键词，则进行搜索
    if search_query:
        # 使用关键词搜索职位名称
        search_mask = df_filtered['职位'].str.contains(search_query, case=False, na=False)
        df_filtered = df_filtered[search_mask]

    # 【变更2】基于筛选后的df提取技能和标签（关键：确保技能与筛选结果联动）
    all_skills, all_tags = extract_skills_and_tags(df_filtered)

    # 数据概览
    st.header("📊 数据概览")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总职位数", len(df_filtered))
    with col2:
        valid_salary_count = df_filtered['平均薪资'].notna().sum()
        st.metric("有效薪资数据", valid_salary_count)
    with col3:
        avg_salary = df_filtered['平均薪资'].mean()
        st.metric("平均薪资", f"{avg_salary:.0f}元" if not np.isnan(avg_salary) else "N/A")
    with col4:
        company_count = df_filtered['公司'].nunique()
        st.metric("涉及公司", company_count)

    # 创建标签页
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 薪资分析", "💻 技能洞察", "🏢 行业趋势", "🏙️ 城市机会", "📋 数据浏览"])

    # 在薪资分析部分（tab1）中添加新的分析内容
    with tab1:
        st.subheader("薪资分析")

        col1, col2 = st.columns(2)

        with col1:
            # 薪资分布直方图
            df_salary = df_filtered.dropna(subset=['平均薪资'])
            if not df_salary.empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.hist(df_salary['平均薪资'], bins=30, edgecolor='black', alpha=0.7, color='skyblue')
                ax.set_xlabel('薪资（元）')
                ax.set_ylabel('职位数量')
                ax.set_title('薪资分布情况')
                st.pyplot(fig)
            else:
                st.info("暂无有效薪资数据")

        with col2:
            # 按学历的平均薪资
            if not df_filtered.empty:
                salary_by_education = df_filtered.groupby('学历')['平均薪资'].mean().dropna()
                if not salary_by_education.empty:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    bars = ax.bar(salary_by_education.index, salary_by_education.values, color='lightcoral')
                    ax.set_xlabel('学历要求')
                    ax.set_ylabel('平均薪资（元）')
                    ax.set_title('不同学历的平均薪资')
                    plt.xticks(rotation=45)

                    # 添加数值标签
                    for bar in bars:
                        height = bar.get_height()
                        ax.annotate(f'{height:.0f}',
                                    xy=(bar.get_x() + bar.get_width() / 2, height),
                                    xytext=(0, 3),
                                    textcoords="offset points",
                                    ha='center', va='bottom')

                    st.pyplot(fig)
                else:
                    st.info("暂无学历相关薪资数据")
            else:
                st.info("暂无数据")

        # 新增：薪资与学历关系深入分析
        st.markdown("---")
        st.subheader("薪资与学历关系深入分析")

        # 创建两列布局
        col3, col4 = st.columns(2)

        with col3:
            # 学历分布饼图
            education_counts = df_filtered['学历'].value_counts()
            if not education_counts.empty:
                fig, ax = plt.subplots(figsize=(8, 8))
                wedges, texts, autotexts = ax.pie(education_counts.values,
                                                  labels=education_counts.index,
                                                  autopct='%1.1f%%',
                                                  startangle=90)
                ax.set_title('学历要求分布')
                st.pyplot(fig)
            else:
                st.info("暂无学历分布数据")

        with col4:
            # 学历与薪资的详细统计
            if not df_filtered.empty:
                education_stats = df_filtered.groupby('学历')['平均薪资'].agg(['count', 'mean', 'median']).round(0)
                education_stats.columns = ['职位数量', '平均薪资', '薪资中位数']
                education_stats = education_stats.dropna()
                education_stats = education_stats.sort_values('平均薪资', ascending=False)  # 按平均薪资从高到低排序

                if not education_stats.empty:
                    # 格式化显示
                    education_stats_display = education_stats.copy()
                    education_stats_display['平均薪资'] = education_stats_display['平均薪资'].apply(
                        lambda x: f"{x:.0f}元")
                    education_stats_display['薪资中位数'] = education_stats_display['薪资中位数'].apply(
                        lambda x: f"{x:.0f}元")

                    st.write("各学历薪资统计:")
                    st.dataframe(education_stats_display)
                else:
                    st.info("暂无学历薪资统计数据")
            else:
                st.info("暂无数据")

        # 新增：学历薪资对比条形图
        st.subheader("学历薪资对比分析")

        if not df_filtered.empty:
            # 准备数据
            education_salary_data = df_filtered.groupby('学历').agg({
                '平均薪资': ['count', 'mean', 'median']
            }).round(0)

            # 展平列名
            education_salary_data.columns = ['职位数量', '平均薪资', '薪资中位数']
            education_salary_data = education_salary_data.dropna()

            if not education_salary_data.empty:
                # 按平均薪资排序
                education_salary_data = education_salary_data.sort_values('平均薪资', ascending=False)

                # 创建对比图表
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

                # 左图：平均薪资对比
                bars1 = ax1.bar(education_salary_data.index, education_salary_data['平均薪资'],
                                color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD'])
                ax1.set_xlabel('学历要求')
                ax1.set_ylabel('平均薪资（元）')
                ax1.set_title('不同学历的平均薪资对比')
                ax1.set_xticklabels(education_salary_data.index, rotation=45)

                # 添加数值标签
                for bar in bars1:
                    height = bar.get_height()
                    ax1.annotate(f'{int(height)}',
                                 xy=(bar.get_x() + bar.get_width() / 2, height),
                                 xytext=(0, 3),
                                 textcoords="offset points",
                                 ha='center', va='bottom')

                # 右图：职位数量对比
                bars2 = ax2.bar(education_salary_data.index, education_salary_data['职位数量'],
                                color=['#A8E6CF', '#DCEDC1', '#FFD3B6', '#FFAAA5', '#FF8B94'])
                ax2.set_xlabel('学历要求')
                ax2.set_ylabel('职位数量')
                ax2.set_title('不同学历的职位数量分布')
                ax2.set_xticklabels(education_salary_data.index, rotation=45)

                # 添加数值标签
                for bar in bars2:
                    height = bar.get_height()
                    ax2.annotate(f'{int(height)}',
                                 xy=(bar.get_x() + bar.get_width() / 2, height),
                                 xytext=(0, 3),
                                 textcoords="offset points",
                                 ha='center', va='bottom')

                plt.tight_layout()
                st.pyplot(fig)

                # 添加分析结论
                st.markdown("### 💡 分析结论")
                highest_edu = education_salary_data.index[0]
                lowest_edu = education_salary_data.index[-1]
                salary_diff = education_salary_data.iloc[0]['平均薪资'] - education_salary_data.iloc[-1]['平均薪资']

                st.markdown(f"""
                - **最高薪资学历**: {highest_edu} (平均 {education_salary_data.iloc[0]['平均薪资']:.0f} 元)
                - **最低薪资学历**: {lowest_edu} (平均 {education_salary_data.iloc[-1]['平均薪资']:.0f} 元)
                - **薪资差距**: {salary_diff:.0f} 元
                - **职位最多学历**: {education_salary_data['职位数量'].idxmax()} ({education_salary_data['职位数量'].max():.0f} 个职位)
                """)
            else:
                st.info("暂无足够的学历薪资数据进行分析")
        else:
            st.info("暂无数据进行学历薪资分析")

    with tab2:
        st.subheader("技能需求洞察")

        # 【变更3】基于筛选后的all_skills统计（与筛选结果联动）
        if all_skills:
            # 热门技能统计（仅筛选后的数据）
            skill_counts = Counter(all_skills)
            top_skills = dict(skill_counts.most_common(15))

            col1, col2 = st.columns(2)

            with col1:
                # 热门技能柱状图
                fig, ax = plt.subplots(figsize=(10, 8))
                skills = list(top_skills.keys())
                counts = list(top_skills.values())
                bars = ax.barh(skills, counts, color='lightgreen')
                ax.set_xlabel('出现频次')
                ax.set_ylabel('技能')
                ax.set_title('热门技能TOP15')

                # 添加数值标签
                for i, (bar, count) in enumerate(zip(bars, counts)):
                    ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                            str(count), ha='left', va='center')

                st.pyplot(fig)

            with col2:
                st.write("### 热门技能统计")
                st.dataframe(pd.DataFrame({
                    '技能': list(top_skills.keys()),
                    '需求频次': list(top_skills.values())
                }).reset_index(drop=True))

                # 高价值技能分析（基于筛选后的df_filtered）
                st.write("### 高价值技能分析")
                high_value_skills = {}
                for skill in list(top_skills.keys())[:10]:
                    # 转义特殊字符以避免正则表达式错误
                    escaped_skill = escape_special_chars(skill)
                    try:
                        # 【变更4】筛选条件改为df_filtered（确保与搜索结果一致）
                        mask = df_filtered['技能要求'].str.contains(escaped_skill, na=False, regex=False)
                        if mask.sum() > 0:
                            avg_salary = df_filtered[mask]['平均薪资'].mean()
                            if not np.isnan(avg_salary):
                                high_value_skills[skill] = {
                                    '需求量': mask.sum(),
                                    '平均薪资': int(avg_salary)
                                }
                    except Exception as e:
                        # 如果仍然出错，跳过该技能
                        continue

                if high_value_skills:
                    st.dataframe(pd.DataFrame(high_value_skills).T)
                else:
                    st.info("暂无高价值技能数据")
        else:
            st.info("暂无技能数据")

    with tab3:
        st.subheader("行业发展趋势")

        # 行业职位数量和平均薪资
        industry_stats = df_filtered.groupby('行业').agg({
            '平均薪资': 'mean',
            '职位': 'count'
        }).rename(columns={'职位': '职位数量'})

        industry_stats = industry_stats.dropna()
        industry_stats['平均薪资'] = industry_stats['平均薪资'].apply(lambda x: int(x) if not np.isnan(x) else 0)
        industry_stats = industry_stats.sort_values('职位数量', ascending=False)

        if not industry_stats.empty:
            col1, col2 = st.columns(2)

            with col1:
                # 行业职位数量饼图
                fig, ax = plt.subplots(figsize=(10, 8))
                wedges, texts, autotexts = ax.pie(industry_stats['职位数量'],
                                                  labels=industry_stats.index,
                                                  autopct='%1.1f%%',
                                                  startangle=90)
                ax.set_title('各行业职位分布')
                st.pyplot(fig)

            with col2:
                st.write("### 行业数据分析")
                st.dataframe(industry_stats)

                # 行业薪资对比
                fig, ax = plt.subplots(figsize=(10, 6))
                bars = ax.bar(industry_stats.index, industry_stats['平均薪资'], color='orange')
                ax.set_xlabel('行业')
                ax.set_ylabel('平均薪资（元）')
                ax.set_title('各行业平均薪资对比')
                plt.xticks(rotation=45)

                # 添加数值标签
                for bar in bars:
                    height = bar.get_height()
                    ax.annotate(f'{int(height)}',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom')

                st.pyplot(fig)
        else:
            st.info("暂无行业数据")

    with tab4:
        st.subheader("城市就业机会")

        # 各城市职位数量
        city_counts = df_filtered['城市'].value_counts().head(10)

        if not city_counts.empty:
            col1, col2 = st.columns(2)

            with col1:
                # 城市职位数量柱状图
                fig, ax = plt.subplots(figsize=(10, 6))
                bars = ax.bar(city_counts.index, city_counts.values, color='lightblue')
                ax.set_xlabel('城市')
                ax.set_ylabel('职位数量')
                ax.set_title('热门城市职位数量TOP10')
                plt.xticks(rotation=45)

                # 添加数值标签
                for bar in bars:
                    height = bar.get_height()
                    ax.annotate(f'{int(height)}',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom')

                st.pyplot(fig)

            with col2:
                # 城市平均薪资对比
                city_salary = df_filtered.groupby('城市')['平均薪资'].mean().dropna().sort_values(ascending=False).head(
                    10)
                if not city_salary.empty:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    bars = ax.bar(city_salary.index, city_salary.values, color='gold')
                    ax.set_xlabel('城市')
                    ax.set_ylabel('平均薪资（元）')
                    ax.set_title('热门城市平均薪资TOP10')
                    plt.xticks(rotation=45)

                    # 添加数值标签
                    for bar in bars:
                        height = bar.get_height()
                        ax.annotate(f'{int(height)}',
                                    xy=(bar.get_x() + bar.get_width() / 2, height),
                                    xytext=(0, 3),
                                    textcoords="offset points",
                                    ha='center', va='bottom')

                    st.pyplot(fig)
                else:
                    st.info("暂无城市薪资数据")
        else:
            st.info("暂无城市数据")

    with tab5:
        st.subheader("原始数据浏览")

        # 显示筛选后的数据表格
        display_columns = ['职位', '期待薪资', '工作经验', '学历', '城市', '公司', '行业']
        df_display = df_filtered[display_columns].copy()

        # 格式化显示
        if '平均薪资' in df_filtered.columns:
            df_display['平均薪资'] = df_filtered['平均薪资'].apply(
                lambda x: f"{x:.0f}元" if pd.notna(x) else "N/A"
            )

        st.dataframe(df_display, use_container_width=True)

        # 数据导出功能
        csv = df_filtered.to_csv(index=False)
        st.download_button(
            label="📥 下载筛选后的数据",
            data=csv,
            file_name="filtered_job_data.csv",
            mime="text/csv"
        )

    # 页面底部信息
    st.markdown("---")
    st.markdown("""
    *数据更新时间：2025.9.3*
    """)


if __name__ == "__main__":
    main()

# streamlit run E:\计算机技术学习\2025年8月大二实训\招聘网站数据分析\网页版本\灵码生成的船新版本v1.2.py