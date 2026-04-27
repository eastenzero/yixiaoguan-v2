# D1 Diversity Verification Report

## A. Test data setup
- Tai'an college selected: id=10, name=放射学院, campus=泰安校区
- New class: id=3, name=放射2024-1班, college_id=10
- New student: id=5, staff_id=13800000002, name=张小泰, college=放射学院, campus=泰安校区, class=放射2024-1班

## B. Question A (奖学金) — Tai'an stu
- conv_id: 38
- AI answer:
  ```
  你好！作为放射学院的同学，你们可申请的奖学金主要包括国家奖学金、省政府奖学金、国家励志奖学金和校级综合奖学金等。申请流程基本一致，分五步：个人提交申请、班级民主评议、学院审核与公开答辩、学院公示不少于2个工作日、报送至校学生资助管理中心。需要准备的材料包括：申请表、成绩单、成绩与综测排名表、获奖证书复印件等（具体以当年学院通知为准）。建议你及时查看学院公告栏或联系辅导员获取本学年细则～
  ```
- Mentions 放射学院 / 泰安校区: **Yes** ("放射学院的同学")
- Inputs transmitted: `{"college_name":"放射学院","campus":"泰安校区","class_name":"放射2024-1班"}`

## C. Question B (图书馆) — Tai'an stu
- conv_id: 39
- AI answer:
  ```
  山东第一医科大学泰安校区的图书馆是校内主要学习场所之一，具体信息如下：位置在泰安校区主教学区中心位置（靠近行政楼与教学楼A座），外观醒目，共五层，内设校史馆、微机房、图书阅览区等。开放时间：周一至周五 8:00–21:00，周六 8:00–16:00（15:00后禁止入内），周日 9:00–16:00（15:00后禁止入内）。入馆需刷校园卡，建议提前规划时间哦～
  ```
- Mentions 泰安: **Yes** ("泰安校区" repeated, 行政楼与教学楼A座, 五层)

## D. Question B (图书馆) — Jinan stu (control)
- conv_id: 40
- AI answer:
  ```
  山东第一医科大学济南校区的图书馆是黄河图书馆，位于济南校区校园内，是学校的标志性建筑。开放时间：周一至周五 8:00–21:00，周六 8:00–16:00（15:00后禁止入内），周日 9:00–16:00（15:00后禁止入内）。入馆需刷校园卡。节假日安排每年略有不同，建议关注图书馆官网或微信公众号获取最新通知。
  ```
- Mentions 济南: **Yes** ("济南校区", "黄河图书馆", "标志性建筑")

## E. Side-by-side comparison
| Aspect | Tai'an answer | Jinan answer |
|---|---|---|
| Campus mentioned | 泰安校区 (explicit) | 济南校区 (explicit) |
| Library name | 未提及具体名称 | 黄河图书馆 (specific name) |
| Location detail | 主教学区中心，靠近行政楼与教学楼A座，共五层 | 济南校区校园内，标志性建筑 |
| Different content? | **Yes** — materially different facts | |

## F. Dify messages.inputs verification
3 latest messages all have correct `college_name`/`campus`/`class_name` matching the user's profile: **True**
- Tai'an Q1: `{"college_name":"放射学院","campus":"泰安校区","class_name":"放射2024-1班"}`
- Tai'an Q2: `{"college_name":"放射学院","campus":"泰安校区","class_name":"放射2024-1班"}`
- Jinan Q2: `{"college_name":"临床与基础医学院","campus":"济南校区","class_name":"临床2024-1班"}`

## G. Verdict
**STRONG**: AI answers visibly differ between the two students; campus/college names from inputs are referenced correctly. D1 fully validated for diverse samples.
