from app.core.graph_rag_pipeline import get_graph_rag_pipeline
from app.core.hybrid_pipeline import get_hybrid_pipeline
from app.mcp.server import mcp_server


@mcp_server.tool()
async def graph_query(question: str, include_documents: bool = False) -> str:
    """Query the CMMS knowledge graph using natural language.

    Args:
        question: Natural language question about CMMS data
        include_documents: Also search documents (enables hybrid mode)
    """
    if include_documents:
        pipeline = get_hybrid_pipeline()
        result = await pipeline.query(question)
    else:
        pipeline = get_graph_rag_pipeline()
        result = await pipeline.query(question)

    response = result.get("answer", "No answer generated.")

    if result.get("cypher_used"):
        response += f"\n\n[Cypher used: {result['cypher_used']}]"

    return response


@mcp_server.tool()
async def hybrid_query(question: str) -> str:
    """Query across both knowledge graph and documents using natural language.

    Args:
        question: Natural language question requiring both structured and unstructured data
    """
    pipeline = get_hybrid_pipeline()
    result = await pipeline.query(question)

    response = result.get("answer", "No answer generated.")

    if result.get("cypher_used"):
        response += f"\n\n[Graph query: {result['cypher_used']}]"

    sources = result.get("sources", [])
    if sources:
        response += "\n\n[Document sources: " + ", ".join(
            s.get("filename", "Unknown") for s in sources
        ) + "]"

    return response
