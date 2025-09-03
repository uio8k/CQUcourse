from DrissionPage import ChromiumPage
import csv
import time
import urllib.parse

# 实例化浏览器对象
dp = ChromiumPage()

# 打开文件写入CSV
f = open('data3.3.csv', 'a', encoding='utf-8', newline='')
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
page_num = 1
# 使用更通用的监听方式

max_pages = 15
next_page = 1

while page_num <= max_pages:
    print(f'正在爬取第{page_num}页...')

    # 构造带page参数的URL
    base_url = 'https://www.zhipin.com/wapi/zpgeek/search/joblist.json'

    next_url = (f"{base_url}?page={page_num}")
    # 先启动监听，再访问页面
    dp.listen.start(next_url) # 通过两次监听来规避反爬
    dp.get('https://www.zhipin.com/web/geek/jobs?city=100010000&position=100106&jobType=1901')
    for n in range(page_num):
        dp.scroll(5000)
        time.sleep(2)
    try:
        # 等待页面API响应
        resp = dp.listen.wait(timeout=3)  # 增加超时时间

        if not resp:
            print(f"第{page_num}页监听超时，可能没有更多数据")
            no_more_data = True
            break

        print(f"成功监听到第{page_num}页的响应")
        json_data = resp.response.body

        # 检查响应数据
        if not json_data:
            print(f"第{page_num}页响应为空")
            no_more_data = True
            continue

        if 'code' in json_data and json_data['code'] != 0:
            print(f"第{page_num}页API返回错误: {json_data.get('message', '未知错误')}")
            no_more_data = True
            continue

        if 'zpData' not in json_data or 'jobList' not in json_data['zpData']:
            print(f"第{page_num}页数据格式不正确")
            no_more_data = True
            continue

        jobList = json_data['zpData']['jobList']

        if not jobList or len(jobList) == 0:
            print(f"第{page_num}页没有职位数据，已到达最后一页")
            no_more_data = True
            continue

        print(f"第{page_num}页获取到{len(jobList)}个职位")
        # 写入数据
        for job in jobList:
            dic = {
                '职位': job.get('jobName', ''),
                '期待薪资': job.get('salaryDesc', ''),
                '工作标签': job.get('jobLabels', []),
                '技能要求': job.get('skills', []),
                '工作经验': job.get('jobExperience', ''),
                '学历': job.get('jobDegree', ''),
                '城市': job.get('cityName', ''),
                '公司': job.get('brandName', ''),
                '公司规模': job.get('brandScaleName', ''),
                '福利列表': job.get('welfareList', []),
            }
            csv_writer.writerow(dic)

    except Exception as e:
        print(f"处理第{page_num}页数据时出错: {e}")
        import traceback
        traceback.print_exc()

    # 等待一段时间再处理下一页
    time.sleep(2)
    page_num += 1
f.close()
dp.quit()
print('爬取完成，文件已关闭')
