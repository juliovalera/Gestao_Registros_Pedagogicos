APP_NAME = "Gestão de Registros CIEBP"
APP_CREDITS = (
    "Créditos: Professor Júlio César Valera\n"
    "Professor de Matemática, Programação e Robótica\n"
    "CIEBP - Ribeirão Preto"
)

PROFESSOR_SITUACOES = [
    "ativo",
    "afastado",
    "removido",
    "contrato encerrado",
    "inativo",
    "outro",
]

PROFESSOR_VINCULOS = [
    "efetivo",
    "temporário",
    "coordenador",
    "professor especializado",
    "outro",
]

SITUACOES_ATIVO_INATIVO = ["ativo", "inativo"]

NIVEIS_GRAVIDADE = [
    "Baixo",
    "Médio",
    "Alto",
    "Crítico",
]

TIPOS_AUSENCIA = [
    "falta",
    "atraso",
    "saída antecipada",
    "ausência no apoio",
    "não comparecimento",
    "outro",
]

OPCOES_TRIPLAS = ["sim", "não", "não sei"]
ESPACO_TODOS = "Todos os espaços"
PROFESSOR_TODOS = "Todos os professores"

ROTINA_DOCENTE_CATEGORIAS = [
    "Articulação com coordenação",
    "Atendimento a estudantes",
    "Atendimento a famílias",
    "Atendimento a público interno",
    "Convocação",
    "Correção e avaliação",
    "Diário de classe",
    "Estudo e formação",
    "Mentoria",
    "Planejamento de aula",
    "Programação",
    "Preparação de material",
    "Reunião pedagógica",
    "Projeto / oficina / laboratório",
    "Registro administrativo",
    "Outro",
]

ESPACOS_INICIAIS = [
    ("Programação Descomplicada", "Espaço voltado ao desenvolvimento de lógica e programação."),
    ("Robótica", "Espaço destinado às atividades de robótica educacional."),
    ("Cultura Maker", "Espaço para projetos mão na massa e cultura maker."),
    ("Cultura Digital", "Espaço para atividades de cultura e cidadania digital."),
    ("Prototipagem e Fabricação Digital", "Espaço para prototipagem, impressão e fabricação digital."),
    ("Hub de Inovação", "Espaço de integração de projetos e inovação."),
    (ESPACO_TODOS, "Use quando a intercorrência envolver todos os espaços do CIEBP."),
    ("Outros", "Utilize quando o registro não se enquadrar nos demais espaços."),
]

TIPOS_OCORRENCIA_INICIAIS = [
    ("Ausência de professor", "Registro objetivo de ausência do professor no espaço previsto.", "Alto"),
    ("Atraso", "Registro de atraso com impacto percebido na rotina.", "Médio"),
    ("Saída antecipada", "Saída do espaço antes do horário previsto.", "Médio"),
    ("Falta de apoio em aula", "Ausência de apoio necessário durante a atividade.", "Alto"),
    ("Conflito entre estudantes", "Situação de conflito envolvendo estudantes.", "Médio"),
    ("Conflito entre servidor e estudante", "Situação de conflito entre servidor e estudante.", "Alto"),
    ("Problema de convivência", "Situação que afetou o convívio ou o clima do ambiente.", "Médio"),
    ("Problema estrutural", "Ocorrência ligada à estrutura física do espaço.", "Médio"),
    ("Problema técnico", "Ocorrência ligada a equipamentos, software ou conectividade local.", "Médio"),
    ("Orientação recebida", "Registro de orientação formal recebida.", "Baixo"),
    ("Encaminhamento à gestão", "Registro de encaminhamento realizado à gestão.", "Alto"),
    ("Registro preventivo", "Registro feito para histórico e prevenção de recorrências.", "Baixo"),
    ("Outro", "Outras situações objetivas que mereçam registro.", "Baixo"),
]

PROFESSORES_EXEMPLO = [
    {
        "nome_completo": "Professor Exemplo 1",
        "nome_curto": "Prof. Exemplo 1",
        "area_atuacao": "Programação",
        "situacao": "ativo",
        "vinculo": "efetivo",
        "telefone_institucional": "",
        "email_institucional": "exemplo1@ciebp.local",
        "observacoes": "Cadastro fictício inicial para testes.",
    },
    {
        "nome_completo": "Professora Exemplo 2",
        "nome_curto": "Profa. Exemplo 2",
        "area_atuacao": "Robótica",
        "situacao": "ativo",
        "vinculo": "temporário",
        "telefone_institucional": "",
        "email_institucional": "exemplo2@ciebp.local",
        "observacoes": "Cadastro fictício inicial para testes.",
    },
]

GRAVIDADE_ORDEM = {
    "Baixo": 1,
    "Médio": 2,
    "Alto": 3,
    "Crítico": 4,
}
