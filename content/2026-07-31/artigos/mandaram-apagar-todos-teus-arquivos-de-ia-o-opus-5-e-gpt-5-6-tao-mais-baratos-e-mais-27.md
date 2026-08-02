# A tentação de apagar tudo: por que o conselho viral sobre IA está errado (e o que fazer no lugar)

Essa semana dois modelos de IA ficaram mais baratos, um deles ficou (talvez) mais burro, e um vídeo de dois minutos convenceu meio Twitter a apagar meses de trabalho de configuração. Os três fatos parecem desconectados, mas não são: eles apontam para o mesmo problema, que é a tentação de tratar cada novo lançamento como um botão de reset em vez de uma peça a mais no sistema.

## O trechinho viral e o que ele omitia

Um clipe da entrevista de Boris Cherny, um dos responsáveis pelo Claude Code, circulou nesta semana com uma frase que virou clickbait instantâneo: se você usa o produto há mais de seis meses, apague seu arquivo de instruções, apague suas skills, apague seus hooks, e veja como o modelo se comporta sem eles. Muita gente recebeu esse clipe na comunidade e entrou em pânico, cogitando zerar meses de configuração acumulada.

O problema é que o clipe corta a frase seguinte. Cherny completa dizendo que, depois de apagar, é preciso trazer as instruções de volta linha por linha, testando cada uma, para entender o que realmente ainda faz diferença com os modelos novos. A recomendação não é "delete e siga sem nada". É "delete, teste metodicamente, e reconstrua só o que se prova necessário". São duas ideias radicalmente diferentes, e a internet ficou só com a primeira porque é a que rende visualização.

Isso importa porque descreve exatamente como desinformação técnica se espalha hoje: não por mentira deliberada, mas por corte de contexto. Um especialista fala uma frase de efeito seguida de uma ressalva, o clipe pega só o efeito, e quem nunca assistiu à entrevista completa reage à frase isolada como se fosse o conselho inteiro.

## Por que a ideia de "apagar tudo" tinha lastro real

O motivo de o corte ter viralizado não é acaso. Há uma mudança real acontecendo: os modelos mais recentes vieram com o texto de instruções internas (o chamado *system prompt*, que é basicamente o manual de comportamento que o modelo lê antes de qualquer conversa) reduzido em torno de 80%. A leitura por trás disso é que modelos mais capazes precisam de menos grade de proteção explícita: menos "faça isso, não faça aquilo" cravado no prompt, porque o modelo já infere o comportamento correto sozinho.

Se isso é verdade, faz sentido que parte das instruções acumuladas nos seus próprios arquivos de configuração também tenha virado peso morto, arrastando o modelo para comportamentos de uma geração anterior, mais burra, que precisava de regras explícitas para não errar o óbvio. Só que "parte das instruções pode ter virado peso morto" é uma tese que exige teste caso a caso. Não é o mesmo que "apague tudo e comece do zero", que é uma aposta cega no melhor cenário possível.

## O harness importa mais que o modelo

Essa semana também trouxe outra peça que se encaixa no mesmo raciocínio: analistas do mercado observaram que quem tem um ambiente de trabalho bem montado, pastas organizadas, um sistema claro de como o agente opera, sente pouca diferença ao trocar de modelo. Quem não tem essa estrutura sente cada lançamento como um terremoto, positivo ou negativo.

Isso é o oposto de tratar o arquivo de instruções como algo descartável a cada atualização de modelo. É tratar a estrutura como o ativo permanente e o modelo como a peça substituível. Na prática, o valor não está em qual modelo você usa numa terça-feira qualquer, está em ter um sistema robusto o bastante para que trocar de modelo, ou até perder acesso a um deles de uma hora para outra, não pare o seu trabalho. Essa semana teve relatos concretos disso: gente notando o modelo mais caro da Anthropic parecendo "piorar" dias depois do lançamento, possivelmente por limitação de capacidade de computação da empresa, e quem tinha alternativa pronta simplesmente trocou de ferramenta sem perder o dia.

## A guerra de preço muda o cálculo, não o princípio

No mesmo período, a OpenAI cortou o preço da sua versão mais barata de modelo em 80% e da versão intermediária em 20%, movimento que a colocou à frente de concorrentes em custo e velocidade combinados. Isso é ótimo para quem paga a conta no fim do mês, mas reforça o argumento estrutural: se o preço e a posição relativa dos modelos mudam a cada poucas semanas, apostar toda a sua produtividade em otimizar para um modelo específico é aposta perdedora. O jogo certo é permanecer agnóstico a qual modelo está por trás, e deixar a camada de organização (os arquivos, os processos, os hábitos de revisão) absorver essa volatilidade.

## O risco que fica escondido atrás do hype

Há um ponto que conecta tudo isso a algo mais sério do que preferência de configuração: dar autonomia demais a um agente sem supervisão é a receita para um desastre irreversível. O próprio episódio trouxe o exemplo do professor que escondeu instruções invisíveis num enunciado de prova, fazendo os alunos que colavam o texto direto na IA caírem numa armadilha detectável. Trinta e dois de trinta e cinco alunos caíram. É a mesma classe de vulnerabilidade, injeção de instrução escondida, que já apareceu em processos judiciais, com advogados tentando manipular decisões inserindo texto oculto em documentos.

A lição prática para quem usa agentes de IA em arquivos e sistemas reais é dupla. Primeiro, nunca dar a um agente permissão irrestrita de apagar, mover ou sobrescrever nada sem uma camada de revisão humana no meio, porque texto malicioso ou instrução ambígua pode chegar por qualquer canal, um e-mail colado, um enunciado, um arquivo compartilhado. Segundo, tratar qualquer sugestão de "resetar tudo" (seja vinda de um vídeo viral, seja vinda do próprio agente) com o mesmo ceticismo: teste em pedaço pequeno, valide, só depois generalize.

## A conclusão que fica

O fio que costura o episódio inteiro é que a inteligência artificial está ficando mais barata e mais capaz na mesma velocidade em que fica mais fácil errar feio com ela. Apagar toda a configuração acumulada por um clipe de dois minutos é o mesmo tipo de erro que dar permissão total de escrita e exclusão a um agente sem supervisão: os dois trocam disciplina por conveniência, e os dois só acertam com a versão inteira da história.

A pergunta que abriu o episódio, sobre o que sobra para o ser humano fazer quando a IA fica mais esperta e mais barata na mesma semana, tem uma resposta que já estava dada nos exemplos: sobra decidir o que atacar, sobra revisar o resultado com discernimento antes de aceitar, e sobra a responsabilidade de nunca terceirizar para um agente uma decisão que, se sair errada, não tem como desfazer.

---

*Análise produzida a partir do episódio #27 do canal Ratos de IA, disponível no [YouTube](https://www.youtube.com/watch?v=TWlxXayG2ZQ).*
