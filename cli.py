import logging
from agents.study_agent import StudyAgent
from models.errors import AgentError

logger = logging.getLogger("studyai")


def run_cli(agent: StudyAgent) -> None:
    print('Olá! Sou seu agente de estudos.\nDigite sua mensagem, "limpar" ou "sair".')
    while True:
        try:
            message = input("\nVocê: ").strip()
            if message.casefold() in {"sair", "exit", "quit"}:
                print("StudyAI: Até a próxima!")
                return
            if message.casefold() == "limpar":
                agent.clear_conversation()
                print("Conversa limpa. Seu histórico acadêmico continua salvo.")
                continue
            if not message:
                continue
            if len(message) > 20000:
                print("Use mensagens com até 20000 caracteres.")
                continue
            print("\nStudyAI:", agent.respond(message))
        except (KeyboardInterrupt, EOFError):
            print("\nAté a próxima!")
            return
        except AgentError as error:
            logger.warning("Falha na comunicação com a IA.")
            print(f"StudyAI: {error}")
            print("Registros já confirmados permanecem salvos; consulte antes de repetir cadastros.")
        except Exception:
            logger.error("Falha inesperada na conversa.")
            print("Ocorreu um erro inesperado. Consulte os registros antes de repetir cadastros.")
