# In app.py
import streamlit as st
from agent import app
from langchain_core.messages import HumanMessage, AIMessage

st.set_page_config(
    page_title="Canyon Code Agent", 
    page_icon="🏞️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main title and description
st.title("Canyon Code Query Agent 🏞️")
st.caption("Ask me anything about the camera feeds, encoder, or decoder configurations.")

# Sidebar with information
with st.sidebar:
    st.header("🔧 System Information")
    st.info("""
    **Available Data:**
    - 📹 Camera feeds database (100 records)
    - ⚙️ Encoder parameters
    - 🔄 Decoder parameters
    - 📋 Schema definitions
    
    **Sample Queries:**
    - "Which 5 feeds have the highest latency?"
    - "What codec is used for feed FD-ML64LG?"
    - "Show me all feeds in the PAC theater"
    - "What preset is the encoder using?"
    - "What are the allowed values for THEATER?"
    """)
    
    if st.button("🔄 Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        AIMessage(content="Hello! I'm your Canyon Code Query Agent. How can I help you analyze the camera feeds, encoder, or decoder configurations today?")
    ]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message.type):
        st.markdown(message.content)

# Main input loop
if prompt := st.chat_input("Ask me about camera feeds, encoder settings, decoder configs, or schema details..."):
    # Add user message to chat history
    st.session_state.messages.append(HumanMessage(content=prompt))
    
    # Display user message
    with st.chat_message("human"):
        st.markdown(prompt)

    # Display assistant response
    with st.chat_message("ai"):
        with st.spinner("🤔 Analyzing your query..."):
            try:
                # The input is the entire conversation history
                inputs = {"messages": st.session_state.messages}

                final_response = None
                message_placeholder = st.empty()

                # Stream the response from the agent
                for output in app.stream(inputs, {"recursion_limit": 10}):
                    # The final answer is in the 'agent' node's last message
                    if "agent" in output:
                        final_response = output["agent"]["messages"][-1]
                        # Update the placeholder with the current response
                        message_placeholder.markdown(final_response.content)

                # Add the final response to chat history
                if final_response:
                    st.session_state.messages.append(AIMessage(content=final_response.content))
                else:
                    error_message = "I apologize, but I encountered an issue processing your request. Please try again."
                    message_placeholder.markdown(error_message)
                    st.session_state.messages.append(AIMessage(content=error_message))

            except Exception as e:
                error_message = f"I encountered an error: {str(e)}. Please check your API key configuration and try again."
                st.error(error_message)
                st.session_state.messages.append(AIMessage(content=error_message))

# Footer
st.markdown("---")
st.markdown("💡 **Tip:** Be specific in your queries for better results. I can analyze camera feeds, retrieve configuration parameters, and explain schema definitions.")
