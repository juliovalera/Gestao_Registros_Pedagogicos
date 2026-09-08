# Manual do Usuário - Gestão de Registros Pedagógicos

Este manual orienta o uso diário do sistema para registros pedagógicos, organização de informações, consultas, relatórios, backups e acompanhamento do Programa Multiplica.

Versão de referência do sistema: `1.059`

## Finalidade

O sistema funciona localmente, no próprio computador, e utiliza um banco de dados SQLite. Ele foi desenvolvido para registrar fatos da rotina pedagógica, preservar o histórico e produzir consultas e relatórios para acompanhamento profissional.

Principais áreas disponíveis:

- rotina docente
- cadastros básicos
- intercorrências, incluindo ausências de professores
- consultas e relatórios gerais
- backups do banco local
- Programa Multiplica

## Como iniciar

1. Abra o terminal na pasta do projeto.
2. Execute o comando:

```bash
python main.py
```

Na primeira execução, o banco de dados local é criado automaticamente na pasta `data/`.

## Acesso e segurança

O sistema exige usuário e senha antes de abrir a tela principal.

No primeiro uso:

1. Clique em `Criar primeiro usuário`.
2. Informe nome, nome de usuário e senha.
3. Faça login com a conta criada.

Depois do acesso:

- use `Segurança > Alterar senha` para atualizar a senha;
- use `Segurança > Trocar usuário` para encerrar a sessão atual;
- use `Segurança > Modo do Programa Multiplica` para vincular um professor e escolher o modo de uso do Programa Multiplica.

## Fluxo sugerido de uso

1. Revise os professores, espaços e tipos de ocorrência em `Cadastros básicos`.
2. Registre atividades profissionais em `Rotina docente`.
3. Registre fatos relevantes em `Nova intercorrência`.
4. Para faltas, atrasos ou saídas antecipadas, registre a intercorrência com o tipo `Ausência de professor`.
5. Use `Consultar registros` para localizar informações com filtros.
6. Gere relatórios gerais ou relatórios específicos do Programa Multiplica.
7. Crie backups regularmente, principalmente antes de mudanças importantes no computador ou no banco.

## Cadastros básicos

### Professores

Cadastre nome completo, nome curto, área de atuação, vínculo e situação.

- Mantenha professores antigos no cadastro quando fizerem parte do histórico.
- Para quem deixou de atuar na unidade, altere a situação para `inativo`, `afastado`, `removido` ou `contrato encerrado`.
- Professores não ativos aparecem destacados em vermelho nas listas, ajudando a diferenciar os registros históricos.

### Espaços

Cadastre os locais de atuação, como salas, laboratórios, coordenação ou outros ambientes da escola.

- Espaços podem ser inativados sem apagar registros anteriores.

### Tipos de ocorrência

Cadastre categorias objetivas para agilizar a rotina de registro.

- Defina a gravidade padrão de cada tipo quando for pertinente.
- O tipo `Ausência de professor` é o tipo oficial para registrar ausências.

## Registro de intercorrências

Use `Nova intercorrência` para registrar fatos objetivos do cotidiano escolar.

Campos mínimos:

- data
- hora, quando aplicável
- tipo de ocorrência
- espaço
- descrição objetiva

Boas práticas:

- registre fatos observáveis e cronológicos;
- informe local, pessoas relacionadas e providências adotadas;
- evite julgamentos pessoais e termos acusatórios;
- use tags e contexto de atuação para facilitar consultas futuras;
- adicione evidências em imagem somente quando forem úteis para consulta ou relatório.

## Ausência de professor: fluxo oficial

O registro oficial de ausência é feito dentro de `Nova intercorrência`.

1. Abra `Nova intercorrência`.
2. Em `Tipo de ocorrência`, escolha `Ausência de professor`.
3. Preencha os campos específicos exibidos para a ausência.
4. Salve a intercorrência.

Os campos específicos permitem registrar, conforme necessário:

- professor relacionado;
- ausência integral ou horários de início e fim;
- contexto de atuação;
- turma ou grupo afetado;
- tipo de ausência;
- comunicação prévia;
- substituição;
- impacto observado;
- providência tomada;
- observações.

Quando a ausência for do período inteiro, marque `Ausência integral`. Os horários deixam de ser necessários e os relatórios indicam essa condição.

Importante: não use registros paralelos para a mesma ausência. Os relatórios de ausências usam as intercorrências do tipo `Ausência de professor`, inclusive os registros antigos que foram migrados com segurança.

## Rotina docente

Use `Rotina docente` para registrar o trabalho profissional realizado ao longo do dia.

Exemplos:

- diário de classe;
- planejamento de aula;
- estudo e formação;
- preparação de material;
- correção e avaliação;
- atendimento a estudantes, famílias ou professores;
- reunião pedagógica;
- projetos, oficinas e laboratórios;
- registros administrativos.

Campos obrigatórios:

- data;
- professor ou professores;
- categoria;
- título;
- descrição da atividade.

Campos complementares incluem horários, espaço, turma ou público, objetivos, recursos, encaminhamentos, tags, observações e evidências em imagem.

## Datas, horas e listas

Nos campos de data:

- digite no formato `DD/MM/AAAA`;
- use o botão com ícone de calendário para escolher uma data;
- o calendário destaca a data atual, feriados nacionais e, no Programa Multiplica, o dia configurado para a turma selecionada.

Nos campos de hora, use o formato `HH:MM`.

Em listas suspensas, digite as primeiras letras para localizar opções mais rapidamente quando o campo estiver selecionado.

## Consultas e análise

Use `Consultar registros` para localizar informações por filtros combinados, como:

- professor e período;
- espaço e período;
- tipo de ocorrência e período;
- palavra-chave e período;
- contexto de atuação;
- ausências por professor;
- rotinas docentes por professor ou categoria;
- registros por gravidade.

O módulo também apresenta indicadores e gráficos locais para apoiar a análise do período selecionado.

## Relatórios gerais

Os atalhos da tela inicial permitem abrir relatórios do dia, por período, por professor e por espaço.

Os relatórios gerais podem reunir, conforme os filtros usados:

- intercorrências;
- ausências de professores;
- rotinas docentes.

As exportações gerais podem ser feitas em TXT, CSV e PDF. A exportação em PDF depende da biblioteca `reportlab` instalada.

## Programa Multiplica

### Configuração do modo

Abra `Segurança > Modo do Programa Multiplica` e selecione um professor vinculado ao usuário.

Escolha apenas um modo:

- `Professor multiplicador`: para acompanhar turmas, cursistas e encontros conduzidos;
- `Professor cursista`: para identificar o professor que recebe formações;
- `Uso geral`: mantém o sistema sem um papel específico no Programa Multiplica.

Um professor não deve ser configurado simultaneamente como multiplicador e cursista. A configuração define como o sistema organiza os recursos do Programa Multiplica, sem apagar registros pedagógicos já existentes.

### Turmas

No modo `Professor multiplicador`, abra `Programa Multiplica > Turmas`.

Para cada turma, informe:

- código da turma;
- dia da semana;
- horário de início;
- tema ou componente;
- situação ativa ou inativa.

Use `Salvar turma` para incluir ou editar. Selecione uma turma na lista e use `Carregar selecionada` para alterar seus dados. A inativação preserva o histórico da turma e dos encontros já registrados.

### Cursistas

Abra a aba `Cursistas` no Programa Multiplica para cadastrar os professores participantes de cada turma.

Informe:

- turma;
- nome completo;
- unidade escolar;
- e-mail;
- telefone;
- situação;
- observações.

Um cursista fica vinculado a uma turma. Use `Carregar selecionado` para editar e `Alterar situação` para ativar ou inativar sem apagar o histórico.

### Encontros

Abra a aba `Encontros` para registrar cada formação, aplicação ou encontro relacionado ao Programa Multiplica.

1. Selecione a turma.
2. Informe a data e a pauta.
3. Ao selecionar a turma, o sistema preenche o horário de início configurado e sugere o término após uma hora e trinta minutos. Os campos continuam editáveis.
4. Informe participantes, situação, papel no encontro e observações.
5. Anexe evidências em imagem quando necessário.
6. Clique em `Salvar encontro`.

O campo `Papel no encontro` é fundamental para os relatórios:

- escolha `multiplicador` quando o encontro for conduzido para a turma de cursistas;
- escolha `cursista` quando o professor multiplicador estiver recebendo formação para posteriormente multiplicar o conteúdo.

Para editar um encontro de outro mês:

1. Escolha, no campo `Data`, qualquer dia do mês desejado.
2. Clique em `Atualizar mês`.
3. Selecione o encontro na lista `Encontros do mês`.
4. Clique em `Carregar selecionado`.
5. Faça a alteração e clique em `Salvar encontro`.

### Relatórios do Programa Multiplica

Na aba `Relatórios`, use os filtros de período, turma, papel e situação.

O relatório apresenta:

- encontros encontrados;
- quantidade de encontros realizados;
- formações recebidas no papel de cursista;
- cursistas ativos acompanhados;
- participantes registrados;
- evidências anexadas;
- detalhes e observações dos encontros.

Selecione um encontro na tabela para visualizar seus detalhes. O relatório pode ser exportado em TXT ou CSV.

## Evidências em imagem

Quando houver imagem útil para consulta futura ou relatório:

1. Use `Adicionar imagens` para anexar arquivos.
2. Use `Colar print` para inserir uma imagem da área de transferência, quando disponível.
3. Selecione um item e use `Remover selecionada` se o anexo não for necessário.

Use evidências com responsabilidade, evitando anexar dados pessoais ou sensíveis sem necessidade.

## Backup e restauração

Abra `Backup` pela tela inicial para administrar cópias do banco local.

Recursos disponíveis:

- criar backup automático na pasta local `backups/`;
- salvar cópia em outro local;
- listar backups pelo mais recente, com tamanho e data de modificação;
- restaurar um backup selecionado;
- excluir um backup selecionado;
- abrir a pasta de backups;
- atualizar a lista.

Ao restaurar um backup, o banco atual é substituído. Confirme a operação somente quando tiver certeza de que deseja recuperar aquela cópia.

Ao excluir o backup mais recente, o sistema mostra um aviso adicional. Mantenha ao menos uma cópia recente em local externo ao computador principal quando possível.

O backup preserva o banco local, incluindo usuários, registros e evidências armazenadas nele.

## Cuidados éticos, privacidade e LGPD

- Registre fatos profissionais, objetivos e cronológicos.
- Evite acusações, diagnósticos médicos e exposição desnecessária de dados sensíveis.
- Evite identificar completamente crianças e adolescentes.
- Prefira descrições como `estudante A`, `grupo do 9º ano`, `turma visitante` ou iniciais.
- Registre o que foi observado e quais providências foram adotadas.

Exemplo preferível:

`Não compareceu ao espaço no horário previsto, conforme observado, e a situação foi comunicada à coordenação.`

## Encerramento e suporte

Se um módulo apresentar erro, feche apenas a janela atual e tente novamente. O sistema busca tratar falhas sem encerrar toda a aplicação.

Antes de executar atualizações ou mudanças importantes, crie um backup. Em caso de dúvida sobre o uso, consulte este manual pelo menu `Ajuda > Manual do usuário`.
