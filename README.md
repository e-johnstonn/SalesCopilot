# SalesGPT 🚀💸
SalesGPT is a sales assistant powered by Deep Lake, Whisper, and GPT 3.5. It transcribes your mic and speaker output in real-time, displaying it the "Transcript" tab. You can chat with SalesGPT about the transcript, asking for advice, summaries, and more. SalesGPT also checks the contents of the transcript every few seconds, detecting any objections from the customer. If an objection is detected, SalesGPT will give you unprompted advice on how to respond to the objection, powered by the knowledge base of your choosing. This knowledge based is embedded and stored using Deep Lake, allowing for the fast retrieval of relevant information from your knowledge base. 

Built with [Deep Lake](https://github.com/activeloopai/deeplake), [LangChain](https://github.com/hwchase17/langchain), and modified versions of [ecoute](https://github.com/SevaSk/ecoute) and [Speech Recognition](https://github.com/Uberi/speech_recognition). All open-source, check them out!

# Demo

Demo video here

# Setup 🔧 
- As of now only Windows is supported. A separate branch supporting macOS is coming soon!
- Ensure you have FFmpeg installed. If you don't, [here's a guide](https://phoenixnap.com/kb/ffmpeg-windows).
1. Clone the repository and navigate to the project directory 
  ```
  git clone https://github.com/e-johnstonn/salesGPT.git
     cd salesGPT       
  ```
2. Install required packages:
  ```pip install -r requirements.txt```
3. Set your OpenAI API key in `keys.env`
4. By default, audio will be transcribed using the Whisper API. If you have an NVIDIA GPU and want to transcribe locally, set ```USE_API``` to ```False``` in AudioTranscriber.py, and install [torch with CUDA](https://pytorch.org/get-started/locally/)

# Running SalesGPT
To start the program, ```python main.py``` in the project directory.

Enter a name for the person you're speaking to, click Start, and the app will load. In the "Sales Assistant" tab, you can chat with the GPT 3.5 powered Sales Assistant. This is also where advice regarding detected objections will appear. 

When the conversation is finished, you can click "Save and Quit" in the "Transcript" tab to save a copy of the transcript. If you restart the app, you can now load this transcript. Ask SalesGPT to summarize it, evaluate your performance, or any other questions related to the transcript. 

# Using your own knowledge base
By default, the app uses [this knowledge base](https://blog.hubspot.com/sales/handling-common-sales-objections), located in the `data` folder. To use your own knowledge base:
1. Put your knowledge base in the `data` folder in the form of a text file
2. Update the path in `chat_utils.py` to the path of your knowledge base
3. I recommend adjusing the ```split_data``` method in `deep_lake_utils.py` to split your document effectively

## License

[MIT License](LICENSE)

## 🤝 Contributing

Contributions are welcome! 




