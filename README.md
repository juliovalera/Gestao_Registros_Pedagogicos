# Gestão de Registros CIEBP

Sistema local em Python 3 para registro, consulta, análise e emissão de relatórios sobre a rotina profissional no ambiente escolar/CIEBP.

Créditos:

Professor Júlio César Valera  
Professor de Matemática, Programação e Robótica  
CIEBP - Ribeirão Preto

## Objetivo

O sistema foi pensado para registrar fatos objetivos do cotidiano profissional, como:

- intercorrências diárias
- ausências de professores
- atrasos e saídas antecipadas
- falta de apoio em aula
- problemas de convivência
- providências e encaminhamentos
- rotina docente, diário de classe, estudos, planejamento de aula e demais atividades do professor

O foco é manter um histórico organizado, pesquisável e cronológico para consulta futura, análise do ambiente de trabalho e emissão de relatórios para acompanhamento e coordenação.

## Características

- funcionamento totalmente local
- sem dependência de internet
- banco de dados local SQLite
- interface gráfica simples em Tkinter
- acesso protegido por usuário e senha
- compatível com Windows e Linux
- criação automática do banco na primeira execução
- relatórios em TXT, CSV e PDF
- gráficos estatísticos locais na área de consultas
- exportação de gráfico em PNG
- backup e restauração do banco local
- campos de data com formatação automática e seletor de calendário
- campos de hora com formatação automática no padrão `HH:MM`
- cadastro de ausência com opção de marcar ausência integral
- anexo opcional de evidências por imagem em intercorrências e rotinas docentes
- colagem de print diretamente da área de transferência quando `Pillow` estiver instalado

## Estrutura do projeto

```text
main.py
database.py
models.py
cadastros.py
intercorrencias.py
ausencias.py
rotinas.py
consultas.py
relatorios.py
backup.py
utils.py
requirements.txt
README.md
docs/manual_usuario.md
data/
backups/
exports/
```

## Instalação

Use Python 3.

Instale as dependências com:

```bash
pip install -r requirements.txt
```

## Execução

Abra o terminal na pasta do projeto e execute:

```bash
python main.py
```

O banco de dados SQLite será criado automaticamente na primeira execução.

## Primeiro acesso e segurança

Na primeira abertura do sistema, será necessário criar um usuário local e uma senha de acesso.

- esse login é exigido antes de abrir a tela principal
- a senha não fica salva em texto puro no banco
- a troca de senha pode ser feita pelo menu `Segurança`
- para reduzir risco de acesso indevido, mantenha a senha em local seguro e não a compartilhe

## Módulos disponíveis

1. Cadastros básicos
2. Nova intercorrência
3. Registrar ausência de professor
4. Rotina docente
5. Consultar registros
6. Relatório do dia
7. Relatório por período
8. Relatório por professor
9. Relatório por espaço
10. Exportar dados
11. Backup
12. Sair

## Cadastros básicos

### Professores

O sistema permite cadastrar, editar, ativar e inativar professores.

Importante:

Não exclua definitivamente professores antigos, pois isso pode prejudicar o histórico. Quando alguém deixar de atuar no CIEBP, altere apenas a situação para `inativo`, `afastado`, `removido` ou `contrato encerrado`.

### Espaços

São criados automaticamente exemplos iniciais:

- Programação Descomplicada
- Robótica
- Cultura Maker
- Cultura Digital
- Prototipagem e Fabricação Digital
- Hub de Inovação
- Outros

### Tipos de ocorrência

São criados automaticamente exemplos iniciais:

- Ausência de professor
- Atraso
- Saída antecipada
- Falta de apoio em aula
- Conflito entre estudantes
- Conflito entre servidor e estudante
- Problema de convivência
- Problema estrutural
- Problema técnico
- Orientação recebida
- Encaminhamento à gestão
- Registro preventivo
- Outro

## Rotina docente

O módulo `Rotina docente` permite registrar atividades profissionais do professor, como:

- diário de classe
- planejamento de aula
- estudo e formação
- preparação de material
- correção e avaliação
- atendimento a estudantes
- atendimento a famílias
- reuniões pedagógicas
- projetos, oficinas e laboratório
- registros administrativos

Campos principais:

- data
- professor
- categoria
- título
- descrição da atividade

Campos complementares:

- horário inicial e final
- espaço
- turma ou público
- objetivos
- recursos utilizados
- encaminhamentos
- tags
- observações
- evidências em imagem, quando necessário

Esses registros também entram nas consultas combinadas, no resumo estatístico e nos relatórios exportáveis.

## Evidências por imagem

Os módulos de `Intercorrências` e `Rotina docente` permitem anexar evidências em imagem de forma opcional.

Você pode:

- adicionar arquivos de imagem ao registro
- colar um print diretamente da área de transferência
- manter essas evidências dentro do próprio banco local SQLite

No módulo de relatórios, o botão `Evidências PDF` gera um arquivo próprio para impressão, relacionando cada registro às imagens anexadas.

Esse relatório usa os filtros atuais de data, professor e espaço quando informados.

## Dados fictícios iniciais

O sistema cria alguns dados fictícios de exemplo apenas na primeira inicialização do banco, para facilitar testes. Esses registros podem ser editados, inativados ou excluídos depois, sem serem recriados automaticamente.

## Orientações éticas, privacidade e LGPD

O sistema deve ser usado para registros objetivos, profissionais e cronológicos.

Os registros devem evitar:

- acusações
- julgamentos pessoais
- diagnósticos médicos
- exposição desnecessária de dados sensíveis
- identificação completa de crianças ou adolescentes

Quando envolver estudantes, prefira:

- iniciais
- turma
- identificação genérica, como `estudante A`, `grupo do 9º ano` ou `turma visitante`

Registre fatos observáveis:

- data
- horário
- local
- pessoas relacionadas
- o que ocorreu
- quem presenciou
- qual providência foi adotada

Evite termos acusatórios. Exemplo:

Em vez de `fraudou o ponto`, prefira:

`não compareceu ao espaço no horário previsto, conforme observado, e a situação foi comunicada à coordenação`

## Exportação

Os relatórios podem ser exportados em:

- TXT
- CSV
- PDF, se a biblioteca `reportlab` estiver instalada

Para colar prints diretamente da área de transferência, mantenha também a biblioteca `Pillow` instalada.

Para exibir os gráficos na aba `Resumo estatístico`, mantenha também a biblioteca `matplotlib` instalada.

Na aba `Resumo estatístico`, o sistema pode mostrar gráficos de barras e gráfico de evolução diária, além de permitir exportar o gráfico atual em formato `PNG`.

Os relatórios podem incluir intercorrências, ausências e rotinas docentes, conforme o filtro selecionado.

## Backup

O módulo de backup permite:

- criar cópia local do banco de dados
- salvar cópia em outro local
- restaurar uma cópia de backup existente

Importante:

O backup copia também a base local de autenticação e as evidências em imagem, pois tudo fica armazenado no banco local. Portanto, quem restaurar um backup antigo voltará também aos usuários, senhas e anexos daquele momento.

## Executável futuro com PyInstaller

Se desejar gerar um executável no futuro:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

## Manual do usuário

O manual está disponível em:

`docs/manual_usuario.md`
