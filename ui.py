import argparse
from zara import Zara
import gradio as gr
  

zara = Zara()

def chat_with_zara(user_message, chat_history):
    if chat_history is None:
        chat_history = []
    response = zara.gui(user_message)  
    chat_history.append((user_message, response))
    return chat_history, ""

def launch_gui():
    with gr.Blocks() as demo:
        gr.Markdown("<h1 style='text-align:center'>Zara AI Assistant</h1>")
        
        chatbot = gr.Chatbot(elem_id="chatbot", label="Chat")
        
        with gr.Row():
            with gr.Column(scale=12):
                txt = gr.Textbox(show_label=False, placeholder="Type your message here...", lines=1, elem_id="input_box")
            with gr.Column(scale=1, min_width=50):
                send_btn = gr.Button("Send")

        send_btn.click(chat_with_zara, inputs=[txt, chatbot], outputs=[chatbot, txt])
        txt.submit(chat_with_zara, inputs=[txt, chatbot], outputs=[chatbot, txt])
        
        demo.style = {
            "max_width": "700px",
            "margin": "auto",
            "height": "80vh",
            "display": "flex",
            "flex_direction": "column",
            "justify_content": "space-between"
        }

    demo.launch()

if __name__=="__main__":
    mode=input('Please enter mode cli or gui')
    if mode=='cli':
        zara.run()
    else:
        launch_gui()
        
        
      