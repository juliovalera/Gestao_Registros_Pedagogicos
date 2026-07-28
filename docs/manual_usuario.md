# Manual do Usuário - Gestão de Registros Pedagógicos

Este manual apresenta um fluxo simples e acolhedor para uso diário do sistema em contextos pedagógicos.

Versão atual do sistema: `1.006`

## Finalidade

O sistema foi criado para registrar, consultar e analisar intercorrências diárias, ausências de professores e rotinas docentes no contexto pedagógico escolar, de forma totalmente local.

## Versionamento

O sistema passa a utilizar uma numeração sequencial simples de versão.

- versão inicial formal: `1.001`
- ajuste da ordem visual dos campos no cadastro de rotina docente: `1.002`
- contexto de atuação obrigatório no cadastro de rotina docente: `1.003`
- inclusão da categoria `Manutenção e/ou Limpeza` no cadastro de rotina docente: `1.004`
- sugestão automática de data e hora inicial com base no último registro: `1.005`
- contexto de atuação obrigatório, reposicionado e sugerido automaticamente nas intercorrências: `1.006`
- cada nova implementação ou correção acrescenta `0.001`

Exemplo:

- `1.001`
- `1.002`
- `1.003`
- `1.004`
- `1.005`
- `1.006`
- `1.007`

Créditos:

Professor Júlio César Valera  
Professor de Matemática, Programação e Robótica  
Registros Pedagógicos - Ribeirão Preto

## Como iniciar

1. Abra o terminal na pasta do projeto.
2. Execute:

```bash
python main.py
```

Na primeira execução, o banco SQLite local será criado automaticamente.

## Acesso ao sistema

Antes de abrir a tela principal, o sistema exige usuário e senha.

No primeiro uso:

1. Clique em `Criar primeiro usuário`.
2. Informe nome, usuário e senha.
3. Faça login com a conta criada.

Depois do acesso:

- use o menu `Segurança` para alterar a senha
- use `Trocar usuário` quando precisar encerrar a sessão atual

## Fluxo sugerido de uso

1. Abra `Cadastros básicos` e revise professores, espaços e tipos de ocorrência.
2. Use `Nova intercorrência` para registrar fatos objetivos do cotidiano.
3. Use `Registrar ausência de professor` para faltas, atrasos ou saídas antecipadas.
4. Use `Rotina docente` para registrar diário de classe, planejamento, estudo, preparação de material e demais atividades profissionais.
5. Acesse `Consultar registros` para aplicar filtros combinados.
6. Gere relatórios em `Relatório do dia`, `Relatório por período`, `Relatório por professor` e `Relatório por espaço`.
7. Faça backup periódico do banco local.

## Cadastros básicos

### Professores

- Cadastre nome completo, nome curto, área de atuação, vínculo e situação.
- Não exclua professores antigos se eles fizerem parte do histórico.
- Quando alguém deixar de atuar na unidade, altere apenas a situação para `inativo`, `afastado`, `removido` ou `contrato encerrado`.

### Espaços

- Cadastre ou edite espaços de atuação.
- Espaços podem ser inativados sem apagar o histórico.

### Tipos de ocorrência

- Cadastre categorias objetivas de registro.
- Defina uma gravidade padrão para agilizar o preenchimento das intercorrências.

## Registro de intercorrências

Campos obrigatórios mínimos:

- data
- hora
- tipo de ocorrência
- espaço
- descrição objetiva

Boas práticas:

- Registre fatos observáveis.
- Informe data, horário, local, pessoas relacionadas e providências adotadas.
- Evite julgamentos pessoais e termos acusatórios.
- Use tags para facilitar buscas futuras.

## Registro de ausência de professor

Campos obrigatórios mínimos:

- data
- professor
- espaço
- tipo de ausência
- impacto observado ou observações

O nome do professor é escolhido em lista suspensa, usando apenas professores ativos cadastrados.

Quando a ausência corresponder ao período inteiro, marque a opção `Ausência integral`.
Nesse caso, os campos de hora início e hora fim são desativados e os relatórios passam a indicar claramente essa condição.

## Registro de rotina docente

O módulo `Rotina docente` foi pensado para documentar a rotina profissional do professor ao longo do dia.

Exemplos de uso:

- diário de classe
- planejamento de aula
- estudo e formação
- preparação de material
- correção e avaliação
- atendimento a estudantes
- reunião pedagógica
- projeto, oficina ou laboratório
- registros administrativos

Campos obrigatórios:

- data
- professor
- categoria
- título
- descrição da atividade

Campos complementares:

- hora início
- hora fim
- espaço
- turma ou público
- objetivos
- recursos utilizados
- encaminhamentos
- tags
- observações

Use esse módulo para organizar evidências de trabalho, preparar sínteses para coordenação e manter um histórico cronológico das ações pedagógicas.

## Consultas e filtros

O módulo de consultas permite combinar filtros como:

- professor + período
- espaço + período
- tipo de ocorrência + período
- palavra-chave + período
- ausências por professor + período
- rotinas docentes por professor + período
- rotinas docentes por categoria + período
- registros de maior gravidade + período

Também há resumo estatístico por período.

Nos campos de data, o sistema:

- formata automaticamente no padrão `DD/MM/AAAA`
- oferece o botão `Cal` para escolher a data no calendário local

Nos campos de hora, o sistema formata automaticamente no padrão `HH:MM`.

## Relatórios

Os relatórios podem ser visualizados em tela e exportados em:

- TXT
- CSV
- PDF, se a biblioteca `reportlab` estiver instalada

Os relatórios reúnem, conforme o filtro aplicado:

- intercorrências
- ausências de professores
- rotinas docentes

Isso permite gerar material consolidado para acompanhamento interno e apresentação à coordenação.

## Backup

- Use o módulo `Backup` para gerar cópias de segurança do banco local.
- A restauração substitui o banco atual pela cópia escolhida.
- Recomenda-se manter cópias em pasta segura e externa ao computador principal quando possível.
- Lembre que o backup também preserva os usuários e senhas vigentes naquele banco.

## Cuidados éticos, privacidade e LGPD

- Registre fatos profissionais, objetivos e cronológicos.
- Evite acusações, diagnósticos médicos ou exposição desnecessária de dados sensíveis.
- Evite identificação completa de crianças e adolescentes.
- Prefira registros como `estudante A`, `grupo do 9º ano`, `turma visitante` ou iniciais.
- Descreva o que foi observado, quem presenciou e qual providência foi adotada.

Exemplo preferível:

`Não compareceu ao espaço no horário previsto, conforme observado, e a situação foi comunicada à coordenação.`

## Encerramento

Se algum módulo apresentar erro, feche apenas a janela atual e tente novamente. O sistema foi estruturado para tratar falhas sem encerrar a aplicação inteira sempre que possível.
