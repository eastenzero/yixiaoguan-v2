# W2 扫描任务生成器（kb-pipeline 本地版）
# 用法：powershell -File generate-w2-tasks.ps1

$base = 'C:\Users\Administrator\Documents\code\kb-pipeline'
$taskDir = Join-Path $base 'kb-cleaning-plans\tasks'
$templateDir = Join-Path $base 'kb-cleaning-plans\templates'
$w2Base = Join-Path $base 'ws2-website-scrape\scraped-pages'
$reportDir = Join-Path $base 'ws2-website-scrape\kimi-reports'

New-Item -ItemType Directory -Force -Path $taskDir | Out-Null
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null

$deptMap = @{
    '后勤管理部' = 'C02 校园生活'
    '计划财务部' = 'C03 财务与缴费'
    '学生工作部（武装部）' = 'C04 奖助学金 + C11 行政'
    '信息门户' = 'C06 图书馆与信息化'
    '研究生院（研究生教育中心）' = 'C08 研究生事务'
    '研究生招生' = 'C08 研究生事务'
    '对外合作交流部' = 'C09 国际交流'
    '团委' = 'C10 学术与竞赛'
    '科研部' = 'C10 学术与竞赛'
    '安全保卫部' = 'C11 行政与规章'
    '学校概况' = 'C12 院系与学校'
    '档案馆（校史馆）' = 'C12 院系与学校'
    '学生' = 'C11 行政与规章'
    '实践教学' = 'C01 教务与学籍'
    '教师教学发展中心（医学教育研究发展中心）' = 'C01 教务与学籍'
    '发展规划与学科建设部（教学评估办公室）' = 'C12 院系与学校'
    '国有资产与实验室管理部' = 'C11 行政与规章'
    '科技查新' = 'C06 图书馆与信息化'
    '书记、校长信箱' = 'C11 行政与规章'
    '临床与基础医学院（基础医学研究所）' = 'C12 院系与学校'
    '公共卫生与健康管理学院' = 'C12 院系与学校'
    '化学与制药工程学院' = 'C12 院系与学校'
    '医学信息与人工智能学院' = 'C12 院系与学校'
    '医药管理学院' = 'C12 院系与学校'
    '口腔医学院' = 'C12 院系与学校'
    '国际教育学院' = 'C12 院系与学校'
    '外国语学院' = 'C12 院系与学校'
    '实验动物学院（省实验动物中心）' = 'C12 院系与学校'
    '护理学院' = 'C12 院系与学校'
    '放射学院' = 'C12 院系与学校'
    '生命科学学院' = 'C12 院系与学校'
    '生物医学科学学院（省医药生物技术研究中心）' = 'C12 院系与学校'
    '药学院（药物研究所）' = 'C12 院系与学校'
    '脑科学与类脑研究院' = 'C12 院系与学校'
    '运动医学与康复学院' = 'C12 院系与学校'
    '预防医学科学学院（放射医学研究所）' = 'C12 院系与学校'
    '马克思主义学院' = 'C12 院系与学校'
}

$generated = 0

foreach ($dept in $deptMap.Keys) {
    $deptPath = Join-Path $w2Base $dept
    if (-not (Test-Path $deptPath)) { continue }
    
    $fileCount = (Get-ChildItem $deptPath -Filter '*.md' | Measure-Object).Count
    if ($fileCount -eq 0) { continue }
    
    $category = $deptMap[$dept]
    $safeName = $dept -replace '[（）\(\)]', '' -replace '、', '-'
    $taskFile = Join-Path $taskDir "w2-scan-$safeName.md"
    
    $content = @"
# 任务：扫描 W2 ${dept}页面

## 工作目录
``$deptPath``

## 任务概述
扫描${dept}目录下的所有 .md 文件（共 $fileCount 个），按照知识库入库标准进行筛选和分类，产出结构化扫描报告。

## 输入
- 待扫描目录：``$deptPath``
- 筛选标准：请读取 ``$templateDir\SCREENING-CRITERIA.md``
- 报告格式：请读取 ``$templateDir\SCAN-REPORT-FORMAT.md``

## 步骤

1. 先读取上述两个模板文件，理解筛选标准和输出格式
2. 列出工作目录下所有 .md 文件
3. 逐个读取每个文件内容
4. 按照 SCREENING-CRITERIA.md 中的 5 条标准判断每个文件是"保留"还是"丢弃"
5. 对保留的文件标注分类（该部门主要对应 $category）
6. 按照 SCAN-REPORT-FORMAT.md 的格式生成报告

## 输出
将完整的扫描报告写入：
``$reportDir\scan-$safeName.md``

报告开头加上：
```
# W2 扫描报告：${dept}
> 扫描时间：{当前日期}
> 数据来源：官网抓取（ws2-website-scrape）
> 对应 KB 分类：${category}
```
"@
    
    Set-Content -Path $taskFile -Value $content -Encoding UTF8
    $generated++
}

Write-Host "Generated $generated W2 task files in $taskDir"
