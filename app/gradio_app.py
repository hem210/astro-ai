"""
Gradio Interface for Astrology Agent

Provides a conversational UI for interacting with the astrology agent.
"""

import gradio as gr
from gradio import ChatMessage
from typing import Optional, Tuple, List, Dict, Any
from app.services.agent.astrology_agent import AstrologyAgent
from app.services.agent.config import AGENT_MODEL, SUPPORTED_MODELS, get_all_model_configs
from langchain_core.messages import HumanMessage, AIMessage


class GradioAgentInterface:
    """Gradio interface wrapper for the astrology agent."""
    
    def __init__(self):
        """Initialize the interface."""
        self.agent: Optional[AstrologyAgent] = None
        self.current_model: str = AGENT_MODEL
        self.conversation_history: list = []
        self.birth_details: Optional[dict] = None
    
    def initialize_agent(self, model_name: str) -> str:
        """
        Initialize or reinitialize the agent with a specific model.
        
        Args:
            model_name: Name of the model to use
        
        Returns:
            Status message
        """
        try:
            self.current_model = model_name
            self.agent = AstrologyAgent(model_name=model_name)
            self.conversation_history = []
            return f"Agent initialized with model: {model_name}"
        except Exception as e:
            return f"Error initializing agent: {str(e)}"
    
    def set_birth_details(self, day: int, month: int, year: int, hour: int, minute: int, birth_place: str) -> str:
        """
        Store birth details for kundali generation.
        
        Args:
            day: Day of birth
            month: Month of birth
            year: Year of birth
            hour: Hour of birth
            minute: Minute of birth
            birth_place: Birth place
        
        Returns:
            Status message
        """
        try:
            self.birth_details = {
                "day": day,
                "month": month,
                "year": year,
                "hour": hour,
                "minute": minute,
                "birth_place": birth_place
            }
            return f"Birth details saved: {day}/{month}/{year} at {hour:02d}:{minute:02d} in {birth_place}"
        except Exception as e:
            return f"Error saving birth details: {str(e)}"
    
    def chat(self, message: str, history: List[ChatMessage]) -> Tuple[List[ChatMessage], str]:
        """
        Handle chat interaction.
        
        Args:
            message: User message
            history: Gradio chat history (list of ChatMessage objects)
        
        Returns:
            Updated history and empty message string
        """
        if not message.strip():
            return history, ""
        
        # Ensure history is a list
        if history is None:
            history = []
        
        # Initialize agent if not already initialized
        if self.agent is None:
            try:
                self.agent = AstrologyAgent(model_name=self.current_model)
            except Exception as e:
                error_msg = f"Error initializing agent: {str(e)}"
                # Append ChatMessage objects
                history.append(ChatMessage(role="user", content=message))
                history.append(ChatMessage(role="assistant", content=error_msg))
                return history, ""
        
        try:
            # Convert Gradio ChatMessage history to LangChain messages
            langchain_messages = []
            for chat_msg in history:
                if isinstance(chat_msg, ChatMessage):
                    if chat_msg.role == "user":
                        langchain_messages.append(HumanMessage(content=str(chat_msg.content)))
                    elif chat_msg.role == "assistant":
                        langchain_messages.append(AIMessage(content=str(chat_msg.content)))
            
            # If birth details are available, add context to the message
            enhanced_message = message
            if self.birth_details:
                birth_info = (
                    f"Note: My birth details are - Date: {self.birth_details['day']}/{self.birth_details['month']}/"
                    f"{self.birth_details['year']}, Time: {self.birth_details['hour']:02d}:{self.birth_details['minute']:02d}, "
                    f"Place: {self.birth_details['birth_place']}. "
                )
                enhanced_message = birth_info + message
            
            # Invoke agent
            response = self.agent.invoke(enhanced_message, conversation_history=langchain_messages)
            
            # Update history with ChatMessage objects (Gradio 6.0 format)
            history.append(ChatMessage(role="user", content=message))
            history.append(ChatMessage(role="assistant", content=str(response)))
            
            # Update conversation history (only store user and assistant messages, not tool messages)
            # This prevents "missing tool call" errors when history is reused
            from langchain_core.messages import ToolMessage
            self.conversation_history = [
                msg for msg in langchain_messages 
                if not isinstance(msg, ToolMessage)
            ]
            self.conversation_history.append(HumanMessage(content=enhanced_message))
            self.conversation_history.append(AIMessage(content=response))
            
            return history, ""
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            # Append ChatMessage objects
            history.append(ChatMessage(role="user", content=message))
            history.append(ChatMessage(role="assistant", content=error_msg))
            return history, ""
    
    def clear_history(self) -> Tuple[List[ChatMessage], str]:
        """
        Clear conversation history.
        
        Returns:
            Empty history and status message
        """
        self.conversation_history = []
        return [], "Conversation history cleared."


def create_gradio_interface():
    """Create and return the Gradio interface."""
    # Ensure both API keys are loaded and validated at startup
    try:
        configs = get_all_model_configs()
        print(f"✓ Loaded {len(configs)} model configurations (both API keys validated)")
    except Exception as e:
        print(f"Warning: Could not load all model configurations: {e}")
    
    interface = GradioAgentInterface()
    
    # Initialize agent on startup
    try:
        interface.initialize_agent(AGENT_MODEL)
    except Exception as e:
        print(f"Warning: Could not initialize agent on startup: {e}")
    
    # Create Gradio blocks
    with gr.Blocks(title="Vedic Astrology Assistant") as demo:
        gr.Markdown(
            """
            # 🔮 Vedic Astrology Assistant
            
            Ask me anything about Vedic astrology! I can:
            - Generate your kundali (natal chart) from birth details
            - Interpret planetary positions in houses and signs
            - Explain ascendant signs and nakshatras
            - Analyze planetary conjunctions
            - Provide personalized astrological insights
            """
        )
        
        # Birth Details Form Section
        with gr.Accordion("📅 Enter Your Birth Details (Optional but Recommended)", open=True):
            with gr.Row():
                birth_day = gr.Number(
                    label="Day",
                    value=1,
                    minimum=1,
                    maximum=31,
                    precision=0,
                    info="Day of birth (1-31)"
                )
                birth_month = gr.Number(
                    label="Month",
                    value=1,
                    minimum=1,
                    maximum=12,
                    precision=0,
                    info="Month of birth (1-12)"
                )
                birth_year = gr.Number(
                    label="Year",
                    value=2000,
                    minimum=1800,
                    maximum=2399,
                    precision=0,
                    info="Year of birth"
                )
            with gr.Row():
                birth_hour = gr.Number(
                    label="Hour",
                    value=12,
                    minimum=0,
                    maximum=23,
                    precision=0,
                    info="Hour of birth (0-23, 24-hour format)"
                )
                birth_minute = gr.Number(
                    label="Minute",
                    value=0,
                    minimum=0,
                    maximum=59,
                    precision=0,
                    info="Minute of birth (0-59)"
                )
            birth_place = gr.Textbox(
                label="Birth Place",
                value="Ahmedabad, Gujarat, India",
                placeholder="Enter city, state, country",
                info="Your place of birth"
            )
            save_birth_details_btn = gr.Button("Save Birth Details", variant="primary")
            birth_details_status = gr.Textbox(
                label="Status",
                value="Please enter your birth details above and click 'Save Birth Details'",
                interactive=False
            )
        
        with gr.Row():
            with gr.Column(scale=1):
                model_dropdown = gr.Dropdown(
                    choices=list(SUPPORTED_MODELS.keys()),
                    value=AGENT_MODEL,
                    label="Model",
                    info="Select the LLM model to use"
                )
                
                model_status = gr.Textbox(
                    label="Model Status",
                    value=f"Current model: {AGENT_MODEL}",
                    interactive=False
                )
                
                clear_btn = gr.Button("Clear History", variant="secondary")
                
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=500,
                    value=[]
                )
                
                msg = gr.Textbox(
                    label="Your Message",
                    placeholder="Ask about your chart, planetary positions, or any astrological question...",
                    lines=3
                )
                
                submit_btn = gr.Button("Send", variant="primary", scale=1)
        
        # Event handlers
        def save_birth_details(day, month, year, hour, minute, place):
            """Save birth details."""
            status = interface.set_birth_details(int(day), int(month), int(year), int(hour), int(minute), place)
            return status
        
        def update_model(model_name: str):
            """Update the model."""
            status = interface.initialize_agent(model_name)
            return status, f"Current model: {model_name}"
        
        def handle_submit(message: str, history: list):
            """Handle message submission."""
            return interface.chat(message, history)
        
        def handle_clear():
            """Handle clear history."""
            return interface.clear_history()
        
        # Connect events
        save_birth_details_btn.click(
            fn=save_birth_details,
            inputs=[birth_day, birth_month, birth_year, birth_hour, birth_minute, birth_place],
            outputs=[birth_details_status]
        )
        
        model_dropdown.change(
            fn=update_model,
            inputs=[model_dropdown],
            outputs=[model_status, model_status]
        )
        
        submit_btn.click(
            fn=handle_submit,
            inputs=[msg, chatbot],
            outputs=[chatbot, msg]
        )
        
        msg.submit(
            fn=handle_submit,
            inputs=[msg, chatbot],
            outputs=[chatbot, msg]
        )
        
        clear_btn.click(
            fn=handle_clear,
            outputs=[chatbot, model_status]
        )
    
    return demo


if __name__ == "__main__":
    demo = create_gradio_interface()
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)

