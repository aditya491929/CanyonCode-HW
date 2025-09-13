# In tools.py
import json
import logging
import pandas as pd
from sqlalchemy import create_engine
from langchain_core.tools import tool

# Configure logging for tools
logging.basicConfig(level=logging.INFO)
tool_logger = logging.getLogger("tools")

# --- Data and DB Setup ---
DB_FILE = "canyon_code.db"
engine = create_engine(f"sqlite:///{DB_FILE}")

# Load JSON configuration files
with open('data/encoder_params.json', 'r') as f:
    encoder_params = json.load(f)
with open('data/decoder_params.json', 'r') as f:
    decoder_params = json.load(f)
with open('data/encoder_schema.json', 'r') as f:
    encoder_schema = json.load(f)
with open('data/decoder_schema.json', 'r') as f:
    decoder_schema = json.load(f)

# --- Tool Definitions ---

@tool
def execute_sql_query(sql_query: str) -> str:
    """
    Executes a read-only SQL query against the database and returns the result.
    The database has a table named 'camera_feeds' with columns:
    FEED_ID, THEATER, FRRATE, RES_W, RES_H, CODEC, ENCR, LAT_MS, MODL_TAG, CIV_OK.
    
    It also has a 'table_definitions' table with columns:
    header, type, allowed_values, description.
    
    Only SELECT statements are permitted.
    
    Args:
        sql_query: The SQL SELECT query to execute
        
    Returns:
        String representation of the query results
    """
    tool_logger.info("🔍 EXECUTE_SQL_QUERY: Tool called!")
    tool_logger.info(f"📝 EXECUTE_SQL_QUERY: Query: {sql_query}")
    
    if not sql_query.strip().upper().startswith("SELECT"):
        error_msg = "Error: Only SELECT queries are allowed."
        tool_logger.error(f"❌ EXECUTE_SQL_QUERY: {error_msg}")
        return error_msg
    
    try:
        tool_logger.info("🔗 EXECUTE_SQL_QUERY: Connecting to database...")
        with engine.connect() as connection:
            df = pd.read_sql_query(sql_query, connection)
            if df.empty:
                result = "No results found."
                tool_logger.warning("⚠️ EXECUTE_SQL_QUERY: No results found")
            else:
                result = df.to_string(index=False)
                tool_logger.info(f"✅ EXECUTE_SQL_QUERY: Found {len(df)} rows")
                tool_logger.info(f"📊 EXECUTE_SQL_QUERY: Result preview: {result[:200]}...")
            return result
    except Exception as e:
        error_msg = f"Query failed with error: {e}"
        tool_logger.error(f"❌ EXECUTE_SQL_QUERY: {error_msg}")
        return error_msg

@tool
def get_parameter_value(config_type: str, parameter_name: str) -> str:
    """
    Retrieves the value of a parameter from the 'encoder' or 'decoder' JSON config files.
    
    Args:
        config_type: Either 'encoder' or 'decoder'
        parameter_name: The name of the parameter to retrieve
        
    Returns:
        String representation of the parameter value
    """
    tool_logger.info("⚙️ GET_PARAMETER_VALUE: Tool called!")
    tool_logger.info(f"📝 GET_PARAMETER_VALUE: Config type: {config_type}, Parameter: {parameter_name}")
    
    if config_type == 'encoder':
        value = encoder_params.get(parameter_name, 'Not found')
        result = f"The value of '{parameter_name}' in encoder config is: {value}"
        tool_logger.info(f"✅ GET_PARAMETER_VALUE: Found encoder parameter: {value}")
        return result
    elif config_type == 'decoder':
        value = decoder_params.get(parameter_name, 'Not found')
        result = f"The value of '{parameter_name}' in decoder config is: {value}"
        tool_logger.info(f"✅ GET_PARAMETER_VALUE: Found decoder parameter: {value}")
        return result
    else:
        error_msg = "Error: config_type must be 'encoder' or 'decoder'."
        tool_logger.error(f"❌ GET_PARAMETER_VALUE: {error_msg}")
        return error_msg

@tool
def get_schema_details(schema_type: str, parameter_name: str) -> str:
    """
    Retrieves the definition for a parameter.
    For schema_type 'table', it queries the SQL 'table_definitions' table.
    For 'encoder' or 'decoder', it checks the JSON schema files.
    
    Args:
        schema_type: 'table', 'encoder', or 'decoder'
        parameter_name: The name of the parameter to get schema details for
        
    Returns:
        String representation of the schema details
    """
    tool_logger.info("📋 GET_SCHEMA_DETAILS: Tool called!")
    tool_logger.info(f"📝 GET_SCHEMA_DETAILS: Schema type: {schema_type}, Parameter: {parameter_name}")
    
    if schema_type == 'table':
        tool_logger.info("🗃️ GET_SCHEMA_DETAILS: Querying table definitions...")
        query = f"SELECT * FROM table_definitions WHERE header = '{parameter_name}'"
        result = execute_sql_query(query)
        tool_logger.info("✅ GET_SCHEMA_DETAILS: Table schema query completed")
        return result
    elif schema_type == 'encoder':
        param_schema = encoder_schema['properties'].get(parameter_name, {'description': 'Not found'})
        result = json.dumps(param_schema, indent=2)
        tool_logger.info(f"✅ GET_SCHEMA_DETAILS: Found encoder schema for {parameter_name}")
        return result
    elif schema_type == 'decoder':
        param_schema = decoder_schema['properties'].get(parameter_name, {'description': 'Not found'})
        result = json.dumps(param_schema, indent=2)
        tool_logger.info(f"✅ GET_SCHEMA_DETAILS: Found decoder schema for {parameter_name}")
        return result
    else:
        error_msg = "Error: schema_type must be 'table', 'encoder', or 'decoder'."
        tool_logger.error(f"❌ GET_SCHEMA_DETAILS: {error_msg}")
        return error_msg
