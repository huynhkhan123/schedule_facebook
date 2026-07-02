import { getBackendApiUrl } from '@/lib/api/client'

type RouteContext = {
  params: Promise<{
    path: string[]
  }>
}

async function proxyRequest(request: Request, context: RouteContext) {
  const { path } = await context.params
  const sourceUrl = new URL(request.url)
  const targetUrl = new URL(getBackendApiUrl(`/api/${path.join('/')}`))
  targetUrl.search = sourceUrl.search

  const body = request.method === 'GET' || request.method === 'HEAD' ? undefined : await request.text()
  const response = await fetch(targetUrl, {
    method: request.method,
    headers: {
      'content-type': request.headers.get('content-type') ?? 'application/json',
    },
    body,
    cache: 'no-store',
  })

  const responseBody = await response.text()

  return new Response(responseBody, {
    status: response.status,
    headers: {
      'content-type': response.headers.get('content-type') ?? 'application/json',
    },
  })
}

export async function GET(request: Request, context: RouteContext) {
  return proxyRequest(request, context)
}

export async function POST(request: Request, context: RouteContext) {
  return proxyRequest(request, context)
}

export async function PATCH(request: Request, context: RouteContext) {
  return proxyRequest(request, context)
}
