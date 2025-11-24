"""
HuggingFace Spaces Entry Point

This is the main entry point for deploying the Gradio app to HuggingFace Spaces.
"""

from app.gradio_app import create_gradio_interface

# Create and launch the Gradio interface
demo = create_gradio_interface()
demo.launch()
