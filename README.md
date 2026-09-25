# StudyAI

Agente de estudos em Python com memória acadêmica persistente e ferramentas reais da OpenAI.
Esta versão implementa um único StudyAgent. É uma base educacional local para um estudante.

## Requisitos

- Python 3.12 ou superior (marque **Add Python to PATH** ao instalar no Windows).
- Visual Studio Code e, opcionalmente, sua extensão Python.
- Conta OpenAI com chave da API, saldo e acesso ao modelo configurado.
- Internet para instalar dependências e conversar com a IA; SQLite e testes funcionam localmente.

## Instalação e execução no VS Code

1. Extraia StudyAI.zip e abra a pasta **StudyAI** em **Arquivo → Abrir Pasta**.
2. Abra **Terminal → Novo Terminal**, na raiz onde está main.py.
3. Crie o ambiente:

```sh
python -m venv .venv
```

Se Windows não reconhecer python, use `py -3.12 -m venv .venv`.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Windows cmd: ative com `.venv\Scripts\activate.bat` e copie com `copy .env.example .env`.

Linux/macOS:

```sh
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Se o PowerShell bloquear a ativação, não precisa mudar sua política: execute
`.\.venv\Scripts\python.exe -m pip install -r requirements.txt` e
`.\.venv\Scripts\python.exe main.py` diretamente.

Edite o arquivo **.env** e substitua somente o marcador da chave:

```dotenv
OPENAI_API_KEY=coloque_sua_chave_aqui
OPENAI_MODEL=gpt-6-astra
```

O modelo é configurável: use um modelo disponível em sua conta que suporte Responses
e function calling. O exemplo não garante acesso ou preço. Não compartilhe sua chave.

Na paleta do VS Code, escolha **Python: Select Interpreter** e selecione **.venv**.
Com o ambiente ativado:

```sh
python main.py
```

O programa cria automaticamente **data/study.db**, tabelas e **logs/studyai.log**.
Sem chave, informa como configurar e encerra com código 1; o banco ainda é inicializado.
Digite **sair** para encerrar ou **limpar** para reiniciar apenas a memória da conversa.
Ctrl+C e fim da entrada também encerram o terminal.

## Exemplos de conversa

- Cadastre a matéria Análise Vetorial.
- Cadastre Curvatura como tópico de Análise Vetorial.
- Quais matérias e tópicos eu tenho?
- Registre 40 minutos de estudo de Curvatura.
- Salve uma nota em Curvatura: revisar parametrização por comprimento de arco.
- Crie um exercício fácil sobre Curvatura e salve-o.
- Minha resposta ao exercício 1 foi [...]. Avalie e registre minha tentativa.
- Quais são minhas maiores dificuldades?
- Cadastre uma prova de Análise Vetorial para 2030-10-20.
- Quais são minhas próximas provas?

Datas de provas usam AAAA-MM-DD. Sessões aceitam horário ISO com fuso
(por exemplo, 2026-09-24T18:00:00-03:00); null significa agora.
A IA consulta identificadores por ferramentas antes de cadastrar relacionamentos.
Avaliações feitas pela IA podem conter erros; revise o feedback antes de usar os
indicadores como evidência de aprendizado. Não há avaliador especializado nesta fase.

## Arquitetura

```text
Terminal → StudyAgent → registro de ferramentas → ferramentas
                                                ├→ PerformanceService
                                                └→ Repository → SQLite
```

- **main.py** compõe as dependências; **cli.py** gerencia a conversa no terminal.
- **agents/** contém a integração com OpenAI e o loop de chamadas de ferramentas.
- **tools/** expõe operações acadêmicas e uma lista explícita das funções permitidas.
- **services/** concentra a fórmula e a atualização transacional de domínio.
- **database/** cuida de conexões, schema, consultas parametrizadas e repositório.
- **models/** contém dataclasses, enum, validações e erros de domínio.
- **config/** carrega .env e configura logs com rotação.
- **prompts/** define o comportamento pedagógico e o uso do histórico.
- **tests/** usa bancos temporários; não modifica data/study.db.

São sete tabelas: subjects, topics, study_sessions, exercises, attempts, exams e
study_notes. Chaves estrangeiras ficam ativas em cada conexão. Uma sessão só pode
referenciar um tópico da própria matéria. Nomes repetidos exatos são impedidos por
matéria; a comparação de nomes é sensível a maiúsculas/acentos nesta primeira versão.
Não há exclusão ou edição de registros pela interface nesta fase.

### Como o agente funciona

1. Python envia a mensagem, o prompt, o histórico em memória e os schemas JSON.
2. O modelo escolhe responder ou emitir uma function_call.
3. O registro valida nome e argumentos e executa apenas uma função permitida.
4. Python envia function_call_output com o call_id correspondente.
5. O modelo usa o resultado para responder ou solicitar outra ferramenta.

Usa o SDK oficial e **Responses API**, com schemas strict, store=False e sem
framework de agentes. Todos os itens de saída, inclusive raciocínio criptografado
quando disponível, são preservados para continuar a conversa. Chamadas paralelas
ficam desativadas. Após oito rodadas de ferramentas, a última chamada solicita
somente texto, limitando loops. Não há shell, SQL livre ou execução de código
fornecido pelo modelo.

Fontes oficiais consultadas na implementação:
[Function calling](https://developers.openai.com/api/docs/guides/function-calling).

### Ferramentas disponíveis

- list_subjects, create_subject, list_topics, create_topic.
- get_topic_performance, get_weak_topics.
- register_study_session, list_recent_study_sessions.
- create_exam, list_upcoming_exams.
- save_study_note, get_study_notes.
- create_exercise, list_exercises, register_attempt, list_attempts.

As quatro últimas operações de exercícios/tentativas completam o caminho para
alimentar e consultar o desempenho pela própria conversa.

### Duas memórias

**Conversa:** lista em RAM, mantida durante a execução. Permite referências como
“nela” ao falar de uma matéria. Desaparece ao sair ou usar limpar. Não há resumo
automático; conversas muito longas podem exceder o contexto ou aumentar o custo.
Use limpar nesse caso.

**Acadêmica:** SQLite em data/study.db. Sobrevive à reinicialização e só é alterada
pelas ferramentas. Faça cópia desse arquivo com o programa fechado para backup.
Não há sincronização, autenticação ou suporte a vários estudantes.

Mensagens e resultados consultados são enviados à OpenAI para gerar respostas.
store=False evita armazenar a resposta para recuperação via API; não representa
garantia de ausência de toda retenção operacional pelo provedor.
O banco local não é criptografado. Não registre segredos ou dados desnecessários.

### Domínio

`mastery_level = acertos / tentativas * 100`, arredondado a duas casas.
Todas as tentativas contam, inclusive repetições do mesmo exercício. Não equivale
à porcentagem de exercícios únicos resolvidos.

Sem tentativas, o valor armazenado é 0, mas has_evidence é false. A busca separa
weak_topics (abaixo de 60% por padrão) de unassessed_topics. No limiar exato o tópico
não é classificado como fraco. Contagens acompanham o resultado para mostrar a amostra.

PerformanceService é o ponto de extensão para pesos por dificuldade, recência,
esquecimento e confiança estatística. A tentativa e o domínio são gravados juntos
em uma transação; falhas provocam rollback. Leituras calculam a taxa a partir do
histórico, enquanto topics.mastery_level mantém o valor persistido.

## Testes

```sh
python -m pytest -q
```

Cobertura: criação idempotente do banco, persistência, matérias/tópicos,
relacionamentos, SQL como dados, sessões, notas, datas de provas, exercícios,
tentativas, domínio, tópicos sem evidência, entradas inválidas, inicialização e
tool calling. O teste do SDK utiliza transporte HTTP simulado e não gasta créditos.

Validação realizada: Python 3.12.14, OpenAI SDK 2.54.0, python-dotenv 1.2.3,
pytest 9.1.1; 34 testes passaram. A API externa com credenciais reais não foi
validada. requirements.txt limita versões principais e permite atualizações compatíveis.

## Erros e logs

- Chave ausente: copie .env.example para .env e preencha a chave.
- Chave recusada: confira a chave e a conta da API.
- Modelo recusado: altere OPENAI_MODEL para um modelo compatível disponível.
- Limite/saldo: confira o uso e a cobrança na conta.
- Conexão/API indisponível: tente novamente mais tarde.
- Banco indisponível: confira permissões, espaço em disco e processos que o bloqueiem.
- Referência inexistente ou entrada inválida: a ferramenta retorna erro legível.

Logs registram somente eventos genéricos, sem mensagens, notas, argumentos,
API keys, dumps de ambiente ou texto bruto das exceções.
Se a API falhar depois de uma gravação, essa gravação permanece. O histórico
mantém o resultado da ferramenta. Consulte antes de repetir a solicitação;
não há garantia global de execução única entre pedidos separados do usuário.
Reiniciar a conversa não desfaz gravações anteriores.

## Estrutura das pastas

```text
StudyAI/
├── README.md
├── requirements.txt
├── pytest.ini
├── .env.example
├── .gitignore
├── main.py
├── cli.py
├── agents/
│   ├── __init__.py
│   └── study_agent.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── logging_config.py
├── database/
│   ├── __init__.py
│   ├── connection.py
│   ├── schema.py
│   └── repositories.py
├── models/
│   ├── __init__.py
│   ├── entities.py
│   ├── errors.py
│   └── validation.py
├── tools/
│   ├── __init__.py
│   ├── registry.py
│   ├── subject_tools.py
│   ├── study_tools.py
│   └── performance_tools.py
├── services/
│   ├── __init__.py
│   └── performance_service.py
├── prompts/
│   └── study_agent_prompt.txt
├── data/
│   └── .gitkeep
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_database.py
    ├── test_performance.py
    ├── test_agent.py
    └── test_startup.py
```

.env, .venv, logs, caches e data/study.db são locais e não fazem parte do ZIP.

## Roadmap

### Fase 1 — Base (implementada)

SQLite; matérias; tópicos; sessões; exercícios; tentativas; provas; notas.

### Fase 2 — Agente (implementada; validação externa depende da sua chave)

OpenAI; tool calling; memória da conversa; memória acadêmica; análise de desempenho.

### Fase 3 — Inteligência educacional (futura)

Exercícios adaptativos; dificuldade dinâmica; revisão espaçada; análise avançada
de erros; planos de estudo; avaliação de qualidade pedagógica.

### Fase 4 — Multiagentes (futura, não implementada)

Tutor; Evaluator; Planner; Exercise Generator; Researcher; Orchestrator.
Os futuros agentes poderão reutilizar ferramentas e serviços sem acessar SQLite.
Não é necessário criar hierarquias de classes ou um orquestrador antes dessa fase.

### Fase 5 — Aplicação (futura)

FastAPI; interface web; autenticação; gráficos; dashboard; migrações versionadas,
paginação e proteção para uso por múltiplos estudantes.
