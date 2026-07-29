"""Constantes e listas de apoio do sistema pedagógico."""

APP_NAME = "Gestão de Registros Pedagógicos"
APP_VERSION = "1.014"
APP_TITLE = f"{APP_NAME} v{APP_VERSION}"
APP_CREDITS = (
    "Créditos: Professor Júlio César Valera\n"
    "Professor de Matemática, Programação e Robótica\n"
    "Registros Pedagógicos - Ribeirão Preto"
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

CONTEXTOS_ATUACAO = [
    "Atendimento remoto",
    "CIEBP",
    "Coordenação pedagógica",
    "Evento / ação institucional",
    "Formação / reunião de rede",
    "Projeto / parceria externa",
    "Unidade escolar",
    "Outro",
]

ROTINA_DOCENTE_CATEGORIAS = [
    "Acompanhamento pedagógico",
    "Articulação com coordenação",
    "Atendimento a estudantes",
    "Atendimento a famílias",
    "Atendimento a professores",
    "Atendimento a público interno",
    "Convocação",
    "Correção e avaliação",
    "Diário de classe",
    "Estudo e formação",
    "Lançamento de notas e frequência",
    "Manutenção e/ou Limpeza",
    "Mentoria",
    "Planejamento coletivo",
    "Planejamento de aula",
    "Preparação de material",
    "Programação",
    "Projeto / oficina / laboratório",
    "Registro administrativo",
    "Registro em sistema",
    "Reunião com famílias",
    "Reunião pedagógica",
    "Tutoria / acompanhamento",
    "Outro",
]

ESPACOS_INICIAIS = [
    ("Área externa", "Espaço externo utilizado em atividades pedagógicas, acolhimento ou circulação."),
    ("Atendimento remoto / online", "Ambiente utilizado para registros de atividades remotas ou híbridas."),
    ("Auditório / sala multiuso", "Espaço para reuniões, apresentações, oficinas e ações coletivas."),
    ("Biblioteca / sala de leitura", "Espaço de leitura, pesquisa e mediação pedagógica."),
    ("Coordenação", "Espaço destinado a atendimentos, alinhamentos e ações da coordenação."),
    ("Cultura Digital", "Espaço para atividades de cultura e cidadania digital."),
    ("Cultura Maker", "Espaço para projetos mão na massa e cultura maker."),
    ("Direção / gestão", "Espaço de gestão escolar, direção e reuniões administrativas."),
    ("Hub de Inovação", "Espaço de integração de projetos e inovação."),
    ("Laboratório de informática", "Espaço de uso de computadores, internet e ferramentas digitais."),
    ("Pátio / convivência", "Espaço de circulação, acolhimento e convivência escolar."),
    ("Programação Descomplicada", "Espaço voltado ao desenvolvimento de lógica e programação."),
    ("Prototipagem e Fabricação Digital", "Espaço para prototipagem, impressão e fabricação digital."),
    ("Quadra / espaço esportivo", "Espaço esportivo e de atividades coletivas."),
    ("Robótica", "Espaço destinado às atividades de robótica educacional."),
    ("Sala de aula", "Sala de aula regular utilizada em atividades pedagógicas."),
    ("Sala de recursos / AEE", "Espaço de atendimento educacional especializado e apoio pedagógico."),
    ("Sala dos professores", "Espaço de planejamento, estudo e atendimento interno aos docentes."),
    ("Secretaria", "Espaço administrativo para atendimento e registros escolares."),
    (ESPACO_TODOS, "Use quando a intercorrência envolver todos os espaços pedagógicos cadastrados."),
    ("Outros", "Utilize quando o registro não se enquadrar nos demais espaços."),
]

TIPOS_OCORRENCIA_INICIAIS = [
    ("Acompanhamento pedagógico", "Registro de acompanhamento pedagógico, devolutiva ou monitoramento de atividade.", "Baixo"),
    ("Ajuste de horário / escala", "Registro de alteração, reorganização ou ajuste de horário de trabalho ou atendimento.", "Baixo"),
    ("Ausência de professor", "Registro objetivo de ausência do professor no espaço previsto.", "Alto"),
    ("Atraso", "Registro de atraso com impacto percebido na rotina.", "Médio"),
    ("Atendimento a família", "Registro de atendimento, contato ou demanda envolvendo responsável ou família.", "Baixo"),
    ("Atendimento a professor", "Registro de orientação, apoio ou atendimento a professor da rede.", "Baixo"),
    ("Conflito entre estudantes", "Situação de conflito envolvendo estudantes.", "Médio"),
    ("Conflito entre servidor e estudante", "Situação de conflito entre servidor e estudante.", "Alto"),
    ("Demanda administrativa", "Registro de situação administrativa com impacto na rotina escolar.", "Baixo"),
    ("Dificuldade de aprendizagem observada", "Registro objetivo de dificuldade de aprendizagem observada em atividade pedagógica.", "Baixo"),
    ("Encaminhamento à gestão", "Registro de encaminhamento realizado à gestão.", "Alto"),
    ("Falta de apoio em aula", "Ausência de apoio necessário durante a atividade.", "Alto"),
    ("Indisciplina / comportamento inadequado", "Registro de comportamento inadequado ou quebra de combinados.", "Médio"),
    ("Orientação recebida", "Registro de orientação formal recebida.", "Baixo"),
    ("Problema de convivência", "Situação que afetou o convívio ou o clima do ambiente.", "Médio"),
    ("Problema estrutural", "Ocorrência ligada à estrutura física do espaço.", "Médio"),
    ("Problema técnico", "Ocorrência ligada a equipamentos, software ou conectividade local.", "Médio"),
    ("Registro preventivo", "Registro feito para histórico e prevenção de recorrências.", "Baixo"),
    ("Reunião / alinhamento", "Registro de orientação, alinhamento ou reunião relacionada à rotina pedagógica.", "Baixo"),
    ("Saída antecipada", "Saída do espaço antes do horário previsto.", "Médio"),
    ("Uso inadequado de equipamento", "Ocorrência relacionada ao uso indevido ou inadequado de equipamento ou recurso.", "Médio"),
    ("Visita / turma visitante", "Registro de situação envolvendo visita técnica, turma visitante ou público externo.", "Baixo"),
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
        "email_institucional": "exemplo1@pedagogico.local",
        "observacoes": "Cadastro fictício inicial para testes.",
    },
    {
        "nome_completo": "Professora Exemplo 2",
        "nome_curto": "Profa. Exemplo 2",
        "area_atuacao": "Robótica",
        "situacao": "ativo",
        "vinculo": "temporário",
        "telefone_institucional": "",
        "email_institucional": "exemplo2@pedagogico.local",
        "observacoes": "Cadastro fictício inicial para testes.",
    },
]

GRAVIDADE_ORDEM = {
    "Baixo": 1,
    "Médio": 2,
    "Alto": 3,
    "Crítico": 4,
}
