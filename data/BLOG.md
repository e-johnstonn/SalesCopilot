# Supercharging An AI Sales Assistant with Deep Lake
Discover how Deep Lake can be used to supercharge an AI sales assistant, SalesCopilot. In this post, we'll dive into the integration of a custom knowledge base with SalesCopilot, making it a more robust tool for handling customer objections. 
## What is SalesCopilot?

[SalesCopilot](https://github.com/e-johnstonn/SalesCopilot)  is a sales call assistant that transcribes audio in real-time and connects the user to a chatbot with full knowledge of the transcript, powered by GPT-3.5 or GPT-4. This live chat allows for highly relevant assistance to be provided within seconds upon the user's request. 

Additionally, SalesCopilot is able to detect potential objections from the customer (e.g. "It's too expensive" or "The product doesn't work for us") and provide well-informed recommendations to the salesperson on how best to handle them. Relying solely on the LLM to come up with these recommendations has some flaws - ChatGPT isn't fine tuned to be a great salesperson, and it may give recommendations that don't align with your personal approach. Integrating it with Deep Lake and a custom knowledge base is the perfect solution - let's dive into how it works!

![enter image description here](https://i.imgur.com/XTYSIWN.png)

## What Did and Didn't Work

Before we look at the exact solution we eventually decided on, let's take a glance at the approaches that didn't work, and what we learned from them:

### Didn't Work: No Custom Knowledge Base

This was the first solution we tried - instead of using a custom knowledge base, we could completely rely on the LLM. 

Unfortunately, we ran into some issues:
- **GPT-4 is awesome, but way too slow**: To get the highest quality responses without a custom knowledge base, using GPT-4 is the best choice. However, the time it takes for the API to return a response mean that by the time the user gets the advice they need, it's too late. This means we have to use GPT-3.5, which comes with a noticeable drop in quality.
- **Response quality is inconsistent**: Relying solely on the LLM, sometimes we get great responses that are exactly what we're looking for. However, without any additional info, guidelines, or domain-specific information, we also get bad responses that aren't very on-topic. 
- **Cramming information into the prompt is not token-efficient**: Using the OpenAI API, cost is a consideration, as you pay for the amount of tokens in your prompt + the completion. To ground the LLM and keep the responses high-quality, we could fill the prompt with tons of relevant information, how we'd like it to respond in different situations, etc. This solution isn't ideal, because it means every time we query the LLM we have to pass all that information, and all those tokens, to the API. The costs can add up, and GPT-3.5 can get confused if you give it too much info at once.

That didn't work - the main issue is that we need a way to efficiently ground the LLM's response. The next thing we tried was to use a custom knowledge base combined with a vector database to pass the LLM relevant info for each individual customer objection.

### Didn't Work: Naively Splitting the Custom Knowledge Base 
To leverage our custom knowledge base, our initial approach was to split the knowledge base into chunks of equal length using LangChain's built-in text splitters. Then we took the detected customer objection, embedded it, and searched the database for those chuhnks that were most relevant. This allowed us to pass relevant excerpts from our knowledge base to the LLM every time we wanted a response, which improved the quality of the responses and made the prompts to the LLM shorter and more efficient. However, our "naive" approach to splitting the custom knowledge base had a major flaw.

To illustrate the issue we faced, let's look at an example. Say we have the following text:

```
Objection: "There's no money."
It could be that your prospect's business simply isn't big enough or generating enough cash right now to afford a product like yours. Track their growth and see how you can help your prospect get to a place where your offering would fit into their business.

Objection: "We don't have any budget left this year."
A variation of the "no money" objection, what your prospect's telling you here is that they're having cash flow issues. But if there's a pressing problem, it needs to get solved eventually. Either help your prospect secure a budget from executives to buy now or arrange a follow-up call for when they expect funding to return.

Objection: "We need to use that budget somewhere else."
Prospects sometimes try to earmark resources for other uses. It's your job to make your product/service a priority that deserves budget allocation now. Share case studies of similar companies that have saved money, increased efficiency, or had a massive ROI with you.
```

If we naively split this text, we might end up with individual sections that look like this:

```
A variation of the "no money" objection, what your prospect's telling you here is that they're having cash flow issues. But if there's a pressing problem, it needs to get solved eventually. Either help your prospect secure a budget from executives to buy now or arrange a follow-up call for when they expect funding to return.

Objection: "We need to use that budget somewhere else."
```

Here, we see that the advice does not match the objection. When we try to retrieve the most relevant chunk for the objection "We need to use that budget somewhere else", this will likely be our top result, which isn't what we want. When we pass it to the LLM, it might be confusing.

What we really need to do is split the text in a more sophisticated way, that maintains semantic boundaries between each chunk. This will improve retrieval performance and keep the LLM responses higher quality.


### Did Work: Intelligent Splitting 
In our example text, there is a set structure to each individual objection and its recommended response. Rather than split the text based on size, why don't we split the text based on its structure? We want each chunk to begin with the objection, and end before the "Objection" of the next chunk. Here's how we could do it:

```python
text = """
Objection: "There's no money."
It could be that your prospect's business simply isn't big enough or generating enough cash right now to afford a product like yours. Track their growth and see how you can help your prospect get to a place where your offering would fit into their business.

Objection: "We don't have any budget left this year."
A variation of the "no money" objection, what your prospect's telling you here is that they're having cash flow issues. But if there's a pressing problem, it needs to get solved eventually. Either help your prospect secure a budget from executives to buy now or arrange a follow-up call for when they expect funding to return.

Objection: "We need to use that budget somewhere else."
Prospects sometimes try to earmark resources for other uses. It's your job to make your product/service a priority that deserves budget allocation now. Share case studies of similar companies that have saved money, increased efficiency, or had a massive ROI with you.
"""

# Split the text into a list using the keyword "Objection: "
objections_list = text.split("Objection: ")[1:]  # We ignore the first split as it is empty

# Now, prepend "Objection: " to each item as splitting removed it
objections_list = ["Objection: " + objection for objection in objections_list]
```

This gave us the best results. Nailing the way we split and embed our knowledge base means more relevant documents are retrieved and the LLM gets the best possible context to generate a response from. Now let's see how we integrated this solution with Deep Lake and SalesCopilot!


## Integrating SalesCopilot with Deep Lake

By using Deep Lake as a vector database, we can quickly and easily retrieve only the most relevant info to provide to the LLM. We can also persist the vector database, so we don't have to re-create it every time we load the app. The knowledge base we're using here is [this list of common customer objections](https://blog.hubspot.com/sales/handling-common-sales-objections). Before we get into the code, here's a rough overview of how it works:

![enter image description here](https://i.imgur.com/enyKesB.png)

First, we take our knowledge base and embed it, storing the embeddings in a Deep Lake vector database. Then, when we detect an objection in the transcript, we embed the objection and use it to search our database, retrieving the most similar guidelines. We then pass those guidelines along with the objection to the LLM and send the result to the user. 

### Creating, Loading, and Querying Our Database
We're going to define a class that handles the database creation, database loading, and database querying. 

```python
import os
import re
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import DeepLake

class DeepLakeLoader:
	def __init__(self, source_data_path):
	self.source_data_path = source_data_path
	self.file_name = os.path.basename(source_data_path) # What we'll name our database 
	self.data = self.split_data()
	if self.check_if_db_exists():
		self.db = self.load_db()
	else:
		self.db = self.create_db()
```
There's a few things happening here. First, the data is being processed by a method called ```split_data```:

```python
def split_data(self):  
	"""  
	Preprocess the data by splitting it into passages.  
	  
	If using a different data source, this function will need to be modified.  
	  
	Returns:  
		split_data (list): List of passages.  
	"""  
	with open(self.source_data_path, 'r') as f:  
		content = f.read()  
	split_data = re.split(r'(?=\d+\. )', content)
	if split_data[0] == '':  
		split_data.pop(0)  
	split_data = [entry for entry in split_data if len(entry) >= 30]  
	return split_data
```
Since we know the structure of our knowledge base, we use this method to split it into individual entries, each representing an example of a customer objection. When we run our similarity search using the detected customer objection, this will improve the results, as outlined above.

After preprocessing the data, we check if we've already created a database for this data. One of the great things about Deep Lake is that it provides us with persistent storage, so we only need to create the database once. If you restart the app, the database doesn't disappear!

Creating and loading the database is super easy:
```python
def load_db(self):  
	"""  
	Load the database if it already exists.  
	  
	Returns:  
		DeepLake: DeepLake object.  
	"""  
	return DeepLake(dataset_path=f'deeplake/{self.file_name}', embedding_function=OpenAIEmbeddings(), read_only=True)  
  
def create_db(self):  
	"""  
	Create the database if it does not already exist.  
	  
	Databases are stored in the deeplake directory.  
	  
	Returns:  
		DeepLake: DeepLake object.  
	"""  
	return DeepLake.from_texts(self.data, OpenAIEmbeddings(), dataset_path=f'deeplake/{self.file_name}')
```

Just like that, our knowledge base becomes a vector database that we can now query.

```python
def query_db(self, query):  
	"""  
	Query the database for passages that are similar to the query.  
	  
	Args:  
		query (str): Query string.  
	  
	Returns:  
		content (list): List of passages that are similar to the query.  
	"""  
	results = self.db.similarity_search(query, k=3)  
	content = []  
	for result in results:  
		content.append(result.page_content)  
	return content
```

We don't want the metadata to be passed to the LLM, so we take the results of our similarity search and pull just the content from them. And that's it! We now have our custom knowledge base stored in a Deep Lake vector database and ready to be queried!

### Connecting Our Database to the LLM
Now, all we need to do is connect our LLM to the database. First, we need to create a DeepLakeLoader instance with the path to our data.
```python
db = DeepLakeLoader('data/salestesting.txt')
```
Next, we take the detected objection and use it to query the database:

```python
results = db.query_db(detected_objection)
```
To have our LLM generate a message based off these results and the objection, we use [LangChain](https://github.com/hwchase17/langchain). In this example, we use a placeholder for the prompt - if you want to check out the prompts used in SalesCopilot, check out the [prompts.py file](https://github.com/e-johnstonn/SalesCopilot/blob/master/prompts.py).
```python
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage

chat = ChatOpenAI()
system_message = SystemMessage(content=objection_prompt)
human_message = HumanMessage(content=f'Customer objection: {detected_objection} | Relevant guidelines: {results}')

response = chat([system_message, human_message])
```
To print the response:
```python
print(response.content)
```

And we're done! In just a few lines of code, we've got our response from the LLM, informed by our own custom knowledge base.

If you want to check out the full code for SalesCopilot, [click here](https://github.com/e-johnstonn/SalesCopilot) to visit the GitHub repo.

##  The Power of Deep Lake - Leveraging Custom Knowledge Bases

Integrating SalesCopilot with Deep Lake allows for a significant enhancement of its capabilities, with immediate and relevant responses based on a custom knowledge base. The beauty of this solution is its adaptability. You can curate your knowledge base according to your own unique sales techniques and customer scenarios, ensuring SalesCopilot's responses are perfectly suited for your situation. 

An efficient vector storage solution is essential to working with large knowledge bases and connecting them to LLM's, allowing the LLM to offer knowledgeable, situation-specific advice. On top of that, Deep Lake's persistent storage means we only create the database once, which saves computational resources and time. 

In conclusion, the integration of SalesCopilot with Deep Lake creates a powerful tool that combines the speed and intelligence of LLM's with the rapid, precise information retrieval of a vector database. This hybrid system offers a highly adaptable, efficient, and effective solution to handling customer objections. The efficiency and simplicity Deep Lake brings to applications like this alongside its seamless integration make it a top choice for vector storage solutions.
