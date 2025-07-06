from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
import asyncio


DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant."

def generate_answer(question: str, context: str) -> str:
    """
    Generate an answer using OpenAI's API (legacy, not recommended for new code).
    Args:
        question (str): The user's question.
        context (str): The context to provide to the LLM.
    Returns:
        str: The generated answer.
    """
    client = OpenAI()
    prompt = f"Context: {context}\n\nQuestion: {question}\nAnswer:"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=256,
        temperature=0.2
    )
    return response.choices[0].message.content.strip()

def generate_answer_langchain(question: str, context: str, system_prompt: str = DEFAULT_SYSTEM_PROMPT) -> str:
    """
    Generate an answer using LangChain's ChatOpenAI LLM.
    Args:
        question (str): The user's question.
        context (str): The context to provide to the LLM.
        system_prompt (str): The system prompt for the LLM.
    Returns:
        str: The generated answer.
    """
    llm = ChatOpenAI()
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=question + "\n" + context)
    ]
    return llm.invoke(messages).content

class StreamHandler(StreamingStdOutCallbackHandler):
    """
    LangChain callback handler for streaming LLM tokens asynchronously.
    Collects tokens in an asyncio.Queue for streaming to the client.
    """
    def __init__(self):
        self.queue = asyncio.Queue()
        self.done = asyncio.Event()
    def on_llm_new_token(self, token: str, **kwargs):
        self.queue.put_nowait(token)
    def on_llm_end(self, *args, **kwargs):
        self.done.set()

async def stream_answer_langchain(question: str, context: str, system_prompt: str = DEFAULT_SYSTEM_PROMPT):
    """
    Stream an answer from LangChain's ChatOpenAI LLM, yielding tokens as they are generated.
    Args:
        question (str): The user's question.
        context (str): The context to provide to the LLM.
        system_prompt (str): The system prompt for the LLM.
    Yields:
        str: The next token in the generated answer.
    """
    handler = StreamHandler()
    llm = ChatOpenAI(streaming=True, callbacks=[handler])
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=question + "\n" + context)
    ]
    async def run_llm():
        await llm.ainvoke(messages)
    task = asyncio.create_task(run_llm())
    while not handler.done.is_set() or not handler.queue.empty():
        try:
            token = await asyncio.wait_for(handler.queue.get(), timeout=0.1)
            yield token
        except asyncio.TimeoutError:
            if handler.done.is_set():
                break
    await task 