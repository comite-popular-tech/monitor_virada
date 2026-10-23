// monitor.boralula.org → o painel de produção no Cloud Run, com o endereço do boralula na barra do navegador.
//
// O Cloud Run só responde pelo próprio host (*.run.app), e no plano Free a Cloudflare não troca o Host numa regra de
// origem. Então o Worker refaz o pedido para ORIGEM, com o mesmo caminho, query, método e corpo.
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origem = new URL(env.ORIGEM);
    const headers = new Headers(request.headers);
    headers.delete("host");
    headers.set("x-forwarded-host", url.host);

    const resposta = await fetch(new URL(url.pathname + url.search, origem), {
      method: request.method,
      headers,
      body: request.body,
      redirect: "manual",
    });

    // Um redirecionamento do painel para ele mesmo volta para o endereço do boralula
    const local = resposta.headers.get("location");
    if (!local) return resposta;
    const destino = new URL(local, origem);
    if (destino.host !== origem.host) return resposta;
    const saida = new Response(resposta.body, resposta);
    saida.headers.set("location", url.origin + destino.pathname + destino.search + destino.hash);
    return saida;
  },
};
