import os
from typing import List, Dict, Any
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import AgentExecutor, create_tool_calling_agent
from src.services.pubmed_service import PubMedService, search_pubmed
from src.services.brave_search_service import BraveSearchService, search_web

class PubMedRetrievalAgent:
    def __init__(self):
        self.service = PubMedService()
        self.llm = ChatAnthropic(
            model="claude-3-haiku-20240307",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.3
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a medical research assistant specializing in finding relevant PubMed articles.
Your task is to analyze search results and extract the most relevant medical evidence.
Focus on peer-reviewed research, clinical trials, and systematic reviews."""),
            ("human", "Query: {query}\n\nSearch Results:\n{results}\n\nProvide a summary of the key findings from these research articles.")
        ])
        
        self.chain = self.prompt | self.llm | StrOutputParser()

    def retrieve(self, query: str) -> Dict[str, Any]:
        results = self.service.search(query)
        
        if not results or (results and "error" in results[0]):
            return {
                "results": [],
                "summary": "Unable to retrieve PubMed results.",
                "error": results[0].get("error") if results else "No results"
            }
        
        formatted_results = "\n".join([
            f"- {r['title']} ({r.get('publication_year', 'N/A')}): {r['snippet'][:200]}..."
            for r in results[:5]
        ])
        
        try:
            summary = self.chain.invoke({"query": query, "results": formatted_results})
        except Exception as e:
            summary = f"Error generating summary: {str(e)}"
        
        return {
            "results": results,
            "summary": summary
        }


class WebSearchRetrievalAgent:
    def __init__(self):
        self.service = BraveSearchService()
        self.llm = ChatAnthropic(
            model="claude-3-haiku-20240307",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.3
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a medical information assistant that analyzes web search results.
Focus on extracting reliable medical information from reputable sources.
Be critical of the sources and prioritize information from medical institutions and health organizations."""),
            ("human", "Query: {query}\n\nSearch Results:\n{results}\n\nProvide a summary of the relevant medical information found.")
        ])
        
        self.chain = self.prompt | self.llm | StrOutputParser()

    def retrieve(self, query: str) -> Dict[str, Any]:
        results = self.service.search(query)
        
        if not results or (results and "error" in results[0]):
            return {
                "results": [],
                "summary": "Unable to retrieve web results.",
                "error": results[0].get("error") if results else "No results"
            }
        
        formatted_results = "\n".join([
            f"- {r['title']}: {r['snippet'][:200]}..."
            for r in results[:5]
        ])
        
        try:
            summary = self.chain.invoke({"query": query, "results": formatted_results})
        except Exception as e:
            summary = f"Error generating summary: {str(e)}"
        
        return {
            "results": results,
            "summary": summary
        }


class ToolBasedAgent:
    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-3-haiku-20240307",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.3
        )
        
        self.tools = [search_pubmed, search_web]
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a medical research assistant with access to PubMed and web search tools.
Use these tools to gather comprehensive medical information.
Always search both PubMed for research articles and the web for additional context."""),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        self.executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

    def run(self, query: str) -> str:
        try:
            result = self.executor.invoke({"input": query, "chat_history": []})
            return result.get("output", "No response generated")
        except Exception as e:
            return f"Agent execution failed: {str(e)}"
