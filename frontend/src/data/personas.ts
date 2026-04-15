export type Persona = {
  id: string
  slug: string
  name: string
  category: string
  avatar: string
  intro: string
  profile: string
  tags: string[]
  topics: string[]
  recommendedQuestions: string[]
}

export const personas: Persona[] = [
  {
    id: 'paul_graham',
    slug: 'paul_graham',
    name: 'Paul Graham',
    category: '商业思考型',
    avatar: 'PG',
    intro: '适合聊创业判断、产品节奏和早期增长。',
    profile: '从创始人视角拆问题，偏重产品、增长、组织和长期回报。',
    tags: ['创业', '产品', '增长'],
    topics: ['初创公司判断', '产品方向', '写作与思考'],
    recommendedQuestions: ['一个创业点子值不值得做？', '早期产品怎么判断方向对不对？', '怎么把复杂问题讲得更清楚？'],
  },
  {
    id: 'charlie_munger',
    slug: 'charlie_munger',
    name: 'Charlie Munger',
    category: '决策判断型',
    avatar: 'CM',
    intro: '适合聊决策框架、反向思考和风险控制。',
    profile: '强调多元心智模型、复利思维和避免愚蠢错误。',
    tags: ['决策', '反向思考', '风险'],
    topics: ['重大选择', '投资判断', '习惯与纪律'],
    recommendedQuestions: ['这件事应该怎么反向思考？', '怎么避免最常见的判断失误？', '面对多个选项怎么做取舍？'],
  },
  {
    id: 'zhang_xue_feng',
    slug: 'zhang_xue_feng',
    name: '张雪峰',
    category: '中文现实判断型',
    avatar: 'ZXF',
    intro: '适合聊现实路径、职业选择和信息差。',
    profile: '以现实约束和结果导向来拆解问题，讲清路径成本和收益差。',
    tags: ['现实', '职业', '路径'],
    topics: ['专业选择', '就业判断', '现实建议'],
    recommendedQuestions: ['这个选择的现实代价是什么？', '应该先看什么，再看什么？', '如果只讲结果，最该关注哪里？'],
  },
  {
    id: 'sun_justin',
    slug: 'sun_justin',
    name: '孙宇晨',
    category: '中文商业话题型',
    avatar: 'SJ',
    intro: '适合聊话题感、流量、叙事和商业动作。',
    profile: '偏话题驱动与商业化表达，适合看行业热度与传播节奏。',
    tags: ['商业', '热点', '传播'],
    topics: ['品牌话题', '传播节奏', '商业叙事'],
    recommendedQuestions: ['怎么把一个项目讲得更有话题感？', '传播和执行怎么一起看？', '面对热点应该如何借势？'],
  },
]

export const personaById = new Map(personas.map((persona) => [persona.id, persona]))

export function getPersonaById(id: string) {
  return personaById.get(id) ?? null
}
