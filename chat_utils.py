import string

from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage

from deep_lake_utils import DeepLakeLoader
import prompts


class GPTChat:
    """
    A class for interacting with an AI chat model, querying transcripts, finding objections in transcripts
    and generating responses from sales calls.
    """

    def __init__(self, live_chat=True):
        """
        Initializes a GPTChat instance.

        Parameters:
            live_chat (bool): Whether the chat is on a live transcript, or a saved one. If true, a Deep Lake DB is created.
        """
        self.messages = []
        self.chat = ChatOpenAI()
        self.response = ""

        if live_chat:
            self.db = DeepLakeLoader('data/salestesting.txt')
            self.messages.append(SystemMessage(content=prompts.LIVE_CHAT_PROMPT))

        self.saved_transcript = ""

    def message_bot(self, human_message, transcript):
        """
        Sends a message to the chatbot, and returns the response.

        Parameters:
            human_message (str): The message to send to the chatbot.
            transcript (str): The transcript of the conversation so far.

        Returns:
            str: The response from the chatbot.

        """
        human_message_with_transcript = HumanMessage(content=f'Transcript: {transcript}, ||| User message: {human_message}')

        temp_messages = self.messages.copy()
        temp_messages.append(human_message_with_transcript)

        print("Messages: ", temp_messages)

        self.response = self.chat(temp_messages)

        human_message_without_transcript = HumanMessage(content=human_message)
        self.messages.append(human_message_without_transcript)
        ai_message = AIMessage(content=self.response.content)
        self.messages.append(ai_message)

        return str(ai_message.content)


    def find_objections(self, transcript):
        print("Finding objections...")
        """
        Detects whether there is an objection in a transcript, and returns the objection if there is one.

        Parameters:
            transcript (str): The transcript to search for an objection in.

        Returns:
            str: The objection found in the transcript, or None if no objection was found.

        """
        human_message = HumanMessage(content=transcript)
        sys_message = SystemMessage(content=prompts.DETECT_OBJECTION_PROMPT)
        response = self.chat([sys_message, human_message])
        return response.content

    def generate_response_from_sales_call(self, transcript):
        """
        Generates a response from a sales call transcript if there is an objection. Queries a Deep Lake DB for relevant guidelines.

        Parameters:
            transcript (str): The transcript to generate a response from.

        Returns:
            str: The response generated from the transcript, or None if no objection was found.
        """
        response = self.find_objections(transcript)
        print("Response: ", response)
        if response[:2].translate(str.maketrans('', '', string.punctuation)).lower() == 'no':
            return None
        else:
            results = self.db.query_db(response)
            sys_message = SystemMessage(content=prompts.OBJECTION_GUIDELINES_PROMPT)
            human_message = HumanMessage(content=f'Customer objection: {response}, ||| Relevant guidelines: {results}')
            response = self.chat([sys_message, human_message])
            ai_message = AIMessage(content=response.content)
            self.messages.append(ai_message)
            return response.content

    def query_transcript(self, query, transcript):
        """
        Answers the user query using the saved transcript.

        Parameters:
            query (str): The user query.
            transcript (str): The transcript to answer the query with.

        Returns:
            str: The response to the query.
        """
        if self.saved_transcript == "":
            self.saved_transcript = transcript
            self.messages.append(HumanMessage(content=transcript))
            self.messages.append(HumanMessage(content=prompts.SAVED_TRANSCRIPT_PROMPT))
        self.messages.append(HumanMessage(content=query))
        response = self.chat(self.messages)
        ai_message = AIMessage(content=response.content)
        self.messages.append(ai_message)
        return response.content










