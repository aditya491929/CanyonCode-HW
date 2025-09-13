# In agent.py
import os
import logging
from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('agent_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Import tools from your tools file
from tools import execute_sql_query, get_parameter_value, get_schema_details

# Load environment variables
load_dotenv()

# --- Agent State ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]

# --- Tool and Model Setup ---
tools = [execute_sql_query, get_parameter_value, get_schema_details]

# Configure OpenAI client to work with OpenRouter + Deepseek
model = ChatOpenAI(
    model="deepseek/deepseek-chat",  # OpenRouter format for Deepseek
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0
)

# Bind tools to the model
model_with_tools = model.bind_tools(tools)

# --- System Prompt ---
SYSTEM_PROMPT = """You are an expert video analytics agent specializing in camera feed analysis and video encoding/decoding configurations. Your role is to help users query and understand camera feed data, encoder parameters, and decoder settings.

## Available Tools:

1. **execute_sql_query**: Query the camera feeds database
   - Table: 'camera_feeds' with columns: FEED_ID, THEATER, FRRATE, RES_W, RES_H, CODEC, ENCR, LAT_MS, MODL_TAG, CIV_OK
   - Table: 'table_definitions' with columns: header, type, allowed_values, description
   - Use for: Finding specific feeds, analyzing patterns, aggregating data

2. **get_parameter_value**: Retrieve encoder/decoder configuration values
   - Use for: Getting current parameter settings from JSON configs
   - Supports 'encoder' and 'decoder' config types

3. **get_schema_details**: Get parameter definitions and allowed values
   - Use for: Understanding what parameters mean and their valid ranges
   - Supports 'table', 'encoder', and 'decoder' schema types

## Database Schema Information:

### camera_feeds table:
- **FEED_ID**: Unique identifier (format: FD-[A-Z0-9]{6})
- **THEATER**: Operational theater (CONUS, PAC, EUR, ME, AFR, ARC)
- **FRRATE**: Frame rate in FPS (e.g., 23.976, 29.97, 59.94)
- **RES_W/RES_H**: Resolution width/height in pixels
- **CODEC**: Video codec (H264, H265, VP9, MPEG2, AV1)
- **ENCR**: Encryption enabled (True/False)
- **LAT_MS**: Latency in milliseconds
- **MODL_TAG**: Model/equipment tag
- **CIV_OK**: Civilian usage approved (True/False)

## Query Analysis Guidelines:

1. **Identify Intent**: Determine if the user wants:
   - Specific feed information (use FEED_ID filters)
   - Aggregate analysis (use GROUP BY, COUNT, AVG, etc.)
   - Configuration parameters (use get_parameter_value)
   - Schema definitions (use get_schema_details)

2. **SQL Query Best Practices**:
   - Use LIMIT for "top N" queries
   - Use ORDER BY for ranking (DESC for highest, ASC for lowest)
   - Use WHERE clauses for filtering by theater, codec, etc.
   - Use aggregate functions (COUNT, AVG, MIN, MAX) for statistics

3. **Response Format**:
   - Start with a clear, direct answer
   - Present data in a structured, readable format
   - Include relevant context and explanations
   - For numerical data, include units (ms for latency, fps for frame rate, etc.)
   - Suggest follow-up questions or related analyses when appropriate

## Example Query Patterns:

- "highest latency feeds" → ORDER BY LAT_MS DESC LIMIT N
- "feeds in PAC theater" → WHERE THEATER = 'PAC'
- "H265 codec usage" → WHERE CODEC = 'H265'
- "average frame rate" → SELECT AVG(FRRATE)
- "encoder preset" → get_parameter_value('encoder', 'preset')

## Response Style:
- Be conversational but professional
- Explain technical terms when needed
- Always verify data with actual queries before responding
- Format results clearly with headers and units
- Offer insights about the data when relevant

Remember: Always use tools to get accurate, current data. Never make assumptions about data values."""

# --- Graph Nodes ---

def agent(state: AgentState):
    """
    The agent node - the "brain" that plans and synthesizes responses.
    """
    logger.info("🧠 AGENT NODE: Starting agent processing...")
    messages = state["messages"]
    logger.info(f"📝 AGENT NODE: Processing {len(messages)} messages")
    
    # Add system prompt if this is the first message or if no system message exists
    if not messages or not isinstance(messages[0], SystemMessage):
        logger.info("🔧 AGENT NODE: Adding system prompt to conversation")
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    # Log the last user message for context
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, 'content'):
            logger.info(f"👤 AGENT NODE: Last user message: {last_message.content[:100]}...")
    
    logger.info("🤖 AGENT NODE: Invoking model with tools...")
    response = model_with_tools.invoke(messages)
    
    # Log tool calls if any
    if hasattr(response, 'tool_calls') and response.tool_calls:
        logger.info(f"🔧 AGENT NODE: Model requested {len(response.tool_calls)} tool calls:")
        for i, tool_call in enumerate(response.tool_calls):
            logger.info(f"  Tool {i+1}: {tool_call['name']} with args: {tool_call['args']}")
    else:
        logger.info("💬 AGENT NODE: Model provided final response (no tool calls)")
        if hasattr(response, 'content'):
            logger.info(f"📄 AGENT NODE: Response content preview: {response.content[:200]}...")
    
    logger.info("✅ AGENT NODE: Completed agent processing")
    return {"messages": [response]}

def ensure_system_prompt(state: AgentState) -> AgentState:
    """
    Ensures the system prompt is always present at the beginning of the conversation.
    """
    logger.info("🔧 SYSTEM_INIT NODE: Checking system prompt...")
    messages = state["messages"]
    
    if not messages or not isinstance(messages[0], SystemMessage):
        logger.info("➕ SYSTEM_INIT NODE: Adding system prompt to conversation")
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        return {"messages": messages}
    
    logger.info("✅ SYSTEM_INIT NODE: System prompt already present")
    return state

# Custom tool node with logging
def logged_tool_node(state: AgentState):
    """
    Custom tool node wrapper that logs tool executions.
    """
    logger.info("⚡ TOOL NODE: Starting tool execution...")
    messages = state["messages"]
    
    if not messages:
        logger.error("❌ TOOL NODE: No messages in state")
        return state
    
    last_message = messages[-1]
    
    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        logger.warning("⚠️ TOOL NODE: No tool calls found in last message")
        return state
    
    logger.info(f"🔧 TOOL NODE: Executing {len(last_message.tool_calls)} tool calls")
    
    # Execute tools using the standard ToolNode
    tool_executor = ToolNode(tools)
    result = tool_executor.invoke(state)
    
    # Log the results
    if "messages" in result:
        for i, message in enumerate(result["messages"]):
            if isinstance(message, ToolMessage):
                logger.info(f"📊 TOOL NODE: Tool {i+1} result preview: {str(message.content)[:200]}...")
    
    logger.info("✅ TOOL NODE: Completed tool execution")
    return result

# --- Conditional Edge ---
def should_continue(state: AgentState):
    """
    Determines whether to continue with tool execution or end.
    """
    logger.info("🔀 CONDITIONAL EDGE: Checking if should continue...")
    messages = state["messages"]
    
    if not messages:
        logger.warning("⚠️ CONDITIONAL EDGE: No messages found, ending")
        return "end"
    
    last_message = messages[-1]
    
    # If the last message has tool calls, continue to tool execution
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        logger.info(f"➡️ CONDITIONAL EDGE: Found {len(last_message.tool_calls)} tool calls, continuing to tool execution")
        return "continue"
    else:
        logger.info("🏁 CONDITIONAL EDGE: No tool calls found, ending conversation")
        return "end"

# --- Build and Compile the Graph ---
logger.info("🏗️ WORKFLOW: Building LangGraph workflow...")

workflow = StateGraph(AgentState)

# Add nodes
logger.info("📦 WORKFLOW: Adding nodes to workflow...")
workflow.add_node("system_init", ensure_system_prompt)
workflow.add_node("agent", agent)
workflow.add_node("action", logged_tool_node)  # Using logged version

# Set entry point
logger.info("🎯 WORKFLOW: Setting entry point to system_init...")
workflow.set_entry_point("system_init")

# Add edge from system initialization to agent
logger.info("🔗 WORKFLOW: Adding edge: system_init -> agent")
workflow.add_edge("system_init", "agent")

# Add conditional edges
logger.info("🔀 WORKFLOW: Adding conditional edges from agent...")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {"continue": "action", "end": END}
)

# Add edge from tool execution back to agent
logger.info("🔗 WORKFLOW: Adding edge: action -> agent")
workflow.add_edge("action", "agent")

# Compile the graph
logger.info("⚙️ WORKFLOW: Compiling workflow...")
app = workflow.compile()
logger.info("✅ WORKFLOW: Workflow compiled successfully!")

# Add wrapper to log workflow executions
class LoggedWorkflow:
    def __init__(self, workflow):
        self.workflow = workflow
    
    def stream(self, inputs, config=None):
        logger.info("🚀 WORKFLOW EXECUTION: Starting workflow stream...")
        logger.info(f"📥 WORKFLOW EXECUTION: Input messages: {len(inputs.get('messages', []))}")
        
        step_count = 0
        for output in self.workflow.stream(inputs, config):
            step_count += 1
            logger.info(f"📤 WORKFLOW EXECUTION: Step {step_count} - Nodes: {list(output.keys())}")
            yield output
        
        logger.info(f"🏁 WORKFLOW EXECUTION: Completed after {step_count} steps")
    
    def invoke(self, inputs, config=None):
        logger.info("🚀 WORKFLOW EXECUTION: Starting workflow invoke...")
        result = self.workflow.invoke(inputs, config)
        logger.info("🏁 WORKFLOW EXECUTION: Invoke completed")
        return result

app = LoggedWorkflow(app)
