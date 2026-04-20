# 任务：扫描 W2 发展规划与学科建设部（教学评估办公室）页面

## 工作目录
`C:\Users\Administrator\Documents\code\kb-pipeline\ws2-website-scrape\scraped-pages\发展规划与学科建设部（教学评估办公室）`

## 任务概述
扫描发展规划与学科建设部（教学评估办公室）目录下的所有 .md 文件（共 35 个），按照知识库入库标准进行筛选和分类，产出结构化扫描报告。

## 输入
- 待扫描目录：`C:\Users\Administrator\Documents\code\kb-pipeline\ws2-website-scrape\scraped-pages\发展规划与学科建设部（教学评估办公室）`
- 筛选标准：请读取 `C:\Users\Administrator\Documents\code\yixiaoguan-v2\docs\kb-cleaning-plans\templates\SCREENING-CRITERIA.md`
- 报告格式：请读取 `C:\Users\Administrator\Documents\code\yixiaoguan-v2\docs\kb-cleaning-plans\templates\SCAN-REPORT-FORMAT.md`

## 步骤

1. 先读取上述两个模板文件，理解筛选标准和输出格式
2. 列出工作目录下所有 .md 文件
3. 逐个读取每个文件内容
4. 按照 SCREENING-CRITERIA.md 中的 5 条标准判断每个文件是"保留"还是"丢弃"
5. 对保留的文件标注分类（该部门主要对应 C12 院系与学校）
6. 按照 SCAN-REPORT-FORMAT.md 的格式生成报告

## 输出
将完整的扫描报告写入：
`C:\Users\Administrator\Documents\code\kb-pipeline\ws2-website-scrape\kimi-reports\scan-发展规划与学科建设部教学评估办公室.md`

报告开头加上：
`
# W2 扫描报告：发展规划与学科建设部（教学评估办公室）
> 扫描时间：{当前日期}
> 数据来源：官网抓取（ws2-website-scrape）
> 对应 KB 分类：C12 院系与学校
`
