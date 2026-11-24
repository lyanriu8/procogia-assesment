"""AI services. Two separate services share one local model client (ai.llm):

- research: question -> LangGraph pipeline -> verified comparison report (a run)
- followup: takes over a completed run and answers questions from its evidence only

Neither service knows about chat sessions; chats.sessions hands work from one to the other.
"""
