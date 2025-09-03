import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import re
import seaborn as sns
import jieba
from wordcloud import WordCloud
import os

# 设置图片清晰度和中文字体（解决中文乱码问题）
plt.rcParams['figure.dpi'] = 300
# 设置多种中文字体备选，确保在不同系统上都能正常显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Songti SC', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号 '-' 显示为方块的问题
# 设置图片清晰度和中文字体（解决中文乱码问题）
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300  # 保存图片时的DPI
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['figure.edgecolor'] = 'none'

# 提高字体渲染质量
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42
plt.rcParams['svg.fonttype'] = 'none'

# 设置多种中文字体备选，确保在不同系统上都能正常显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Songti SC', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号 '-' 显示为方块的问题

# 预编译正则表达式以提升性能
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
        df = pd.read_csv('data3.2.csv')

        # 处理空值和空列表
        df['工作经验'] = df['工作经验'].fillna('经验不限')
        df['学历'] = df['学历'].fillna('学历不限')
        df['公司规模'] = df['公司规模'].fillna('未公布')
        df['福利列表'] = df['福利列表'].fillna('[]')  # 填充为空列表而不是字符串'未公布'

        # 处理空列表的情况
        df.loc[df['福利列表'] == '[]', '福利列表'] = '未公布'

        return df
    except FileNotFoundError:
        st.error("错误：未找到 data3.2.csv 文件，请确认文件是否存在")
        return None
    except Exception as e:
        st.error(f"读取数据时发生错误：{str(e)}")
        return None

def process_salary(salary):
    """
    处理薪资数据，将不同格式的薪资转换为数值类型（单位：元/月）
    """
    if not isinstance(salary, str):
        return None

    # 移除空格并统一处理
    salary = salary.strip()

    # 处理日薪格式 (如: 100-5000元/天)
    if '元/天' in salary:
        match = SALARY_REGEX_DAY.search(salary)
        if match:
            low, high = int(match.group(1)), int(match.group(2))
            return (low + high) / 2 * 30  # 转换为月薪（按30天计算）
        else:
            match = SALARY_REGEX_SINGLE_DAY.search(salary)
            if match:
                return int(match.group(1)) * 30

    # 处理时薪格式 (如: 20-25元/时)
    elif '元/时' in salary:
        match = SALARY_REGEX_HOUR.search(salary)
        if match:
            low, high = int(match.group(1)), int(match.group(2))
            return (low + high) / 2 * 8 * 22  # 转换为月薪（按每天8小时，每月22个工作日）
        else:
            match = SALARY_REGEX_SINGLE_HOUR.search(salary)
            if match:
                return int(match.group(1)) * 8 * 22

    # 处理月薪格式 (如: 15-25K, 7-10K·13薪)
    else:
        # 提取基本薪资部分（去除·13薪等附加信息）
        base_salary = salary.split('·')[0]

        # 匹配K格式的薪资 (如: 15-25K)
        match = SALARY_REGEX_K.search(base_salary)
        if match:
            low = float(match.group(1))
            high = float(match.group(2)) if match.group(2) else low
            return (low + high) / 2 * 1000  # K转换为具体数值

        # 匹配纯数字格式
        match = SALARY_REGEX_PLAIN.search(base_salary)
        if match:
            low = float(match.group(1))
            high = float(match.group(2)) if match.group(2) else low
            return (low + high) / 2

    return None


def get_salary_by_education_data(df, city_name="全国"):
    """获取不同学历的平均薪资数据用于表格展示"""
    try:
        # 检查必要列是否存在
        required_columns = ['平均薪资', '学历']
        if not all(col in df.columns for col in required_columns):
            st.warning("警告：数据缺少必要的列（'平均薪资' 或 '学历'）")
            return None

        # 如果指定了城市且不是"全国"，则进行筛选
        if city_name != "全国":
            if '城市' not in df.columns:
                st.warning("警告：数据缺少城市列，无法按城市筛选")
                return None
            df = df[df['城市'] == city_name]

        # 过滤掉无效薪资数据
        df_valid = df.dropna(subset=['平均薪资'])

        if df_valid.empty:
            st.warning("警告：没有有效的薪资数据用于展示")
            return None

        # 按学历分组计算平均薪资，并获取对应的公司和职位示例
        salary_by_education = df_valid.groupby('学历')['平均薪资'].agg(['mean', 'count']).reset_index()

        # 正确重命名列
        salary_by_education.columns = ['学历', '平均薪资(元)', '岗位数量']

        # 按平均薪资降序排序
        salary_by_education = salary_by_education.sort_values('平均薪资(元)', ascending=False)

        # 格式化平均薪资列
        salary_by_education['平均薪资(元)'] = salary_by_education['平均薪资(元)'].apply(lambda x: f"{x:.0f}")

        return salary_by_education
    except Exception as e:
        st.error(f"处理数据时发生错误: {str(e)}")
        return None


def plot_job_count_by_company_size(df, city_name="全国"):
    """绘制不同公司规模的岗位数量柱状图"""
    job_count_by_company_size = df['公司规模'].value_counts()

    # 调整为更适合您屏幕的尺寸
    fig, ax = plt.subplots(figsize=(12, 6))  # 从 (25, 6) 调整为 (12, 6)

    # 使用新的matplotlib colormap语法
    colors = cm.get_cmap('plasma')(np.linspace(0, 1, len(job_count_by_company_size)))
    bars = ax.bar(job_count_by_company_size.index, job_count_by_company_size.values, color=colors)

    # 添加数值标签
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{int(height)}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)

    ax.set_xlabel('公司规模')
    ax.set_ylabel('岗位数量')
    ax.set_title(f'{city_name}不同公司规模的岗位数量')
    plt.xticks(rotation=45)
    plt.tight_layout()

    return fig

def plot_salary_by_experience(df, city_name="全国"):
    """绘制不同工作经验的平均薪资柱状图"""
    df_valid = df.dropna(subset=['平均薪资'])

    if df_valid.empty:
        st.warning("警告：没有有效的薪资数据用于展示")
        return None

    salary_by_experience = df_valid.groupby('工作经验')['平均薪资'].mean().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = cm.get_cmap('coolwarm')(np.linspace(0, 1, len(salary_by_experience)))
    bars = ax.bar(salary_by_experience.index, salary_by_experience.values, color=colors)

    # 添加数值标签
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.0f}元',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)

    ax.set_xlabel('工作经验')
    ax.set_ylabel('平均薪资（元）')
    ax.set_title(f'{city_name}不同工作经验的平均薪资')
    plt.xticks(rotation=45)
    plt.tight_layout()

    return fig


def plot_salary_by_city(df, selected_city):
    """绘制不同城市的平均薪资对比（选定城市与其他城市的对比）"""
    df_valid = df.dropna(subset=['平均薪资', '城市'])

    if df_valid.empty:
        st.warning("警告：没有有效的薪资和城市数据用于展示")
        return None

    # 计算各城市平均薪资
    salary_by_city = df_valid.groupby('城市')['平均薪资'].mean().sort_values(ascending=False).head(10)

    # 创建对比数据：选定城市 vs 其他城市平均
    other_cities_avg = df_valid[df_valid['城市'] != selected_city]['平均薪资'].mean()
    selected_city_avg = df_valid[df_valid['城市'] == selected_city]['平均薪资'].mean()

    comparison_data = pd.Series({
        selected_city: selected_city_avg,
        '其他城市平均': other_cities_avg
    })

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['red' if city == selected_city else 'blue' for city in comparison_data.index]
    bars = ax.bar(comparison_data.index, comparison_data.values, color=colors)

    # 添加数值标签
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.0f}元',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)

    ax.set_xlabel('城市')
    ax.set_ylabel('平均薪资（元）')
    ax.set_title(f'{selected_city}与其它城市薪资对比')
    plt.xticks(rotation=45)
    plt.tight_layout()

    return fig


def plot_top_jobs(df, top_n=10, city_name="全国"):
    """绘制热门职位分布图"""
    top_jobs = df['职位'].value_counts().head(top_n)

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = cm.get_cmap('tab20')(np.linspace(0, 1, len(top_jobs)))
    bars = ax.barh(top_jobs.index, top_jobs.values, color=colors)

    # 添加数值标签
    for i, (bar, value) in enumerate(zip(bars, top_jobs.values)):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                str(value), ha='left', va='center', fontsize=9)

    ax.set_xlabel('职位数量')
    ax.set_ylabel('职位名称')
    ax.set_title(f'{city_name}热门职位TOP{top_n}')
    plt.tight_layout()

    return fig


def plot_education_experience_bar(df, city_name="全国"):
    """绘制学历与工作经验交叉分析柱状图"""
    df_valid = df.dropna(subset=['学历', '工作经验'])

    if df_valid.empty:
        st.warning("警告：没有有效的学历和工作经验数据用于展示")
        return None

    # 创建交叉表
    cross_table = pd.crosstab(df_valid['学历'], df_valid['工作经验'])

    # 将交叉表转换为长格式数据，便于绘制柱状图
    bar_data = cross_table.reset_index().melt(id_vars=['学历'], var_name='工作经验', value_name='数量')

    fig, ax = plt.subplots(figsize=(12, 8))

    # 使用seaborn的barplot
    sns.barplot(data=bar_data, x='学历', y='数量', hue='工作经验', ax=ax)

    ax.set_xlabel('学历')
    ax.set_ylabel('岗位数量')
    ax.set_title(f'{city_name}学历与工作经验分布')
    plt.xticks(rotation=45)
    plt.legend(title='工作经验', loc='upper right')
    plt.tight_layout()

    return fig


def plot_salary_distribution(df, city_name="全国"):
    """绘制薪资分布直方图"""
    df_valid = df.dropna(subset=['平均薪资'])

    if df_valid.empty:
        st.warning("警告：没有有效的薪资数据用于展示")
        return None

    fig, ax = plt.subplots(figsize=(10, 6))
    n, bins, patches = ax.hist(df_valid['平均薪资'], bins=30, edgecolor='black', alpha=0.7)

    # 为柱子添加颜色
    cm_colors = cm.get_cmap('viridis')(np.linspace(0, 1, len(patches)))
    for patch, color in zip(patches, cm_colors):
        patch.set_facecolor(color)

    ax.set_xlabel('薪资（元）')
    ax.set_ylabel('职位数量')
    ax.set_title(f'{city_name}薪资分布情况')
    plt.tight_layout()

    return fig


def plot_skill_distribution(df, city_name="全国"):
    """绘制技能要求分布图"""
    # 合并所有技能要求
    all_skills = ' '.join(df['技能要求'].astype(str))

    # 简单处理技能数据
    skills_list = []
    for skill_str in df['技能要求'].dropna():
        if skill_str != '[]':
            # 移除方括号并分割
            skills = skill_str.replace('[', '').replace(']', '').replace("'", "").split(', ')
            skills_list.extend([skill.strip() for skill in skills if skill.strip()])

    # 统计技能频次
    skill_counts = pd.Series(skills_list).value_counts().head(15)

    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.barh(skill_counts.index, skill_counts.values, color='skyblue')

    # 添加数值标签
    for bar in bars:
        width = bar.get_width()
        ax.text(width, bar.get_y() + bar.get_height() / 2,
                f'{int(width)}',
                ha='left', va='center', fontsize=9)

    ax.set_xlabel('出现频次')
    ax.set_ylabel('技能要求')
    ax.set_title(f'{city_name}热门技能要求TOP15')
    plt.tight_layout()

    return fig


def plot_work_tags_distribution(df, city_name="全国"):
    """绘制工作标签分布图"""
    # 合并所有工作标签
    all_tags = ' '.join(df['工作标签'].astype(str))

    # 简单处理标签数据
    tags_list = []
    for tag_str in df['工作标签'].dropna():
        if tag_str != '[]':
            # 移除方括号并分割
            tags = tag_str.replace('[', '').replace(']', '').replace("'", "").split(', ')
            tags_list.extend([tag.strip() for tag in tags if tag.strip()])

    # 统计标签频次
    tag_counts = pd.Series(tags_list).value_counts().head(15)

    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.barh(tag_counts.index, tag_counts.values, color='lightcoral')

    # 添加数值标签
    for bar in bars:
        width = bar.get_width()
        ax.text(width, bar.get_y() + bar.get_height() / 2,
                f'{int(width)}',
                ha='left', va='center', fontsize=9)

    ax.set_xlabel('出现频次')
    ax.set_ylabel('工作标签')
    ax.set_title(f'{city_name}热门工作标签TOP15')
    plt.tight_layout()

    return fig


def generate_wordcloud_and_frequency(df, city_name="全国"):
    """生成福利待遇词云图和词频统计图"""
    df_valid = df.dropna(subset=['福利列表'])

    if df_valid.empty:
        st.warning("警告：没有有效的福利数据用于展示")
        return None, None

    # 合并所有福利信息
    all_benefits = ' '.join(df_valid['福利列表'].astype(str))

    # 简单的中文分词
    words = jieba.cut(all_benefits)
    # 过滤掉单字符和空字符串
    words = [word.strip() for word in words if len(word.strip()) > 1]
    text = ' '.join(words)

    # 统计词频
    word_freq = {}
    for word in words:
        if word in word_freq:
            word_freq[word] += 1
        else:
            word_freq[word] = 1

    # 获取前20个高频词
    top_words = dict(sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20])

    # 动态检测字体路径
    font_paths = ['simhei.ttf', '/System/Library/Fonts/PingFang.ttc', 'C:/Windows/Fonts/simhei.ttf']
    font_path = None
    for path in font_paths:
        if os.path.exists(path):
            font_path = path
            break

    if not font_path:
        st.warning("警告：未找到可用的中文字体文件")
        return None, None

    # 生成词云
    try:
        wordcloud = WordCloud(
            font_path=font_path,
            width=800,
            height=400,
            background_color='white',
            colormap='viridis'
        ).generate(text)

        # 创建词云图
        fig1, ax1 = plt.subplots(figsize=(10, 5))
        ax1.imshow(wordcloud, interpolation='bilinear')
        ax1.axis('off')
        ax1.set_title(f'{city_name}福利待遇词云图')
        plt.tight_layout()

        # 创建词频统计图
        if top_words:
            fig2, ax2 = plt.subplots(figsize=(12, 8))
            words_list = list(top_words.keys())
            freq_list = list(top_words.values())

            # 使用渐变色彩
            colors = cm.get_cmap('viridis')(np.linspace(0, 1, len(freq_list)))
            bars = ax2.barh(words_list, freq_list, color=colors)

            # 添加数值标签
            for i, (bar, freq) in enumerate(zip(bars, freq_list)):
                ax2.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                         str(freq), ha='left', va='center', fontsize=9)

            ax2.set_xlabel('出现频次')
            ax2.set_ylabel('福利关键词')
            ax2.set_title(f'{city_name}福利待遇词频统计（TOP20）')
            plt.tight_layout()
        else:
            fig2 = None

        return fig1, fig2
    except Exception as e:
        st.warning(f"警告：生成词云图时发生错误: {e}")
        return None, None


def main():
    st.set_page_config(page_title="招聘数据可视化", layout="wide")
    # 设置整个页面背景为渐变蓝色
    st.markdown(
        """
        <style>
        .stApp {
            background-color: white;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        """
        <style>
        h1, h2, h3, h4, h5, h6, p, li, .stMarkdown, .stText, .stMetricLabel, .stMetricValue {
            background: linear-gradient(90deg, #ff6b6b, #ffa500, #ffff00, #00ff00, #00ffff, #0000ff, #8a2be2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            color: transparent;
            background-size: 300% 300%;
            animation: rainbow 3s ease infinite;
        }

        @keyframes rainbow {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        /* 确保图表不受影响 */
        .matplotlib {
            color: initial;
            background: initial;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    # 设置总职位数、有效薪资数据、平均薪资的数值为黑色斜体
    st.markdown(
        """
        <style>
        /* 选择前三个指标值（总职位数，有效薪资数据，平均薪资） */
        [data-testid="stMetricValue"] {
            color: black !important;
            font-style: italic !important;
        }

        /* 确保指标标签保持炫彩 */
        [data-testid="stMetricLabel"] {
            background: linear-gradient(90deg, #ff6b6b, #ffa500, #ffff00, #00ff00, #00ffff, #0000ff, #8a2be2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            color: transparent;
            background-size: 300% 300%;
            animation: rainbow 3s ease infinite;
            font-style: normal !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # 创建一个名为"BOSS直聘"的容器
    with st.container():
        st.title('📊 招聘数据可视化分析')
        st.markdown("---")

        # 加载数据
        df = load_data()
        if df is None:
            return

        # 处理薪资数据
        with st.spinner('正在处理薪资数据...'):
            df['平均薪资'] = df['期待薪资'].apply(process_salary)

        # 城市选择功能
        st.subheader('🏙️ 请选择要分析的城市')
        cities = ["全国"] + sorted(df['城市'].dropna().unique().tolist())

        # 使用session_state保存选择的城市
        if 'selected_city' not in st.session_state:
            st.session_state.selected_city = "全国"

        # 创建城市选择器
        selected_city = st.selectbox('请选择城市', cities, index=0)

        # 更新session_state
        st.session_state.selected_city = selected_city

        # 根据选择的城市过滤数据
        if selected_city == "全国":
            df_filtered = df
            city_name = "全国"
        else:
            df_filtered = df[df['城市'] == selected_city]
            city_name = selected_city

        # 检查是否有数据
        if df_filtered.empty:
            st.info(f"该城市 {selected_city} 暂无岗位信息")
            return

        # 在数据概览部分添加更多信息
        # 显示数据概览
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
            # 添加公司数量统计
            company_count = df_filtered['公司'].nunique()
            st.metric("公司数量", company_count)

        st.markdown("---")

        # 显示该城市的所有招聘信息表格
        with st.expander(f"📋 {city_name}所有招聘信息", expanded=False):
            # 选择要显示的列
            display_columns = ['职位', '期待薪资', '工作经验', '学历', '公司', '公司规模']

            # 添加平均薪资列（如果存在）
            if '平均薪资' in df_filtered.columns:
                display_columns.append('平均薪资')
                # 格式化平均薪资显示
                df_display = df_filtered[display_columns].copy()
                df_display['平均薪资'] = df_display['平均薪资'].apply(
                    lambda x: f"{x:.0f}元" if pd.notna(x) else "N/A"
                )
            else:
                df_display = df_filtered[display_columns]

            # 显示表格，隐藏索引
            st.dataframe(df_display, use_container_width=True, hide_index=True)

        # 创建图表显示区域
        st.subheader(f'📈 {city_name}数据分析图表')

        # 第一行图表 - 学历平均薪资和公司规模
        col1, col2 = st.columns(2)

        with col1:
            with st.expander("🎓 不同学历的平均薪资", expanded=True):
                salary_data = get_salary_by_education_data(df_filtered, city_name)
                if salary_data is not None:
                    st.dataframe(salary_data, use_container_width=True, hide_index=True)
                else:
                    st.info("暂无数据可显示")

        with col2:
            with st.expander("🏢 不同公司规模的岗位数量", expanded=True):
                fig2 = plot_job_count_by_company_size(df_filtered, city_name)
                if fig2:
                    st.pyplot(fig2)

        # 第二行图表 - 工作经验与薪资和城市薪资对比
        col3, col4 = st.columns(2)

        with col3:
            with st.expander("💼 工作经验与薪资关系", expanded=True):
                fig3 = plot_salary_by_experience(df_filtered, city_name)
                if fig3:
                    st.pyplot(fig3)

        with col4:
            with st.expander("🏙️ 城市薪资对比", expanded=True):
                if selected_city != "全国":
                    fig4 = plot_salary_by_city(df, selected_city)
                    if fig4:
                        st.pyplot(fig4)
                else:
                    st.info("请选择具体城市以查看城市薪资对比")

        # 第三行图表 - 热门职位和学历经验交叉分析
        col5, col6 = st.columns(2)

        with col5:
            with st.expander("热门职位TOP10", expanded=True):
                fig5 = plot_top_jobs(df_filtered, 10, city_name)
                if fig5:
                    st.pyplot(fig5)

        with col6:
            with st.expander("学历与经验交叉分析", expanded=True):
                fig6 = plot_education_experience_bar(df_filtered, city_name)
                if fig6:
                    st.pyplot(fig6)

        # 第四行图表 - 薪资分布
        with st.expander("💰 薪资分布情况", expanded=True):
            fig7 = plot_salary_distribution(df_filtered, city_name)
            if fig7:
                st.pyplot(fig7)

        # 福利待遇词云图单独一行显示，更加突出
        st.markdown("---")
        st.subheader("🎁 福利待遇词云图")

        # 为福利待遇部分添加特殊样式
        st.markdown(
            """
            <style>
            [data-testid="stExpander"] {
                border: 2px solid #ff6b6b;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        with st.expander("福利待遇词云图和词频统计", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                fig8_wordcloud, fig8_frequency = generate_wordcloud_and_frequency(df_filtered, city_name)
                if fig8_wordcloud:
                    st.pyplot(fig8_wordcloud)
                else:
                    st.info("暂无词云图数据")
            with col2:
                if fig8_frequency:
                    st.pyplot(fig8_frequency)
                else:
                    st.info("暂无词频统计数据")

        # 在main函数中添加新的图表展示部分
        # 在福利待遇词云图之后添加：

        # 技能要求和工作标签分析
        st.markdown("---")
        st.subheader("🎯 技能与标签分析")

        col1, col2 = st.columns(2)

        with col1:
            with st.expander("热门技能要求", expanded=True):
                fig_skills = plot_skill_distribution(df_filtered, city_name)
                if fig_skills:
                    st.pyplot(fig_skills)
                else:
                    st.info("暂无技能数据可显示")

        with col2:
            with st.expander("热门工作标签", expanded=True):
                fig_tags = plot_work_tags_distribution(df_filtered, city_name)
                if fig_tags:
                    st.pyplot(fig_tags)
                else:
                    st.info("暂无标签数据可显示")


if __name__ == "__main__":
    main()