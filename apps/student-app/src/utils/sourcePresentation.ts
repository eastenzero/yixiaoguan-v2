import type { Source } from '@/types/chat'

type SourcePresentation = Partial<Source> & { title: string }

const SOURCE_CATALOG: Record<string, SourcePresentation> = {
  '00-scholarship-router': { title: '山东第一医科大学奖学金分类与适用范围说明', source_url: 'https://www.sdfmu.edu.cn/jgsz1/jxjg.htm', published_at: '2026-08-03' },
  '01-comprehensive-assessment': { title: '山东第一医科大学本科生综合素质测评办法（暂行）', source_url: 'https://sps.sdfmu.edu.cn/info/1039/2268.htm', published_at: '2022-09-04', screenshot_url: '/static/evidence/scholarship/comprehensive-quality-assessment-policy.png' },
  '02-inspirational-2023-2024-history': { title: '2023—2024学年本科生国家励志奖学金、省政府励志奖学金评审通知', source_url: 'https://sa.sdfmu.edu.cn/info/1341/18991.htm', published_at: '2024-09-24', screenshot_url: '/static/evidence/scholarship/2023-2024-inspirational-scholarship-article.png' },
  '03-hongyi-2024-2025-result': { title: '2024—2025学年“弘毅”奖学金推荐名单公示', source_url: 'https://sa.sdfmu.edu.cn/info/1341/21871.htm', published_at: '2026-05-15' },
  '04-pharmacy-inspirational-2024-2025-result': { title: '药学院2024—2025学年励志奖学金评审结果公示', source_url: 'https://sps.sdfmu.edu.cn/info/1049/17834.htm', published_at: '2025-10-11' },
  '05-national-scholarship-current-base': { title: '本专科生国家奖学金现行国家基础政策', source_url: 'https://www.gov.cn/zhengce/202507/content_7032288.htm', published_at: '2025-07-29' },
  '06-national-inspirational-current-base': { title: '本专科生国家励志奖学金现行国家基础政策', source_url: 'https://www.gov.cn/zhengce/202507/content_7032288.htm', published_at: '2025-07-29' },
  '07-hongyi-2024-2025-policy': { title: '2024—2025学年“弘毅”奖学金申请细则', source_url: 'https://sa.sdfmu.edu.cn/info/1341/21411.htm', published_at: '2026-03-23' },
  '08-self-reliance-star-2026': { title: '关于开展2026届“自强之星”评选工作的通知', source_url: 'https://sa.sdfmu.edu.cn/info/1341/21471.htm', published_at: '2026-03-25' },
  '09-pharmacy-national-2024-2025': { title: '药学院2024—2025学年国家奖学金评审及公示', source_url: 'https://sps.sdfmu.edu.cn/info/1049/17764.htm', published_at: '2025-09-25' },
  '10-biomedical-provincial-2024-2025': { title: '生物医学科学学院2024—2025学年省政府奖学金评审', source_url: 'https://bms.sdfmu.edu.cn/info/1009/7532.htm', published_at: '2025-10-10' },
  '11-sports-rehab-scholarships-2024': { title: '运动医学与康复学院2024年国家及省政府奖学金评审', source_url: 'https://ykxy.sdfmu.edu.cn/info/1045/13661.htm', published_at: '2024-09-29' },
  '12-experimental-animal-enterprise-awards-2026': { title: '实验动物学院企业专项奖助学金项目说明', source_url: 'https://sydw.sdfmu.edu.cn/info/1002/8944.htm', published_at: '2026-05-25' },
  '13-biomedical-excellence-2022': { title: '首届生物医学优秀本科生奖学金评选结果', source_url: 'https://bms.sdfmu.edu.cn/info/1009/1953.htm', published_at: '2022-12-22' },
  '14-chemistry-aibo-2024': { title: '化学与制药工程学院2024年“爱博科研之星”奖学金通知', source_url: 'https://cpe.sdfmu.edu.cn/info/1113/5684.htm', published_at: '2024-04-25' },
  '15-college-coverage-routing': { title: '山东第一医科大学各学院奖学金公开资料索引', source_url: 'https://www.sdfmu.edu.cn/jgsz1/jxjg.htm', published_at: '2026-08-03' },
  '16-medical-management-coverage': { title: '医药管理学院本科奖学金公开资料说明', source_url: 'https://mm.sdfmu.edu.cn/', published_at: '2026-08-03' },
  '17-medical-security-scholarships-2024-2025': { title: '医疗保障学院2024—2025学年奖学金评审记录', source_url: 'https://ylbz.sdfmu.edu.cn/info/1013/17775.htm', published_at: '2025-10-10' },
  '18-foreign-language-scholarships-2024-2025': { title: '外国语学院2024—2025学年奖学金评审记录', source_url: 'https://language.sdfmu.edu.cn/info/1020/6438.htm', published_at: '2025-09-30' },
  '19-graduate-scholarship-route': { title: '山东第一医科大学研究生奖助学金管理与通知入口', source_url: 'https://graduate.sdfmu.edu.cn/xsgz/zzgl.htm', published_at: '2025-09-08' },
  '20-international-scholarship-route': { title: '山东第一医科大学国际学生奖学金通知入口', source_url: 'https://ie.sdfmu.edu.cn/zsxx/jxj.htm', published_at: '2026-08-03' },
  '00-academic-impact-router': { title: '挂科影响问题分类与适用范围说明', source_url: 'https://www.sdfmu.edu.cn/', published_at: '2026-08-04' },
  '01-party-development-current-rule-2026': { title: '中国共产党发展党员工作细则（2026年修订）', source_url: 'https://www.moe.gov.cn/jyb_xxgk/moe_1777/moe_1778/202605/t20260520_1437115.html', published_at: '2026-05-18' },
  '02-party-development-college-gap': { title: '山东第一医科大学学院党员发展公开材料覆盖说明', source_url: 'https://www.sdfmu.edu.cn/jgsz1/jxjg.htm', published_at: '2026-08-04' },
  '03-comprehensive-assessment-policy': { title: '山东第一医科大学本科生综合素质测评办法（暂行）', source_url: 'https://sps.sdfmu.edu.cn/info/1039/2268.htm', published_at: '2022-09-04', screenshot_url: '/static/evidence/scholarship/comprehensive-quality-assessment-policy.png' },
  '04-inspirational-scholarship-2023-2024': { title: '2023—2024学年本科生励志奖学金评审通知', source_url: 'https://sa.sdfmu.edu.cn/info/1341/18991.htm', published_at: '2024-09-24', screenshot_url: '/static/evidence/campus/inspirational-scholarship-2023-2024-full.png' },
  '05-hongyi-2024-2025': { title: '2024—2025学年“弘毅”奖学金申请细则', source_url: 'https://sa.sdfmu.edu.cn/info/1341/21411.htm', published_at: '2026-03-23' },
  '06-answer-matrix': { title: '挂科对入党、奖学金和评优影响的回答说明', source_url: 'https://www.sdfmu.edu.cn/', published_at: '2026-08-04' },
  '07-school-honors-2024-2025': { title: '2024—2025学年校级优秀学生等荣誉称号评选通知', source_url: 'https://sa.sdfmu.edu.cn/info/1341/21151.htm', published_at: '2025-11-25', screenshot_url: '/static/evidence/campus/honors-2024-2025.png' },
  '08-comprehensive-scholarship-2024-2025': { title: '2024—2025学年校级综合奖学金评选通知', source_url: 'https://sa.sdfmu.edu.cn/info/1341/21131.htm', published_at: '2025-11-18', screenshot_url: '/static/evidence/campus/comprehensive-scholarship-2024-2025.png' },
  '09-medical-management-retake-2025-2026': { title: '2025—2026学年第二学期重修、补修报名通知', source_url: 'https://mm.sdfmu.edu.cn/info/1686/21807.htm', published_at: '2026-03-13' },
}

const SOURCE_TITLE_ALIASES: Record<string, SourcePresentation> = {
  '本科生综合素质测评：校级参考框架': {
    title: '山东第一医科大学本科生综合素质测评办法（暂行）',
    source_url: 'https://sps.sdfmu.edu.cn/info/1039/2268.htm',
    published_at: '2022-09-04',
    source_label: '学校官网',
    verified: true,
    screenshot_url: '/static/evidence/scholarship/comprehensive-quality-assessment-policy.png',
  },
  '关于评选2024-2025学年校级综合奖学金的通知（模板版）': {
    title: '2024—2025学年校级综合奖学金评选通知',
    source_url: 'https://sa.sdfmu.edu.cn/info/1341/21131.htm',
    published_at: '2025-11-18',
    source_label: '学校官网',
    verified: true,
    screenshot_url: '/static/evidence/campus/comprehensive-scholarship-2024-2025.png',
  },
  '2024—2025学年校级综合奖学金评选条件': {
    title: '2024—2025学年校级综合奖学金评选通知',
    source_url: 'https://sa.sdfmu.edu.cn/info/1341/21131.htm',
    published_at: '2025-11-18',
    source_label: '学校官网',
    verified: true,
    screenshot_url: '/static/evidence/campus/comprehensive-scholarship-2024-2025.png',
  },
  '挂科影响问题如何拆分': {
    title: '挂科影响问题：按入党、奖学金与评优分别核验',
    source_url: 'https://www.sdfmu.edu.cn/jgsz1/dzgljg.htm',
    source_label: '学校官网',
    verified: true,
  },
  '挂科影响问题应如何拆分': {
    title: '挂科影响问题：按入党、奖学金与评优分别核验',
    source_url: 'https://www.sdfmu.edu.cn/jgsz1/dzgljg.htm',
    source_label: '学校官网',
    verified: true,
  },
  '挂科对党员发展的上级规则边界': {
    title: '中国共产党发展党员工作细则（现行上级规则）',
    source_url: 'https://www.moe.gov.cn/jyb_xxgk/moe_1777/moe_1778/202605/t20260520_1437115.html',
    source_label: '权威政策来源',
    verified: true,
  },
  '挂科影响问题的标准回答矩阵': {
    title: '山东第一医科大学本科生综合素质测评办法（暂行）',
    source_url: 'https://sps.sdfmu.edu.cn/info/1039/2268.htm',
    source_label: '学院官网',
    verified: true,
    screenshot_url: '/static/evidence/scholarship/comprehensive-quality-assessment-policy.png',
  },
}

const RELATED_OFFICIAL_RULES: Array<{ terms: string[]; catalogKeys: string[] }> = [
  {
    terms: ['综合奖学金'],
    catalogKeys: ['01-comprehensive-assessment', '08-comprehensive-scholarship-2024-2025'],
  },
  {
    terms: ['励志奖学金'],
    catalogKeys: ['06-national-inspirational-current-base', '02-inspirational-2023-2024-history'],
  },
  {
    terms: ['弘毅'],
    catalogKeys: ['07-hongyi-2024-2025-policy', '03-hongyi-2024-2025-result'],
  },
  {
    terms: ['挂科', '补考', '重修'],
    catalogKeys: ['01-comprehensive-assessment', '07-school-honors-2024-2025', '09-medical-management-retake-2025-2026'],
  },
  {
    terms: ['优秀学生', '评优'],
    catalogKeys: ['07-school-honors-2024-2025', '01-comprehensive-assessment'],
  },
  {
    terms: ['入党', '党员发展'],
    catalogKeys: ['01-party-development-current-rule-2026'],
  },
]

function sourceKey(title: string): string {
  return title.trim().replace(/\.(md|markdown|txt)$/i, '')
}

function normalizedTitle(title: string): string {
  return sourceKey(title)
    .replace(/^KB-V\d+-C\d+-\d+\s*/i, '')
    .replace(/[\s“”"'《》【】\[\]（）()—–·：:]/g, '')
    .toLowerCase()
}

function catalogForTitle(title: string): SourcePresentation | undefined {
  const direct = SOURCE_CATALOG[sourceKey(title)]
  if (direct) return direct

  const alias = SOURCE_TITLE_ALIASES[sourceKey(title)]
  if (alias) return alias

  const wanted = normalizedTitle(title)
  const aliasByTitle = Object.entries(SOURCE_TITLE_ALIASES).find(([aliasTitle]) => {
    const candidate = normalizedTitle(aliasTitle)
    return candidate === wanted || (candidate.length >= 8 && (candidate.includes(wanted) || wanted.includes(candidate)))
  })?.[1]
  if (aliasByTitle) return aliasByTitle

  return Object.values(SOURCE_CATALOG).find((item) => {
    const candidate = normalizedTitle(item.title)
    return candidate === wanted || (candidate.length >= 12 && (candidate.includes(wanted) || wanted.includes(candidate)))
  })
}

function headingFromContent(content?: string): string | undefined {
  const match = content?.match(/^#\s+(.+)$/m)
  return match?.[1]?.trim()
}

function fallbackTitle(source: Source): string {
  const raw = source.title?.trim() || ''
  const cleaned = raw
    .replace(/^KB-V\d+-C\d+-\d+\s*/i, '')
    .replace(/\.(md|markdown|txt)$/i, '')
    .trim()
  if (cleaned && !/^[\d\s._-]*[a-z][a-z\d\s._-]*$/i.test(cleaned)) return cleaned
  return headingFromContent(source.content) || source.category || '校内公开资料'
}

function officialLabel(url?: string): Pick<Source, 'source_type' | 'source_label' | 'verified'> {
  if (!url) return {}
  if (url.includes('gov.cn')) return { source_type: 'official_web', source_label: '政府官网', verified: true }
  if (url.includes('sdfmu.edu.cn')) return { source_type: 'official_web', source_label: '学校及学院官网', verified: true }
  return {}
}

export function presentSource(source: Source): Source {
  const catalog = catalogForTitle(source.title || '')
  const sourceUrl = source.source_url || catalog?.source_url
  const inferredOfficial = officialLabel(sourceUrl)
  return {
    ...catalog,
    ...source,
    ...inferredOfficial,
    title: catalog?.title || fallbackTitle(source),
    source_url: sourceUrl,
    published_at: source.published_at || catalog?.published_at,
    screenshot_url: source.screenshot_url || catalog?.screenshot_url,
    source_type: source.source_type || catalog?.source_type || inferredOfficial.source_type,
    source_label: source.source_label || catalog?.source_label || inferredOfficial.source_label,
    verified: source.verified ?? catalog?.verified ?? inferredOfficial.verified,
  }
}

export function presentSources(sources?: Source[]): Source[] {
  const seen = new Set<string>()
  return (sources || [])
    .map(presentSource)
    .filter((source) => {
      const key = source.document_id || source.source_url || normalizedTitle(source.title)
      if (!key || seen.has(key)) return false
      seen.add(key)
      return true
    })
}

export function knowledgeBaseSources(sources?: Source[]): Source[] {
  const seen = new Set<string>()
  return presentSources(sources)
    .filter((source) => {
      const key = normalizedTitle(source.title)
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
    .slice(0, 2)
    .map((source) => ({
      ...source,
      source_url: undefined,
      source_type: 'knowledge_base',
      source_label: '医小管知识库',
      verified: false,
    }))
}

export function officialArticleSources(sources?: Source[]): Source[] {
  const seen = new Set<string>()
  const presented = presentSources(sources)
  const titleText = presented.map((source) => source.title).join(' ')
  const related = RELATED_OFFICIAL_RULES
    .filter((rule) => rule.terms.some((term) => titleText.includes(term)))
    .flatMap((rule) => rule.catalogKeys)
    .map((key) => SOURCE_CATALOG[key])
    .filter((source): source is SourcePresentation => !!source)
    .map((source) => presentSource(source as Source))

  return [...presented, ...related]
    .filter((source) => source.verified && !!source.source_url)
    .filter((source) => {
      const url = source.source_url as string
      if (seen.has(url)) return false
      seen.add(url)
      return true
    })
    .slice(0, 6)
}

export function mixedEvidenceSources(sources?: Source[]): Source[] {
  // Keep the retrieved evidence first. Related official links only supplement it.
  // Eight cards remain readable on mobile while giving broad answers enough traceability.
  const primary = presentSources(sources).slice(0, 6)
  const related = officialArticleSources(sources)
  const seen = new Set<string>()
  const mixed: Source[] = []
  const count = Math.max(primary.length, related.length)

  for (let index = 0; index < count; index += 1) {
    for (const source of [primary[index], related[index]]) {
      if (!source) continue
      const key = normalizedTitle(source.title)
      const existingIndex = mixed.findIndex((item) => normalizedTitle(item.title) === key)
      if (existingIndex >= 0) {
        if (!mixed[existingIndex].source_url && source.source_url) mixed[existingIndex] = source
        continue
      }
      const identity = source.source_url || source.document_id || key
      if (seen.has(identity)) continue
      seen.add(identity)
      mixed.push(source)
    }
  }

  return mixed.slice(0, 8)
}
