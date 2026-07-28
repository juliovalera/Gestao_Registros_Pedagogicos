# Gestão de Registros Pedagógicos

Sistema local em Python 3 para registrar, consultar, analisar e exportar informações da rotina pedagógica escolar de forma organizada, cronológica e profissional.

Versão atual: `1.006`

Status desta versão:

- versão atual com contexto obrigatório e reposicionado no cadastro de intercorrências
- próxima atualização prevista: `1.007`

## Visão geral

O projeto foi pensado para apoiar o trabalho de professores, coordenação e equipes pedagógicas no acompanhamento do dia a dia escolar.

Com ele, é possível registrar:

- rotina docente
- diário de classe
- planejamento de aula
- estudos e formações
- atendimentos pedagógicos
- ausências e atrasos
- orientações recebidas
- encaminhamentos realizados
- intercorrências e situações relevantes da rotina

O objetivo é facilitar a memória institucional, a consulta posterior, a produção de relatórios e a análise de dados de maneira simples e totalmente local.

## Controle de versão

O projeto passa a adotar versionamento sequencial simples.

- versão inicial formal: `1.001`
- atualização da ordem dos campos no cadastro de rotina docente: `1.002`
- contexto de atuação obrigatório no cadastro de rotina docente: `1.003`
- nova categoria `Manutenção e/ou Limpeza` nas rotinas docentes: `1.004`
- sugestão automática de data e hora inicial com base no último registro: `1.005`
- contexto de atuação obrigatório, reposicionado e sugerido automaticamente nas intercorrências: `1.006`
- a cada implementação, ajuste ou correção: somar `0.001`
- exemplos futuros: `1.007`, `1.008`, `1.009`

Essa versão pode ser exibida na interface do sistema e também na documentação do projeto.

## Créditos

Professor Júlio César Valera  
Professor de Matemática, Programação e Robótica  
Ribeirão Preto

## Principais recursos

- funcionamento totalmente local, sem depender de internet
- banco de dados SQLite criado automaticamente na primeira execução
- interface gráfica em Tkinter
- acesso protegido por usuário e senha
- compatível com Windows e Linux
- cadastro de professores, espaços e tipos de registro
- módulo de intercorrências
- módulo de ausências de professores
- módulo de rotinas docentes
- consultas com filtros combinados
- relatórios do dia, por período, por professor e por espaço
- relatórios em formato de ata
- exportação em TXT, CSV e PDF
- resumo estatístico com gráficos locais
- exportação de gráficos em PNG
- backup e restauração do banco local
- anexos opcionais de evidências por imagem em intercorrências e rotinas docentes

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

### O que faz cada arquivo

| Arquivo | Finalidade |
|---|---|
| `main.py` | Inicializa a aplicação, autenticação, menu principal e resumo da tela inicial. |
| `database.py` | Centraliza a criação do banco SQLite, consultas, gravações, filtros e estatísticas. |
| `models.py` | Reúne constantes, listas fixas, nomes do sistema e versão atual. |
| `cadastros.py` | Tela de cadastros básicos de professores, espaços e tipos de ocorrência. |
| `intercorrencias.py` | Tela de busca rápida, cadastro, edição e exclusão de intercorrências. |
| `ausencias.py` | Tela de busca rápida, cadastro, edição e exclusão de ausências de professores. |
| `rotinas.py` | Tela de busca rápida, cadastro, edição e exclusão de rotinas docentes. |
| `consultas.py` | Consultas combinadas, filtros avançados, estatísticas e gráficos locais. |
| `relatorios.py` | Geração de relatórios, atas, exportações e PDFs de evidências. |
| `backup.py` | Rotinas de backup, restauração e acesso rápido à pasta de cópias locais. |
| `auth.py` | Controle de login, criação do primeiro usuário e troca de senha. |
| `utils.py` | Componentes reutilizáveis da interface, calendário, hora, mensagens e funções auxiliares. |
| `merge_onedrive_databases.py` | Apoio técnico para análise e conferência de bancos duplicados em cenários de sincronização. |
| `requirements.txt` | Dependências opcionais e recomendadas para PDF, imagens e gráficos. |
| `README.md` | Apresentação pública do projeto, recursos, execução e visão geral. |
| `docs/manual_usuario.md` | Manual de uso com linguagem prática para o usuário final. |
| `data/` | Pasta do banco local utilizado pelo sistema. |
| `backups/` | Pasta padrão de backups locais do banco. |
| `exports/` | Pasta padrão de relatórios, planilhas e arquivos exportados. |

## Requisitos

- Python 3

## Instalação

Instale as dependências com:

```bash
pip install -r requirements.txt
```

## Como executar

Abra o terminal na pasta do projeto e execute:

```bash
python main.py
```

Na primeira execução, o sistema cria automaticamente o banco de dados local.

## Primeiro acesso

No primeiro uso, o sistema solicitará a criação de um usuário e uma senha.

Isso permite restringir o acesso aos registros e proteger informações de uso interno.

Recursos de segurança disponíveis:

- login obrigatório antes da tela principal
- senha armazenada de forma protegida
- troca de senha pelo menu `Segurança`

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

O sistema possui cadastros para:

- professores
- espaços
- tipos de ocorrência

Os registros históricos são preservados. Por isso, o ideal é manter professores e referências antigas inativados quando necessário, em vez de removê-los definitivamente.

## Rotina docente

O módulo `Rotina docente` foi criado para acompanhar o trabalho profissional diário do professor e da equipe pedagógica.

Exemplos de uso:

- diário de classe
- planejamento de aula
- planejamento coletivo
- estudo e formação
- mentoria
- programação
- acompanhamento pedagógico
- atendimento a estudantes
- atendimento a famílias
- atendimento a professores
- atendimento a público interno
- reuniões pedagógicas
- registros administrativos

Campos principais:

- data
- professor ou professores
- categoria
- título
- descrição da atividade

Campos complementares:

- hora de início e hora de fim
- espaço
- contexto de atuação
- turma ou público
- objetivos
- recursos utilizados
- encaminhamentos
- tags
- observações
- evidências em imagem, quando necessário

## Intercorrências e ausências

Além da rotina docente, o sistema também permite registrar fatos objetivos relacionados ao funcionamento pedagógico diário, como:

- ausências
- atrasos
- saídas antecipadas
- falta de apoio em aula
- orientações e encaminhamentos
- situações de convivência
- registros preventivos
- ocorrências técnicas, estruturais ou administrativas

Esses registros podem ser consultados depois com filtros combinados e incluídos em relatórios.

## Consultas e análise

O módulo `Consultar registros` permite combinar filtros para localizar informações com rapidez.

Exemplos:

- professor + período
- espaço + período
- categoria + período
- tipo de ocorrência + período
- palavra-chave + período
- contexto de atuação + período

Também há um resumo estatístico com contagens e gráficos locais, incluindo:

- quantidade de intercorrências por período
- quantidade por tipo de ocorrência
- quantidade por espaço
- quantidade de ausências por professor
- quantidade de registros por nível de gravidade
- quantidade de registros por contexto de atuação

## Relatórios

O sistema pode gerar:

- relatório do dia
- relatório por período
- relatório por professor
- relatório por espaço
- relatório em formato de ata
- ata por período

Os relatórios podem combinar:

- intercorrências
- ausências
- rotinas docentes

Também é possível controlar como as evidências aparecem:

- ocultar totalmente
- mostrar apenas a quantidade
- mostrar quantidade e nomes dos arquivos

## Evidências por imagem

Nos módulos de `Intercorrências` e `Rotina docente`, é possível anexar imagens de forma opcional.

Você pode:

- adicionar arquivos de imagem ao registro
- colar um print da área de transferência, quando `Pillow` estiver instalado
- gerar um PDF específico de evidências a partir dos filtros utilizados

## Datas e horas

O sistema possui apoio para preenchimento mais rápido:

- campos de data com formatação automática
- botão de calendário
- destaque para a data atual no calendário
- campos de hora com formatação automática no padrão `HH:MM`

## Exportação

Os relatórios podem ser exportados em:

- TXT
- CSV
- PDF, quando a biblioteca `reportlab` estiver instalada

Recursos adicionais:

- gráficos podem ser exportados em PNG
- nomes dos arquivos exportados incluem data e hora para evitar sobrescrita
- há botão para abrir a pasta de exportação diretamente pela interface

## Backup

O módulo de backup permite:

- criar backup automático na pasta local do projeto
- salvar uma cópia em outro local
- restaurar um backup existente
- abrir rapidamente a pasta onde os backups ficam armazenados

Como o sistema é local, o backup preserva também:

- usuários cadastrados
- registros
- evidências em imagem

## Dados iniciais de exemplo

Na primeira inicialização do banco, o sistema pode criar alguns dados fictícios para facilitar testes.

Esses registros podem ser:

- editados
- inativados
- excluídos

Eles não são recriados automaticamente depois.

## Boas práticas de uso

O sistema foi pensado para registros:

- objetivos
- profissionais
- cronológicos
- úteis para acompanhamento pedagógico

Sempre que possível, prefira registrar:

- data e horário
- local
- pessoas relacionadas
- descrição observável do fato
- providências ou encaminhamentos adotados

Quando houver participação de estudantes, é recomendável usar identificação pedagógica mais discreta, como:

- iniciais
- turma
- grupo
- identificação genérica

## Privacidade e cuidado com a escrita

Como o sistema pode armazenar informações sensíveis de rotina profissional, recomenda-se:

- evitar exposição desnecessária de dados pessoais
- evitar julgamentos ou conclusões precipitadas
- priorizar linguagem objetiva
- manter foco em fatos, ações e encaminhamentos

Isso ajuda a preservar a utilidade do histórico e melhora a qualidade dos relatórios produzidos.

## Executável futuro com PyInstaller

Se desejar gerar um executável no futuro:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

## Manual do usuário

O manual está disponível em:

`docs/manual_usuario.md`

## Licença

Este projeto está licenciado sob a licença MIT.

Em termos simples, isso significa que outras pessoas podem:

- usar o projeto livremente
- estudar o código
- adaptar para outra realidade escolar ou institucional
- copiar e redistribuir
- publicar versões modificadas

Desde que mantenham:

- o aviso de copyright
- o texto da licença MIT

Em linguagem pedagógica, a licença MIT funciona como uma autorização ampla para reaproveitamento do projeto, inclusive com personalizações, desde que a autoria original e a licença sejam preservadas junto ao código.

Importante:

- a licença não obriga que melhorias sejam devolvidas ao projeto original
- a licença não oferece garantia de funcionamento para todos os contextos
- o texto jurídico oficial continua sendo o arquivo `LICENSE`

Ou seja: o projeto pode ser reutilizado, adaptado e compartilhado com bastante liberdade, mas sempre com os créditos e a licença acompanhando a distribuição do código.
