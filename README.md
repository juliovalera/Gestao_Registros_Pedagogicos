<div align="center">

# Gestão de Registros Pedagógicos

**Sistema local para organizar registros pedagógicos, preservar históricos e produzir relatórios com segurança.**

[![Versão](https://img.shields.io/badge/vers%C3%A3o-1.059-0F5F8F?style=flat-square)](#versão-atual)
[![Python](https://img.shields.io/badge/Python-3-3776AB?style=flat-square&logo=python&logoColor=white)](#instalação)
[![Banco de dados](https://img.shields.io/badge/banco-SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)](#arquitetura-local)
[![Licença](https://img.shields.io/badge/licença-MIT-2E7D32?style=flat-square)](LICENSE)

[Começar](#instalação) · [Recursos](#recursos-principais) · [Programa Multiplica](#programa-multiplica) · [Manual](docs/manual_usuario.md)

</div>

---

## Visão geral

O **Gestão de Registros Pedagógicos** é uma aplicação desktop em Python para apoiar professores, coordenação e equipes pedagógicas na organização do cotidiano escolar. Os dados permanecem no computador do usuário, em um banco SQLite criado automaticamente na primeira execução.

> O foco do projeto é transformar registros dispersos em um histórico cronológico, consultável e útil para acompanhamento profissional, devolutivas e relatórios.

## Versão atual

`1.059`

Nesta versão, destacam-se:

| Entrega | Resultado prático |
|---|---|
| Ausências unificadas | O registro oficial é feito em `Nova intercorrência > Ausência de professor`, evitando divergências nos relatórios. |
| Programa Multiplica | Cadastro de turmas e cursistas, encontros, evidências e relatórios por período. |
| Calendário e horários | Campos de data com calendário e horários no padrão `HH:MM`. |
| Backup aprimorado | Lista ordenada pelo mais recente, com tamanho, data de modificação e exclusão confirmada. |

## Recursos principais

| Área | O que permite fazer |
|---|---|
| **Rotina docente** | Registrar diário de classe, planejamento, estudos, atendimentos, reuniões, projetos e atividades administrativas. |
| **Intercorrências** | Documentar fatos objetivos, providências, gravidade, contexto e evidências. |
| **Ausências** | Registrar ausências, atrasos e saídas antecipadas dentro do fluxo de intercorrências. |
| **Cadastros básicos** | Manter professores, espaços e tipos de ocorrência, preservando o histórico por inativação. |
| **Consultas** | Filtrar por período, professor, espaço, tipo, contexto, gravidade e palavras-chave. |
| **Relatórios gerais** | Gerar relatórios do dia, por período, professor e espaço, inclusive em formato de ata. |
| **Evidências** | Anexar imagens e prints aos registros quando forem realmente necessários. |
| **Backup** | Criar, restaurar, copiar, listar e excluir backups locais com segurança. |

## Programa Multiplica

O Programa Multiplica é ativado em `Segurança > Modo do Programa Multiplica`, vinculando o usuário a um professor cadastrado.

| Modo | Finalidade |
|---|---|
| `Professor multiplicador` | Organiza turmas, acompanha cursistas, registra encontros e consolida relatórios. |
| `Professor cursista` | Identifica o professor que recebe formações do Programa Multiplica. |
| `Uso geral` | Mantém o sistema sem um papel específico no programa. |

Um professor deve atuar em apenas um dos papéis do programa por vez: multiplicador ou cursista.

### Fluxo do professor multiplicador

1. Cadastre as turmas com código, dia, horário, componente e situação.
2. Vincule os professores participantes na aba `Cursistas`.
3. Registre os encontros com data, pauta, horários, participantes, observações e evidências.
4. Marque o papel no encontro:
   - `multiplicador` para os encontros conduzidos para seus cursistas;
   - `cursista` para as formações que o próprio multiplicador recebe.
5. Gere relatórios por período, turma, papel e situação.

O registro do papel `cursista` permite distinguir, nos relatórios, as formações recebidas pelo multiplicador das ações que ele multiplicou para suas turmas.

### Edição de encontros anteriores

Para localizar um encontro de outro mês:

1. Escolha, no campo `Data`, qualquer dia do mês desejado.
2. Clique em `Atualizar mês`.
3. Selecione o encontro em `Encontros do mês`.
4. Use `Carregar selecionado`, altere o que for necessário e clique em `Salvar encontro`.

## Arquitetura local

```text
Gestao_Registros_CIEBP/
├── main.py                    # Inicialização, login e tela principal
├── database.py                # Banco SQLite, consultas, migrações e backups
├── models.py                  # Constantes, listas de apoio e versão
├── cadastros.py               # Professores, espaços e tipos de ocorrência
├── intercorrencias.py         # Registro oficial de intercorrências e ausências
├── rotinas.py                 # Rotinas docentes
├── consultas.py               # Filtros, indicadores e gráficos
├── relatorios.py              # Relatórios gerais, atas e exportações
├── multiplica_window.py       # Programa Multiplica
├── backup.py                  # Cópias e restauração do banco
├── utils.py                   # Componentes reutilizáveis da interface
├── docs/
│   └── manual_usuario.md      # Manual completo de uso
├── data/                      # Banco local criado na execução
├── backups/                   # Backups automáticos e locais
└── exports/                   # Relatórios e arquivos exportados
```

## Instalação

### Requisitos

- Python 3 com Tkinter habilitado;
- `pip` para instalar dependências opcionais.

### Preparação

```bash
git clone https://github.com/juliovalera/Gestao_Registros_Pedagogicos.git
cd Gestao_Registros_Pedagogicos
pip install -r requirements.txt
```

### Execução

```bash
python main.py
```

Na primeira execução, o sistema solicita a criação do primeiro usuário e cria o banco local automaticamente.

## Relatórios, evidências e exportação

| Recurso | Saídas disponíveis |
|---|---|
| Relatórios gerais | Visualização, TXT, CSV e PDF quando `reportlab` estiver instalado. |
| Relatórios do Programa Multiplica | Visualização, TXT e CSV por período, turma, papel e situação. |
| Gráficos | Visualização local e exportação em PNG. |
| Evidências | Quantidade, nomes de arquivos ou inclusão em PDF, conforme a opção escolhida no relatório geral. |

As evidências devem ser usadas com critério, apenas quando ajudarem na consulta futura, em relatórios ou na comprovação de uma ação pedagógica.

## Backup e segurança dos dados

O módulo `Backup` permite:

- criar cópias automáticas na pasta `backups/`;
- salvar cópias em outro local;
- visualizar arquivo, tamanho e data de modificação;
- restaurar um backup selecionado;
- excluir backups com confirmação adicional para o mais recente;
- abrir rapidamente a pasta de backups.

> A restauração substitui o banco local atual. Crie um backup antes de atualizações, mudanças de computador ou operações de manutenção.

## Privacidade e boas práticas

- Registre fatos profissionais, objetivos e cronológicos.
- Evite dados sensíveis, julgamentos pessoais e exposição desnecessária de estudantes.
- Prefira identificações pedagógicas discretas, como iniciais, turma ou grupo.
- Inative referências antigas em vez de excluí-las quando fizerem parte do histórico.
- Mantenha cópias de backup em local externo ao computador principal sempre que possível.

## Documentação

| Documento | Conteúdo |
|---|---|
| [Manual do usuário](docs/manual_usuario.md) | Fluxos completos, campos, Programa Multiplica, relatórios, backups e cuidados com privacidade. |
| [Licença MIT](LICENSE) | Condições de uso, adaptação e redistribuição do projeto. |

## Créditos

**Professor Júlio César Valera**<br>
Professor de Matemática, Programação e Robótica<br>
Ribeirão Preto, SP

## Licença

Este projeto é distribuído sob a [Licença MIT](LICENSE). Ele pode ser utilizado, estudado, adaptado e redistribuído, desde que os créditos e o texto da licença sejam preservados.
