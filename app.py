"""
HuggingFace Spaces Entry Point

This is the main entry point for deploying the Gradio app to HuggingFace Spaces.
"""

from app.gradio_app import create_gradio_interface

# Create and launch the Gradio interface
demo = create_gradio_interface()

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
else:
    # For HuggingFace Spaces, the app is accessed via the demo object
    app = demo

