import http from 'node:http'
import https from 'node:https'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import dotenv from 'dotenv'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
dotenv.config({ path: path.join(__dirname, '.env') })

const PORT   = Number(process.env.PORT || 8787)
const TOKEN  = (process.env.BEARER_TOKEN || '').trim()

// === Telegram config (hardcoded — only this server uses these) ===
const TG_BOT_TOKEN = '8609798183:AAGcIIm_cSnLQRFtlYCaH9A5gaE6P86scGA'
const TG_CHANNEL   = '@AgentToWest'

// === Helpers ===

/** Escape MarkdownV2 special characters per Telegram Bot API spec */
function escapeMd(text) {
  return String(text).replace(/[_*[\]()~`>#+\-=|{}.!]/g, '\\$&')
}

async function readBody(req) {
  const chunks = []
  for await (const c of req) chunks.push(c)
  return Buffer.concat(chunks).toString('utf8').trim()
}

/** Call Telegram Bot API method with JSON body */
function telegramRequest(method, body) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body)
    const url = new URL('https://api.telegram.org/bot' + TG_BOT_TOKEN + '/' + method)
    const req = https.request({
      hostname: url.hostname,
      path: url.pathname,
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) }
    }, res => {
      let chunks = []
      res.on('data', c => chunks.push(c))
      res.on('end', () => {
        try { resolve(JSON.parse(Buffer.concat(chunks).toString())) }
        catch (e) { reject(e) }
      })
    })
    req.on('error', reject)
    req.write(data)
    req.end()
  })
}

// === Server ===

const server = http.createServer(async (req, res) => {
  const send = (code, obj) => {
    res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8' })
    res.end(JSON.stringify(obj, null, 2))
  }

  // --- Health check ---
  if (req.method === 'GET' && req.url === '/health') {
    res.writeHead(200); return res.end('ok')
  }

  // --- POST /publish: raw text → DeepSeek format → WeChat draft ---
  if (req.method === 'POST' && req.url === '/publish') {
    const auth = req.headers['authorization'] || ''
    if (!TOKEN)          return send(500, { error: '未设置 BEARER_TOKEN' })
    if (auth !== 'Bearer ' + TOKEN) return send(401, { error: 'unauthorized' })

    const rawText = await readBody(req)
    if (!rawText)        return send(400, { error: '内容为空' })

    console.log('[pub] ' + new Date().toISOString() + ' 收到文章 ' + rawText.length + ' 字')
    try {
      const { formatArticle } = await import('./deepseek.js')
      const { createDraft }   = await import('./wechat.js')
      const article = await formatArticle(rawText)
      console.log('[pub] DeepSeek 排版完成:', article.title)
      const mediaId = await createDraft(article)
      console.log('[pub] 草稿已创建 media_id:', mediaId)
      return send(200, { ok: true, title: article.title, media_id: mediaId })
    } catch (e) {
      console.error('[pub] 错误:', e.message)
      return send(502, { ok: false, error: e.message, errcode: e.errcode })
    }
  }

  // --- POST /push_telegram: JSON → MarkdownV2 → Telegram channel ---
  if (req.method === 'POST' && req.url === '/push_telegram') {
    const auth = req.headers['authorization'] || ''
    if (!TOKEN)          return send(500, { error: '未设置 BEARER_TOKEN' })
    if (auth !== 'Bearer ' + TOKEN) return send(401, { error: 'unauthorized' })

    try {
      const body = await readBody(req)
      if (!body) return send(400, { error: '内容为空' })

      const { title, excerpt, wp_link, wx_url, mp_name } = JSON.parse(body)
      if (!title) return send(400, { error: '缺少 title 字段' })

      const excerptText = (excerpt || '').substring(0, 200)
      const moreSuffix = (excerpt && excerpt.length > 200) ? '...' : ''
      const mpText = mp_name || '中本笨-BG'

      let message = '📝 *' + escapeMd(title) + '*\n\n' + escapeMd(excerptText) + moreSuffix + '\n\n'
      if (wp_link)  message += '🔗 ' + escapeMd(wp_link) + '\n'
      if (wx_url)   message += '📱 ' + escapeMd(wx_url) + '\n'
      message += '📢 微信公众号：' + escapeMd(mpText)

      console.log('[tg] ' + new Date().toISOString() + ' 推送TG: ' + title)

      const result = await telegramRequest('sendMessage', {
        chat_id: TG_CHANNEL,
        text: message,
        parse_mode: 'MarkdownV2',
        disable_web_page_preview: true
      })

      if (result.ok) {
        console.log('[tg] 推送成功 msg_id:', result.result?.message_id)
        return send(200, { ok: true, message_id: result.result?.message_id })
      } else {
        console.error('[tg] 推送失败:', result.description)
        return send(502, { ok: false, error: result.description })
      }
    } catch (e) {
      console.error('[tg] 错误:', e.message)
      return send(502, { ok: false, error: e.message })
    }
  }

  // --- 404 fallback ---
  send(404, { error: 'not found' })
})

server.listen(PORT, '0.0.0.0', () =>
  console.log('[wx-publisher] 监听 0.0.0.0:' + PORT + '  POST /publish  POST /push_telegram  GET /health'))
