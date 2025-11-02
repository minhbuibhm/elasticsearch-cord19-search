# elasticsearch-cord19-search
An AI-powered search engine for scientific literature, built with Elasticsearch. This project indexes the CORD-19 dataset to provide fast, semantic search and analytics, helping researchers navigate the overwhelming volume of COVID-19 papers.

# Feature
- Search by keyword (will add search by full-phrase in late update)
- Search n-gram
- Search by semantic (vector)

# How to run
0. Clone
```python
# clone repo and move to dir
git clone https://github.com/minhbuibhm/elasticsearch-cord19-search.git
cd elasticsearch-cord19-search
# move to branch dev_2
git checkout dev_2
```

1. Download and run elasticsearch and kinaba in local using docker (for develop - [see here](https://www.elastic.co/docs/deploy-manage/deploy/self-managed/local-development-installation-quickstart)) (will run in cloud in production)
    - Elasticsearch for store and index data
    - Kinana to interact with elasticsearch throw UI (can do store, index, search, analytics... using interface)

    ***Ensure elasticsearch is running***
2. Indexing data: 
we will use sample data (in datasets folder)
We will index data in 3 ways, so we can search papers in 3 ways, run:
```python
# set these option to index in three way
# Index for keyword search
    # use_embedding = False
    # use_n_gram_tokenizer = False
# Index for n-gram search
    # use_embedding = False
    # use_n_gram_tokenizer = True
# Index for semantic search
    # use_embedding = True
    # use_n_gram_tokenizer = False

python index_data.py
```
3. Run fronend
```python
cd frontend
npm run serve
```
4. Run backend
```python
cd backend
fastapi run main.py
```
detial will be update soon

# Reference
[github](https://github.com/ImadSaddik/ElasticSearch_Python_Course)
[youtube](https://www.youtube.com/watch?v=a4HBKEda_F8&t=17213s)