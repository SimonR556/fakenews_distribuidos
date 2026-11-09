# Guia de contribuição

## Branches

O padrão escolhido pelo time é `nome/arquivo-arquivo`. Usar nome ou identificador que diferencie integrantes com nomes iguais, minúsculas, sem acentos e sem `.py`. O segundo arquivo é opcional.

| Entrega | Exemplo de branch |
| --- | --- |
| Sequencial e testes | `nome/sequencial-testes` |
| Paralela | `nome/paralelo` |
| Distribuída | `thiago/distribuido-worker` |
| Benchmark | `nome/benchmark-resultados` |
| Melhorias | `nome/melhorias` |
| Documentação inicial | `thiago/readme-organizacao` |

Uma branch por entrega mantém a revisão pequena. Para uma correção futura, usar um sufixo descritivo, por exemplo `thiago/distribuido-fronteiras`.

## Fluxo de trabalho

Antes de começar, confira `git status` e salve seu trabalho. Com a árvore de trabalho limpa:

```bash
git switch main
git pull --ff-only origin main
git switch -c thiago/distribuido-worker
```

Depois de implementar e testar sua parte, adicione somente os arquivos da entrega:

```bash
git status
git diff
git add distribuido.py worker.py
git commit -m "feat: implementa coordenador e trabalhadores por sockets"
git push -u origin thiago/distribuido-worker
```

Os comandos acima são exemplos para Thiago, quando esses arquivos existirem. Cada integrante substitui branch, arquivos e mensagem. `commit` salva localmente; `push` publica os commits no GitHub.

No GitHub, abrir **Pull Request** da branch de trabalho para `main`. Preencher o modelo, relatar os testes efetivamente realizados e solicitar a revisão de outro integrante. Um PR incompleto pode ser aberto como rascunho. Após aprovação e integração, atualizar a `main` local e criar uma nova branch para a próxima entrega.

Não enviar alterações diretamente à `main`. Não fazer force push na branch compartilhada. Se `pull --ff-only` falhar, investigar a divergência antes de prosseguir. Combinar alterações em arquivos de outro integrante.

## Antes da revisão

- Preservar o contrato `simular` e a matriz recebida.
- Testar 5 × 5, 10 × 10 e 100 × 100; comparar com o original.
- Verificar fronteiras, divisão com sobra de linhas e sincronização por geração.
- Documentar comandos reais de execução, dependências e limitações.
- Registrar fontes externas e uso de IA; compreender o código entregue.
- Manter melhorias opcionais desativadas nos testes básicos.

Não versionar ambientes virtuais, caches, senhas ou `.env`. Dados e gráficos finais de experimentos devem ser versionados com seus parâmetros e identificação do código usado.
