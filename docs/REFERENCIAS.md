# Referências e registro de apoio

## Fontes disponíveis

- **Código original:** `FakeNews.py`, fornecido pelo professor no enunciado do trabalho. Cópia preservada na raiz. Completar nome do docente, disciplina e data do material antes da entrega.
- **Python Software Foundation. threading — Thread-based parallelism.** https://docs.python.org/3/library/threading.html — threads, sincronização e limitações do GIL em tarefas de CPU.
- **Python Software Foundation. Socket Programming HOWTO.** https://docs.python.org/3/howto/sockets.html — TCP, envio/recebimento parcial e delimitação de mensagens.

Essas referências técnicas foram registradas na organização inicial. A seção seguinte acrescenta uma fonte acadêmica consultada na revisão e explicita sua relação com o modelo. A equipe deve ler as fontes e distinguir contextualização posterior das decisões do desenvolvimento original.

## Fontes consultadas na revisão de 19/11/2026

- **Python Software Foundation. concurrent.futures — Launching parallel tasks.** https://docs.python.org/3/library/concurrent.futures.html — fundamenta a execução explícita de tarefas em threads, a propagação de exceções por `Future.result()` e a espera pelo encerramento do executor. A revisão usa esses recursos para sincronizar cada geração sem a barreira interna redundante.
- **Python Software Foundation. Socket Programming HOWTO.** https://docs.python.org/3/howto/sockets.html — fundamenta o protocolo TCP com enquadramento, envio completo e leitura em laço; orienta a distinção entre comunicação local e entre hosts.
- **CHEN, Xuelong; WANG, Nan.** Rumor spreading model considering rumor credibility, correlation and crowd classification based on personality. *Scientific Reports*, v. 10, artigo 5887, 2020. DOI: https://doi.org/10.1038/s41598-020-62585-9. Texto: https://pmc.ncbi.nlm.nih.gov/articles/PMC7125100/.

O artigo discute diferenças individuais na disposição para propagar rumores e modelos com classes de ignorantes, espalhadores e indivíduos que deixam de espalhar. Serve como contextualização teórica para a heterogeneidade e a resistência do modelo didático. O projeto não reproduz as equações nem a validação empírica desse artigo. O peso 3 dos influenciadores e a resistência extra 2 são escolhas demonstrativas da implementação, não valores derivados da publicação. A influência diferenciada é uma hipótese exploratória do grupo.

As fontes acima foram consultadas como apoio à revisão posterior à implementação. A equipe deve lê-las antes de usá-las na apresentação; não se afirma que fundamentaram o desenvolvimento original dos colegas. A estatística por geração registra a evolução dos três estados e permite comparar os efeitos dos parâmetros, sem acrescentar uma regra de transição ao modelo básico.

## Uso de IA generativa — histórico e revisão

ChatGPT/Codex foi utilizado como apoio na organização inicial do repositório, redação do README e guias, interpretação do contrato e proposta inicial de arquitetura distribuída. O código original foi preservado e executado para conferir o cenário padrão.

Cada integrante deve registrar apoios adicionais, o que foi aproveitado, adaptações e validação humana. A equipe deve revisar a documentação e compreender todas as implementações, limitações e resultados apresentados.

## Coleta de hardware no Windows — revisão dos experimentos

Microsoft Learn. GetLogicalProcessorInformationEx: https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getlogicalprocessorinformationex. A consulta RelationProcessorCore retorna os núcleos ativos; a implementação percorre registros de tamanho variável, sem deduzir núcleos físicos dos processadores lógicos.

Microsoft Learn. GlobalMemoryStatusEx: https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-globalmemorystatusex. Usado para registrar memória física total visível ao sistema. O nome da CPU é lido do registro do Windows; campos indisponíveis permanecem desconhecidos.
