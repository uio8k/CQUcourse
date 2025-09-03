from DrissionPage import ChromiumPage
import csv

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
# 启动监听：监听所有 joblist.json 请求
dp.listen.start('https://www.zhipin.com/wapi/zpgeek/search/joblist.json')

# 访问网页
dp.get('https://www.zhipin.com/web/geek/jobs?city=100010000&position=100101')

# 等待初始页面加载完成
resp = dp.listen.wait()
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
f.close()
print('成功爬取第一页，文件f已关闭')