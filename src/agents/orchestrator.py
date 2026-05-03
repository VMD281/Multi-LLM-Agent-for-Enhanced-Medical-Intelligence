import os
from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.agents.retrieval_agents import PubMedRetrievalAgent, WebSearchRetrievalAgent

class MedicalAgentState(TypedDict):
    query: str
    pubmed_results: List[Dict[str, Any]]
    pubmed_summary: str
    web_results: List[Dict[str, Any]]
    web_summary: str
    final_answer: str
    error: str

class MedicalAgentOrchestrator:
    def __init__(self):
        self.pubmed_agent = PubMedRetrievalAgent()
        self.web_agent = WebSearchRetrievalAgent()
        
        self.synthesizer_llm = ChatAnthropic(
            model="claude-3-haiku-20240307",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.5
        )
        
        self.synthesis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert medical synthesizer. Your role is to combine information from 
multiple sources (PubMed research and web search) into a comprehensive, accurate medical answer.

Guidelines:
- Prioritize peer-reviewed research from PubMed
- Cross-reference information between sources
- Clearly cite sources when making claims
- Include relevant statistics and study findings
- Note any limitations or areas of uncertainty
- Provide actionable insights when appropriate
- Always recommend consulting healthcare professionals for personal medical advice"""),
            ("human", """Original Question: {query}

PubMed Research Summary:
{pubmed_summary}

Web Search Summary:
{web_summary}

Based on the above evidence, provide a comprehensive answer to the medical question. Structure your response with:
1. Key Findings
2. Evidence Summary
3. Clinical Implications (if applicable)
4. Recommendations""")
        ])
        
        self.synthesis_chain = self.synthesis_prompt | self.synthesizer_llm | StrOutputParser()
        self.memory = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(MedicalAgentState)
        
        workflow.add_node("pubmed_search", self._pubmed_search_node)
        workflow.add_node("web_search", self._web_search_node)
        workflow.add_node("synthesize", self._synthesize_node)
        
        workflow.set_entry_point("pubmed_search")
        workflow.add_edge("pubmed_search", "web_search")
        workflow.add_edge("web_search", "synthesize")
        workflow.add_edge("synthesize", END)
        
        return workflow.compile(checkpointer=self.memory)

    def _pubmed_search_node(self, state: MedicalAgentState) -> Dict[str, Any]:
        print(f"[PubMed Agent] Searching for: {state['query']}")
        
        result = self.pubmed_agent.retrieve(state["query"])
        
        return {
            "pubmed_results": result.get("results", []),
            "pubmed_summary": result.get("summary", "No summary available")
        }

    def _web_search_node(self, state: MedicalAgentState) -> Dict[str, Any]:
        print(f"[Web Search Agent] Searching for: {state['query']}")
        
        result = self.web_agent.retrieve(state["query"])
        
        return {
            "web_results": result.get("results", []),
            "web_summary": result.get("summary", "No summary available")
        }

    def _synthesize_node(self, state: MedicalAgentState) -> Dict[str, Any]:
        print("[Synthesizer Agent] Combining evidence...")
        
        try:
            answer = self.synthesis_chain.invoke({
                "query": state["query"],
                "pubmed_summary": state.get("pubmed_summary", "No PubMed results available"),
                "web_summary": state.get("web_summary", "No web results available")
            })
        except Exception as e:
            answer = f"Error during synthesis: {str(e)}"
        
        return {"final_answer": answer}

    def run(self, query: str, thread_id: str = "default") -> Dict[str, Any]:
        initial_state = {
            "query": query,
            "pubmed_results": [],
            "pubmed_summary": "",
            "web_results": [],
            "web_summary": "",
            "final_answer": "",
            "error": ""
        }
        
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            result = self.graph.invoke(initial_state, config)
            return {
                "query": query,
                "answer": result.get("final_answer", ""),
                "pubmed_results": result.get("pubmed_results", []),
                "pubmed_summary": result.get("pubmed_summary", ""),
                "web_results": result.get("web_results", []),
                "web_summary": result.get("web_summary", ""),
                "success": True
            }
        except Exception as e:
            return {
                "query": query,
                "answer": f"Error processing query: {str(e)}",
                "pubmed_results": [],
                "web_results": [],
                "success": False,
                "error": str(e)
            }

    async def arun(self, query: str, thread_id: str = "default") -> Dict[str, Any]:
        return self.run(query, thread_id)
