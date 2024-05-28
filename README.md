<div align="center">

[![pathwaycom/llm-app: Build your LLM App in 30 lines of code](https://d14l3brkh44201.cloudfront.net/pathway-llm.png)](https://pathway.com/)

# LLM App

[![LICENSE](https://img.shields.io/github/license/pathwaycom/llm-app?style=plastic)](https://github.com/pathwaycom/llm-app/blob/main/LICENSE)
[![Contributors](https://img.shields.io/github/contributors/pathwaycom/llm-app?style=plastic)](https://github.com/pathwaycom/llm-app/graphs/contributors)

<!--- [![Contributors](https://img.shields.io/github/actions/workflow/status/pathwaycom/llm-app/install_package.yml?style=plastic)](https://github.com/pathwaycom/llm-app/actions/workflows/install_package.yml) --->
![Linux](https://img.shields.io/badge/OS-Linux-green)
![macOS](https://img.shields.io/badge/OS-macOS-green)
[![chat on Discord](https://img.shields.io/discord/1042405378304004156?logo=discord)](https://discord.gg/pathway)
[![follow on Twitter](https://img.shields.io/twitter/follow/pathway_com?style=social&logo=twitter)](https://twitter.com/intent/follow?screen_name=pathway_com)
</div>

Pathway's **LLM (Large Language Model) Apps** allow you to quickly put in production AI applications which use the most up-to-date knowledge available in your data sources. You can directly run a 24/7 service to answer natural language queries about an ever-changing private document knowledge base, or run an LLM-powered data transformation pipeline on a data stream. 

The Python application examples provided in this repo are ready-to-use. They can be run as Docker containers, and expose an HTTP API to the frontend. To allow quick testing and demos, most app examples also include an optional Streamlit UI which connects to this API. The apps rely on the [Pathway framework](https://github.com/pathwaycom/pathway) for data source synchronization, for serving API requests, and for all low-latency data processing. The apps connect to document data sources on S3, Google Drive, Sharepoint, etc. with no infrastructure dependencies (such as a vector database) that would need a separate setup.

**Quick links** - 👀 [Why use Pathway LLM Apps?](#why-use-pathway-llm-apps) 🚀 [Watch it in action](#watch-it-in-action) 📚 [How it works](#how-it-works) 🌟 [Application examples](#application-examples) 🏁 [Get Started](#get-started) 💼 [Showcases](#showcases) 🛠️ [Troubleshooting](#troubleshooting)
👥 [Contributing](#troubleshooting) ⚙️ [Hosted Version](#%EF%B8%8F-hosted-version-%EF%B8%8F) 💡 [Need help?](#need-help) 

## Why use Pathway LLM Apps?

1. **Simplicity** - Simplify your AI pipeline by consolidating capabilities into one platform. No need to integrate and maintain separate modules for your Gen AI app: ~Vector Database (e.g. Pinecone/Weaviate/Qdrant) + Cache (e.g. Redis) + API Framework (e.g. Fast API)~.
2. **Real-time data syncing** - Sync both structured and unstructured data from diverse sources, enabling real-time Retrieval Augmented Generation (RAG).
3. **Easy alert setup** - Configure alerts for key business events with simple configurations. Ask a question, and get updated when new info is available.  
4. **Scalability** - Handle heavy data loads and usage without degradation in performance. Metrics help track usage and scalability. Learn more about the performance of the underlying [Pathway data processing framework](https://github.com/pathwaycom/pathway/).
5. **Monitoring** - Provide visibility into model behavior via monitoring, tracing errors, anomaly detection, and replay for debugging. Helps with response quality.
6. **Security** - Designed for Enterprise, with capabilities like Personally Identifiable Information (PII) detection, content moderation, permissions, and version control. Pathway apps can run in your private cloud with local LLMs.
7. **Unification** - Cover multiple aspects of your choice with a unified application logic: back-end, embedding, retrieval, LLM tech stack.

## Watch it in action

### Effortlessly extract and organize unstructured data from PDFs, docs, and more into SQL tables - in real-time.

Analysis of live documents streams.

![Effortlessly extract and organize unstructured data from PDFs, docs, and more into SQL tables - in real-time](examples/pipelines/unstructured_to_sql_on_the_fly/unstructured_to_sql_demo.gif)


(Check out: [`gpt_4o_multimodal_rag`](examples/pipelines/gpt_4o_multimodal_rag/README.md) to see the whole pipeline in the works. You may also check out: [`unstructured-to-sql`](examples/pipelines/unstructured_to_sql_on_the_fly/app.py) for a minimal example which works with non-multimodal models as well.)


### Automated real-time knowledge mining and alerting. 

Monitor streams of changing documents, get real-time alerts when answers change. 

Using incremental vector search, only the most relevant context is automatically passed into the LLM for analysis, minimizing token use - even when thousands of documents change every minute. This is real-time RAG taken to a new level 😊.

![Automated real-time knowledge mining and alerting](examples/pipelines/drive_alert/drive_alert_demo.gif)

For the code, see the [`drive_alert`](#examples) app example. You can find more details in a [blog post on alerting with LLM-App](https://pathway.com/developers/showcases/llm-alert-pathway).


## How it works

The default [`contextful`](examples/pipelines/contextful/app.py) app example launches an application that connects to a source folder with documents, stored in [AWS S3](https://aws.amazon.com/s3/) or locally on your computer. The app is **always in sync** with updates to your documents, building in real-time a "vector index" using the Pathway package. It waits for user queries that come as HTTP REST requests, then uses the index to find relevant documents and responds using [OpenAI API](https://openai.com/blog/openai-api) or [Hugging Face](https://huggingface.co/) in natural language. This way, it provides answers that are always best on the freshest and most accurate **real-time data**.

This application template can also be combined with streams of fresh data, such as news feeds or status reports, either through REST or a technology like Kafka. It can also be combined with extra static data sources and user-specific contexts, to provide more relevant answers and reduce LLM hallucination.

Read more about the implementation details and how to extend this application in [our blog article](https://pathway.com/developers/user-guide/llm-xpack/llm-app-pathway/).

### Instructional videos

▶️ [Building an LLM Application without a vector database](https://www.youtube.com/watch?v=kcrJSk00duw) - by [Jan Chorowski](https://scholar.google.com/citations?user=Yc94070AAAAJ)

▶️ [Let's build a real-world LLM app in 11 minutes](https://www.youtube.com/watch?v=k1XGo7ts4tI) - by [Pau Labarta Bajo](https://substack.com/@paulabartabajo)


## Advanced Features

LLM Apps built with Pathway can also include the following capabilities:

* **Local Machine Learning models** - Pathway LLM Apps can run with local LLMs and embedding models, without making API calls outside of the User's Organization.
* **Multiple live data sources** - Pathway LLM Apps can [connect to live data sources](https://pathway.com/developers/user-guide/connecting-to-data/connectors/) of diverse types (news feeds, APIs, data streams in Kafka, and others),
* **Extensible enterprise logic** - user permissions, user session handling, and a data security layer can all be embedded in your application logic by integrating with your enterprise SSO, AD Domains, LDAP, etc.
* **Live knowledge graphs** - the Pathway framework enables concept mining, organizing data and metadata as knowledge graphs, and knowledge-graph-based indexes, kept in sync with live data sources.

To learn more about advanced features see: [Features for Organizations](FEATURES-for-organizations.md), or reach out to the Pathway team.


## Application Examples

Pick one that is closest to your needs.

| Example app (template)                                                                           | Description                                                                                                                                                                                                                                                                                                                                                         |
| --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`demo-question-answering`](examples/pipelines/demo-question-answering/app.py)    | The question-answering pipeline that uses the GPT model of choice to provide answers to the queries about a set of documents. You can also try it on the Pathway [Hosted Pipelines website](https://cloud.pathway.com).              |
| [`demo-document-indexing`](examples/pipelines/demo-document-indexing/main.py)     | The real-time document indexing pipeline that provides the monitoring of several kinds of data sources and health-check endpoints. It is available on the Pathway [Hosted Pipelines website](https://cloud.pathway.com).         |
| [`contextless`](examples/pipelines/contextless/app.py)                            | This simple example calls OpenAI ChatGPT API but does not use an index when processing queries. It relies solely on the given user query. We recommend it to start your Pathway LLM journey.                                                                                                                                                                        |
| [`contextful`](examples/pipelines/contextful/app.py)                              | This default example of the app will index the jsonlines documents located in the [`data/pathway-docs`](examples/data/pathway-docs) directory. These indexed documents are then taken into account when processing queries. |
| [`contextful-s3`](examples/pipelines/contextful_s3/app.py)                        | This example operates similarly to the contextful mode. The main difference is that the documents are stored and indexed from an S3 bucket, allowing the handling of a larger volume of documents. This can be more suitable for production environments.                                                                                                           |
| [`contextful-parsing`](examples/pipelines/contextful_parsing/app.py)                          | Process unstructured documents such as PDF, HTML, DOCX, PPTX, and more. Visit [unstructured-io](https://unstructured-io.github.io/unstructured/) for the full list of supported formats.                                                                                                                                                                            |
| [`local`](examples/pipelines/local/app.py)                                        | This example runs the application using Huggingface Transformers, which eliminates the need for the data to leave the machine. It provides a convenient way to use state-of-the-art NLP models locally.                                                                                                                                                             |
| [`unstructured-to-sql`](examples/pipelines/unstructured_to_sql_on_the_fly/app.py) | This example extracts the data from unstructured files and stores it into a PostgreSQL table. It also transforms the user query into an SQL query which is then executed on the PostgreSQL table.                                                                                                                                                                   |
| [`alert`](examples/pipelines/alert/app.py)                                        | Ask questions, get alerted whenever response changes. Pathway is always listening for changes, whenever new relevant information is added to the stream (local files in this example), LLM decides if there is a substantial difference in response and notifies the user with a Slack message.                                                                     |
| [`drive-alert`](examples/pipelines/drive_alert/app.py)                            | The [`alert`](examples/pipelines/alert/app.py) example on steroids. Whenever relevant information on Google Docs is modified or added, get real-time alerts via Slack. See the [`tutorial`](https://pathway.com/developers/showcases/llm-alert-pathway).                                                                                                            |
| [`contextful-geometric`](examples/pipelines/contextful_geometric/app.py)          | The [`contextful`](examples/pipelines/contextful/app.py) example, which optimises use of tokens in queries. It asks the same questions
with increasing number of documents given as a context in the question, until ChatGPT finds an answer.                                                                                                               |


## Get Started

### Prerequisites


1. Make sure that [Python](https://www.python.org/downloads/) 3.10 or above installed on your machine.
2. Download and Install [Pip](https://pip.pypa.io/en/stable/installation/) to manage project packages.
3. [Optional if you use OpenAI models]. Create an [OpenAI](https://openai.com/) account and generate a new API Key: To access the OpenAI API, you will need to create an API Key. You can do this by logging into the [OpenAI website](https://openai.com/product) and navigating to the API Key management page.
4. [Important if you use Windows OS]. The examples only support Unix-like systems (such as Linux, macOS, and BSD). If you are a Windows user, we highly recommend leveraging [Windows Subsystem for Linux (WSL)](https://learn.microsoft.com/en-us/windows/wsl/install) or Dockerize the app to run as a container.
5. [Optional if you use Docker to run samples]. Download and install [docker](https://www.docker.com/).

Now, follow the steps to install and [get started with one of the provided examples](#examples). You can pick any example that you find interesting - if not sure, pick `contextful`.

Alternatively, you can also take a look at the [application showcases](#showcases).

### Clone the repository

This is done with the `git clone` command followed by the URL of the repository:

```bash
git clone https://github.com/pathwaycom/llm-app.git
```

### Run the chosen example

Each [example](examples/pipelines/) contains a README.md with instructions on how to run it.

### Bonus: Build your own Pathway-powered LLM App

Want to learn more about building your own app? See step-by-step guide [Building a llm-app tutorial](https://pathway.com/developers/showcases/llm-app-pathway)

Or,

Simply add `llm-app` to your project's dependencies and copy one of the [examples](#examples) to get started!

## Showcases

* [Python sales](https://github.com/pathway-labs/chatgpt-api-python-sales) - Find real-time sales with AI-powered Python API using ChatGPT and LLM (Large Language Model) App.

* [Dropbox Data Observability](https://github.com/pathway-labs/dropbox-ai-chat) - See how to get started with chatting with your Dropbox and having data observability. 

## Troubleshooting

Please check out our [Q&A](https://github.com/pathwaycom/llm-app/discussions/categories/q-a) to get solutions for common installation problems and other issues.

### Raise an issue

To provide feedback or report a bug, please [raise an issue on our issue tracker](https://github.com/pathwaycom/pathway/issues).

## Contributing

Anyone who wishes to contribute to this project, whether documentation, features, bug fixes, code cleanup, testing, or code reviews, is very much encouraged to do so.

To join, just raise your hand on the [Pathway Discord server](https://discord.com/invite/pathway) (#get-help) or the GitHub [discussion](https://github.com/pathwaycom/llm-app/discussions) board.

If you are unfamiliar with how to contribute to GitHub projects, here is a [Get Started Guide](https://docs.github.com/en/get-started/quickstart/contributing-to-projects). A full set of contribution guidelines, along with templates, are in progress.


## Coming Soon

* Templates for retrieving context via graph walks.
* Easy setup for model drift monitoring.
* Templates for model A/B testing.
* Real-time OpenAI API observability.

## ☁️ Hosted Version ☁️

Please see <a href="https://cloud.pathway.com/">cloud.pathway.com</a> for hosted services. You can quickly set up variants of the `demo-document-indexing` app, which connect live data sources on Google Drive and Sharepoint to your Gen AI app.

## Need help?

Interested in building your own Pathway LLM App with your data source, stack, and custom use cases? Connect with us to get help with:

* Connecting your own live data sources to your LLM application (e.g. Google or Microsoft Drive documents, Kafka, databases, API's, ...).
* Explore how you can get your LLM application up and running in popular cloud platforms such as Azure and AWS.
* Developing knowledge graph use cases.
* End-to-end solution implementation.

Reach us at contact@pathway.com or via <a href="https://pathway.com/solutions/llm-app">Pathway's website</a>.


## Supported and maintained by

<p align="center">
  <a href="https://github.com/pathwaycom/"><img src="https://pathway.com/logo-light.svg" alt="Pathway"/></a>
</p>
<p align="center">
  <a href="https://pathway.com/solutions/llm-app">
    <img src="https://img.shields.io/badge/See%20Pathway's%20offering%20for%20AI%20applications-0000FF" alt="See Pathway's offering for AI applications"/>
  </a>
</p>
