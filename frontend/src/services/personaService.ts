import { getPersonaById, personas, type Persona } from '@/data/personas'

const replyTemplates: Record<string, string[]> = {
  paul_graham: [
    '我会先看这件事有没有足够强的问题定义，再考虑怎么做得更快。',
    '如果方向不清晰，先把最小可行的验证做出来，比长时间争论更有效。',
    '真正重要的是：这个想法能不能在小规模里先证明自己。',
  ],
  charlie_munger: [
    '先反过来想，看看最容易犯的错是什么，再决定要不要继续。',
    '如果一个选择带来太多不必要的复杂性，通常就该警惕了。',
    '别只看可能收益，也要看坏结果出现时你是否扛得住。',
  ],
  zhang_xue_feng: [
    '先看现实条件，再看理想预期，不然容易把自己绕进去。',
    '如果资源有限，就要优先把能落地的路径排前面。',
    '别先问“好不好听”，先问“能不能成”。',
  ],
  sun_justin: [
    '这件事如果想做出话题，关键不只是内容，还要看传播节奏和动作设计。',
    '商业上能不能跑出来，往往看叙事和执行是不是同频。',
    '先把抓眼球的切口定住，再去想后面的转化路径。',
  ],
}

export async function listPersonas(): Promise<Persona[]> {
  return personas
}

export async function loadPersona(id: string): Promise<Persona | null> {
  return getPersonaById(id)
}

export function buildMockReply(persona: Persona, userMessage: string): string {
  const templates = replyTemplates[persona.id] ?? [
    '我会先把问题拆成“目标、约束、选择”三部分，再往下看。',
    '如果只看表面，会漏掉真正影响结果的那一层。',
  ]
  const sample = templates[Math.abs(userMessage.length) % templates.length]
  return `${sample} 你刚刚提到的重点是「${userMessage.slice(0, 18)}${userMessage.length > 18 ? '…' : ''}」，我会优先从这个角度继续聊。`
}

export function getRecentSessionCards() {
  return [
    { personaId: 'paul_graham', title: '产品方向要不要重做？', time: '今天 09:12' },
    { personaId: 'charlie_munger', title: '怎么避免一次错误决策？', time: '昨天 18:40' },
    { personaId: 'zhang_xue_feng', title: '专业与就业怎么选？', time: '昨天 12:08' },
  ]
}
