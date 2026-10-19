# Metodologia

## Por que grupos e âncora

O Google Trends não devolve volume de buscas. Ele devolve um **índice de 0 a 100** que é relativo a tudo o que entrou na mesma consulta: o maior valor da consulta vira 100 e o resto é proporcional a ele. Duas consultas diferentes **não** podem ser comparadas diretamente.

Como cada consulta aceita no máximo 5 termos e monitoramos 37, os termos foram divididos em grupos, e **todo grupo leva o mesmo termo-âncora: "bolsa família"**. A âncora tem volume alto e estável no Brasil todo, então serve de régua comum:

```
indice_vs_ancora = valor do termo / valor de "bolsa família" no mesmo local × 100
```

Exemplo: em Campinas, `inss = 30` e `bolsa família = 40` → `indice_vs_ancora = 75`. Ou seja, buscaram "inss" 75% do que buscaram "bolsa família". Esse número pode ser comparado entre grupos, entre locais e entre dias.

| Grupo | Termos (+ âncora) |
|---|---|
| G1 | inss, aposentadoria, posto de saúde, creche |
| G2 | ubs, escola pública, bpc loas, merenda escolar |
| G3 | mais médicos, saúde da família, escola em tempo integral, dinheiro direto na escola |
| G4 | brasil sorridente |
| CAND | lula, flávio bolsonaro, bolsonaro |
| ATQ_LULA_1 | roberta luchsinger, luchsinger, lulinha, filho do lula |
| ATQ_LULA_2 | filho lula bateu, lula lobista, lula socio, lula vorcaro |
| ATQ_FLAVIO_ORG_1 | 134 milhoes, flavio vorcaro, inimigo do trabalhador, privatizar o sus |
| ATQ_FLAVIO_ORG_2 | lottenberg, flavio 6x1 |
| ATQ_FLAVIO_PUSH_1 | flavio miliciano, flavio ana clara, flavio comando vermelho, bolsonaro miliciano |
| ATQ_FLAVIO_PUSH_2 | armas bolsonaro, inflacao bolsonaro |

Os grupos misturam macrotemas de propósito: termos de volume parecido ficam juntos, o que evita que um termo muito grande achate os outros em zero.

### Macrotemas

- **Saúde:** posto de saúde, ubs, mais médicos, saúde da família, brasil sorridente
- **Educação:** escola pública, creche, merenda escolar, dinheiro direto na escola, escola em tempo integral
- **Aposentadoria e renda:** aposentadoria, inss, bpc loas, bolsa família
- **Candidatos:** lula, flávio bolsonaro, bolsonaro
- **ATQ_LULA / ATQ_FLAVIO_ORG / ATQ_FLAVIO_PUSH:** termos de ataque, grafados como foram definidos (sem acento). O Trends costuma juntar variações com e sem acento, mas não é garantido; se um termo vier zerado em todo lugar, teste a grafia acentuada.
- Os macrotemas de ataque ficam fora das buscas relacionadas (`macrotemas_relacionadas` em `config/termos.yaml`).

## Recortes geográficos

- **Estados** (`geo=BR`, `region=REGION`): uma linha por UF.
- **Cidades** (`geo` = cada um dos 27 estados, `region=CITY`, incluindo locais de baixo volume): todas as cidades que o Google devolver em cada estado, para os 11 grupos.
  - Cada cidade é cruzada com `config/cidades_segmentacao.csv` (1.794 cidades: RM SP, interior PR, interior SC, GO, MG) por UF + nome sem acento. Quando bate, a linha recebe `cod_tse`, `recorte`, `segmento`, `porte` e `rank_no_segmento_recorte`, e `cidade_alvo = true`.
  - Campinas, Ribeirão Preto, Sorocaba, São José dos Campos e São José do Rio Preto também ficam com `cidade_alvo = true`, sem dados de segmentação.
  - Cidades que não estão em nenhuma das duas listas ficam com `cidade_alvo = false` (por exemplo, Curitiba e Florianópolis, que estão fora dos recortes de interior).
  - O Google só devolve cidades com volume mínimo de buscas: boa parte das cidades pequenas vai aparecer vazia ou não aparecer. Os termos de ataque têm volume baixo, então espere zeros na maioria das cidades e sinal concentrado nas capitais e cidades grandes.
- **Buscas relacionadas** (`geo=BR`): Brasil todo. Candidatos com janela de 1 dia (`now 1-d`) para pegar o assunto do dia; temas com 7 dias.

## Como ler os números

- `valor` (0-100): só faz sentido **dentro da mesma consulta, no mesmo dia**.
- `indice_vs_ancora`: compare à vontade entre termos, locais e dias. Acima de 100 = mais buscado que "bolsa família".
- Valor 0 ou vazio = volume abaixo do mínimo que o Google publica. Em cidades pequenas isso é comum e **não** significa zero buscas.
- **Buscas relacionadas, lista "em alta":** `Breakout` = crescimento acima de 5.000%; `+250%` = crescimento no período. São os melhores sinais de assunto novo (ex.: "flávio bolsonaro inss" subindo).
- Janela padrão `now 7-d`: cada coleta diária mostra os últimos 7 dias. A variação de um dia para o outro mostra a tendência; o valor isolado é uma média da semana.

## Limitações

- O Trends é uma amostra das buscas do Google, não uma pesquisa de opinião. Mostra **interesse**, não apoio.
- Termos ambíguos ("creche", "aposentadoria") somam buscas de todo tipo, não só de política.
- Cada estado em `geos` do job `cidades` custa 11 buscas/dia. Para economizar, tire estados da lista.
- Mudar termos ou grupos no meio do período quebra a comparação com os dias anteriores. Se precisar mudar, anote a data.

## Orçamento (plano atual)

| Item | Cálculo | Buscas de 19/10 a 24/10 |
|---|---|---|
| Estados | 11 grupos × 6 dias | 66 |
| Cidades (27 estados) | 11 grupos × 27 estados × 6 dias | 1.782 |
| Relacionadas candidatos | 3 × 6 dias | 18 |
| Relacionadas temas | 14 × 2 coletas (19 e 22/10) | 28 |
| **Total** | | **1.894** |

Por dia: 311 buscas (325 em 19 e 22/10). Exige plano pago. O script usa o menor valor entre o limite da conta e `limite_por_hora` (1000); com um plano de 50/h, a coleta para e retoma na hora seguinte.
