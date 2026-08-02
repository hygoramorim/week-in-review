# A regra do 1%: o teste que Jeff Dean usa para saber se vale a pena construir em IA

Existe uma pergunta simples que separa quem está perdendo tempo de quem está prestes a construir algo relevante em inteligência artificial: o modelo geral resolve esse problema 20% das vezes, ou 0% a 1%? A resposta parece contraintuitiva. Jeff Dean, cientista chefe do Google e uma das pessoas que desenhou a infraestrutura que roda a internet moderna (MapReduce, BigTable, TensorFlow, TPU, Gemini), disse isso numa conversa recente com Diana Hu, da Y Combinator, na Startup School 2026. Se um modelo já acerta 20% de um problema, ele vai continuar melhorando ali com mais dados e mais escala, e qualquer empresa que aposte nesse nicho está construindo em cima de areia movediça. Mas se o modelo erra quase tudo, isso é sinal de uma capacidade ainda ausente, um território onde um time pequeno, com dados certos ou um modelo especializado, pode abrir uma vantagem real.

Essa regra do 1% não é só uma dica de posicionamento de produto. É a lente que Dean usa desde os anos 2000 para escolher em que apostar, e a mesma lente que produziu o MapReduce, o TPU e a técnica de destilação de modelos que hoje sustenta praticamente toda a indústria de IA.

## O napkin math como disciplina, não como sorte

Dean é famoso por suas contas de guardanapo, e a entrevista traz dois exemplos que não são anedotas de sorte: são metodologia repetível.

Em 2001, ele e Sanjay Ghemawat perceberam que o índice de busca do Google, que até então rodava em disco, logo caberia inteiro na memória RAM de todos os servidores da empresa. Fizeram a conta, viram que o momento estava próximo, e em poucos dias colocaram em produção uma versão inteiramente nova da busca, agora rodando em RAM. Foi esse salto que tornou o Google rápido do jeito que conhecemos.

Em 2013, outra conta de guardanapo: se cada usuário do Google usasse reconhecimento de voz por apenas três minutos por dia, a empresa precisaria dobrar sua frota inteira de servidores só para sustentar a demanda. Os novos modelos de fala baseados em deep learning eram tão melhores (o equivalente a vinte anos de avanço em poucos meses) que Dean sabia que, se funcionassem bem, o uso explodiria. Rodar isso em CPU seria financeiramente inviável. A resposta foi construir um chip especializado só para álgebra linear densa de baixa precisão, o núcleo de praticamente todo algoritmo de machine learning. Nasceu o TPU, de 30 a 80 vezes mais eficiente em energia e de 20 a 30 vezes mais rápido que CPUs e GPUs da época.

O padrão que conecta os dois casos é o mesmo: não é prever o futuro, é fazer a aritmética do presente até ela ficar desconfortável. Quando a conta mostra que a demanda vai superar a capacidade por uma ou duas ordens de grandeza, ali mora a oportunidade de construir algo consequente. É o oposto de acompanhar hype: é sentar com os números reais de uso, custo e energia e deixá-los apontar o problema.

## Energia é a métrica que ninguém está olhando

Um dos pontos mais reveladores da conversa é quando Dean explica por que, hoje, a unidade de medida que realmente importa em sistemas de IA não é FLOPs nem número de parâmetros: é energia. Fazer uma operação matemática custa cerca de um picojoule. Mover esse mesmo dado da memória de alta largura de banda (HBM) até o processador para computá-lo custa mil vezes mais.

Essa diferença de mil vezes não é um detalhe técnico obscuro, ela dita decisões de produto inteiras. É por isso que existe batching (agrupar exemplos ou tokens antes de processar): sem agrupar, se paga o custo total de mover dados a cada operação; agrupando, esse custo se diluí pelo tamanho do lote. O problema é que batching também aumenta latência, e para aplicações que exigem resposta instantânea, esse é um trade-off direto entre custo de energia e experiência do usuário.

Dean está pessoalmente obcecado com o lado da inferência desse problema, não o de treinamento. Treinamento tolera alguma latência; inferência, cada vez mais, não tolera nenhuma. Se você souber exatamente qual precisão numérica seu sistema precisa, pode construir um chip que só faz aquilo, sem generalidade nenhuma, e ganhar ordens de magnitude em eficiência: foi essa mesma aposta que criou o TPU original. A profecia dele para os próximos anos é hardware de inferência especializado, com latência até 50 vezes menor que a atual, uma mudança capaz de tornar viáveis produtos que hoje não fazem sentido econômico.

## Context engineering: a democratização que ninguém percebeu

Se treinar modelos exige GPUs, dados em escala e capital que só um punhado de empresas possui, existe uma camada inteira do problema que qualquer pessoa com acesso a uma API pode disputar: o que Dean chama de "context engineering". É tudo que envolve dar ao modelo as ferramentas certas, a memória certa, os documentos certos no momento certo, e ensinar a ele, por meio de instruções bem escritas ("skills", no vocabulário dele), como sequenciar chamadas de ferramentas para resolver um problema complexo.

O exemplo que ele dá é revelador pela simplicidade: ele e Sanjay Ghemawat escreveram uma "skill" que ensina um agente a fazer, sozinho, o ciclo completo de otimização de performance que os dois fariam manualmente (medir benchmark, alterar código, remedir, comparar footprint de cache, iterar). Não mudaram o modelo. Deram a ele, em texto, o método que dois dos melhores engenheiros de sistemas do mundo usam. Esse documento, batizado de "performance hints", tem cerca de trinta páginas e está publicamente disponível.

Essa é talvez a virada mais prática da entrevista: a vantagem competitiva não está mais garantida só a quem treina o modelo maior, está também disponível a quem escreve o contexto mais preciso, sem esperar pela próxima rodada de investimento em GPUs.

## Onde o pequeno ainda vence o Google

Perguntado diretamente sobre em que camadas um time de duas ou três pessoas ainda consegue competir com uma empresa que controla desde o processador até o produto, Dean foi específico: modelos gerais como o Gemini são otimizados para fazer quase tudo razoavelmente bem, o que deixa espaço para quem constrói algo estreito, bem desenhado e extremamente preciso num domínio específico. Duas rotas concretas: produtos com acesso a dados que o modelo geral simplesmente não enxerga (as informações pessoais de um usuário, por exemplo), ou modelos especializados e baratos de treinar para um problema estreito. Ele cita o AlphaFold, da própria Google DeepMind, como exemplo canônico de um modelo não generalista que resolveu uma classe de problema (dobra de proteínas) melhor que qualquer modelo geral jamais faria.

A ressalva importante: isso é uma corrida contra o tempo. Antes de investir num nicho, é preciso perguntar se os modelos de fronteira vão engolir aquela capacidade em seis meses, doze meses, ou se é algo que resiste por dois ou três anos. É a mesma regra do 1% aplicada ao horizonte temporal, não só à taxa de acerto atual.

## O fio que une tudo

Há uma ironia no fato de que o mesmo homem que ajudou a construir a infraestrutura mais centralizada e poderosa da história da computação está, nessa conversa, ensinando fundadores a encontrar as frestas onde essa infraestrutura ainda não chega. Mas faz sentido: Dean não fala como quem defende o tamanho do Google, fala como quem passou a carreira caçando o lugar exato onde a aritmética simples revela um problema que ninguém mais está vendo. O MapReduce nasceu de espremer a complexidade de paralelização para fora do código de negócio. A destilação de modelos, hoje onipresente na indústria (inclusive nos próprios modelos "flash" do Gemini), nasceu de um paper rejeitado por um revisor que achou que não teria "impacto significativo". A lição prática, para quem constrói produtos de IA em 2026, não é copiar as ferramentas do Google. É copiar o método: fazer a conta, respeitar a energia como métrica final, escrever o contexto com o mesmo rigor de quem escreveria código, e procurar os lugares onde o modelo geral ainda falha quase por completo.
