from ai_agent.intent_model import get_response

def ask_cricket_ai(question):

    answer = get_response(question)

    return answer