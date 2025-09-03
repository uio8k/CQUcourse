from DrissionPage import ChromiumPage
import csv
import time

# 实例化浏览器对象
dp = ChromiumPage()

# 打开文件写入CSV
f = open('data001.csv', 'a', encoding='utf-8', newline='')
csv_writer = csv.DictWriter(f, fieldnames=[
    '职位',
    '期待薪资',
    '工作标签',
    '技能要求',
    '工作经验',
    '学历',
    '城市',
    '公司',
    '公司规模',
    '福利列表'
])
csv_writer.writeheader()

# 访问网页
dp.get('https://www.zhipin.com/web/geek/jobs?city=100010000&position=100202')
time.sleep(2)
page_num = 1

print(f'正在爬取第{page_num}页...')

# 启动监听对应页面的请求
dp.listen.start(f'https://www.zhipin.com/wapi/zpgeek/search/joblist.json?page={page_num}')

# 等待页面API响应
resp = dp.listen.wait(timeout=5)  # 设置超时时间
json_data = resp.response.body
jobList = json_data['zpData']['jobList']
for job in jobList:
    dic = {
        '职位': job['jobName'],
        '期待薪资': job['salaryDesc'],
        '工作标签': job['jobLabels'],
        '技能要求': job['skills'],
        '工作经验': job['jobExperience'],
        '学历': job['jobDegree'],
        '城市': job['cityName'],
        '公司': job['brandName'],
        '公司规模': job['brandScaleName'],
        '福利列表': job['welfareList'],
        }
    csv_writer.writerow(dic)
# 模拟鼠标滚轮向下滑动
dp.scroll.to_bottom(5000)
print('已模拟鼠标滚轮向下滑动')

# 检测滚动之后是否还有新内容出现
print(f'已成功获取第{page_num}页数据，准备获取下一页...')
page_num += 1
time.sleep(2)  # 页面间等待

f.close()
print('爬取完成，文件已关闭')
