# SalesGPT 🚀💸
SalesGPT is an AI-powered sales assistant that provides real-time transcription, live chat, automatic unprompted advice, integration with a custom knowledge base, and the ability to save and load past conversations. 

Built with [Deep Lake](https://github.com/activeloopai/deeplake), [LangChain](https://github.com/hwchase17/langchain), and modified versions of [ecoute](https://github.com/SevaSk/ecoute) and [Speech Recognition](https://github.com/Uberi/speech_recognition). All open-source, check them out!

## Features

- Real-Time Transcription: Transcribes your conversations with in real-time, maintaining a record in the 'Transcript' tab for review and analysis.
- Live Chat: Ask questions, get advice, and more with a chat bot that reads and understands the live transcript.
- Unprompted Advice: Potential objections or questions the customer has are detected, and advice on how to respond is offered within seconds.
- Knowledge Base Integration: Uses [Deep Lake](https://github.com/activeloopai/deeplake) as a vector database to store and retrieve information, allowing your chosen sales guidelines to be queried, with the most relevant being used to give advice.
- Save and Load Transcripts: Save transcripts, then load them up later and have it summarized, ask for a performance evaluation, and more. 

## Demo

https://github.com/e-johnstonn/salesGPT/assets/30129211/c5c86bc5-6516-4dcd-bba2-989caaaf563f

## Setup 🔧 
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

## Running SalesGPT
To start the program, ```python main.py``` in the project directory.

Enter a name for the person you're speaking to, click Start, and the app will load. In the "Sales Assistant" tab, you can chat with the GPT 3.5 powered Sales Assistant. This is also where advice regarding detected objections will appear. 

When the conversation is finished, you can click "Save and Quit" in the "Transcript" tab to save a copy of the transcript. If you restart the app, you can now load this transcript. Ask SalesGPT to summarize it, evaluate your performance, or any other questions related to the transcript. 

## Using your own knowledge base
By default, the app uses [this](https://blog.hubspot.com/sales/handling-common-sales-objections) as a knowledge base, located in the `data` folder. To use your own knowledge base:
1. Put your knowledge base in the `data` folder in the form of a text file
2. Update the path in `chat_utils.py` to the path of your knowledge base
3. I recommend adjusing the ```split_data``` method in `deep_lake_utils.py` to split your document effectively - if it's unstructured use something LangChain's RecursiveCharacterSplitter

## License

[MIT License](LICENSE)

## 🤝 Contributing

Contributions are welcome! 




