 ![Collect infrastructure](diagramme_architecture_logo.png)

# Tweets collection and indexation infrastructure

Collect massive amounts of tweets using the Twitter streaming APIs and index them with ElasticSearch. 

Deal with indexing delay using a RabbitMQ queue.

We combine Twitter [Sample](https://developer.twitter.com/en/docs/tweets/sample-realtime/overview/get_statuses_sample)
and [Filter](https://developer.twitter.com/en/docs/tweets/filter-realtime/api-reference/post-statuses-filter)
streaming APIs to maximize the number of tweets.

## Summary:
* [Getting started](#getting-started)
* [Check if streamer is running](#check-if-streamer-is-running)
* [Check if tweets are indexed](#check-if-tweets-are-indexed)
* [Turn off the stack](#turn-off-the-stack)
* [Deploy a large number of streamers](#turn-off-the-stack)
* [Paper](#paper)



## Getting started
* Clone this repo: 


        git clone https://github.com/ina-foss/stream-index-massive-tweets.git
        cd stream-index-massive-tweets

* Install [Docker](https://docs.docker.com/get-docker/)

* [Create a Twitter developper account and a Twitter App](https://developer.twitter.com/en/docs/basics/apps/overview).
Then get the app's [access tokens](https://developer.twitter.com/en/docs/basics/authentication/guides/access-tokens).
If you have several accounts, you can get several tokens. Copy them in `config.py` within the `ACCESS` list.

* Setup other parameters in `config.py` : `KEYWORDS` the keywords you want to track, `LANG` the language of the tweets.

* Increase the [system limits on mmap counts](https://www.elastic.co/guide/en/elasticsearch/reference/current/vm-max-map-count.html) if needed:
      
   
        sudo sysctl -w vm.max_map_count=262144
    
* Build the docker infrastructure


        docker-compose build
        docker swarm init
        docker network create --driver overlay net0 --attachable
        mkdir -p data/es_nodes/master data/es_nodes/slave1 data/es_nodes/slave2

* Deploy docker stack


        docker stack deploy stream-index --compose-file docker-compose.yml --with-registry-auth
  
The stack may take some minutes to be fully deployed. Check if services are deployed using
 
    docker service ls
    

## Check if streamer is running
    
To check if a streamer is running, you can simply curl it using its port number (5050 for sample streamer,
5051, 5052, etc. for the next streamers):

    curl localhost:5050

The response should look like:

    {"key": 0, "lang": null, "track": null} 

for sample streamer, and

    {"key": 2, "lang": "fr", "track": ["hier", "toujours", "beaucoup"]}
    
for the other streamers.

## Check if tweets are indexed

You can visualize the indexed tweets using Kibana. Type localhost:5656 in your browser.
If it is the first time you connect on Kibana, you are redirected to the 
*Configure an index pattern* page. Type `tweets-index*` as index name
and choose `created_at` as time-field name.

## Turn off the stack

    docker stack rm stream-index

## Deploy a large number of streamers
The current configuration provides 4 streaming servers from streamer_0 to streamer_3. 
It needs 4 different Twitter Developer access tokens in the `config.py` file. 

If you have more access tokens, you can add more streaming servers in the
`docker-compose.yml` file, then redeploy the stack.

## Paper
The reason why we use stop-words to collect tweets is explained in: 

Mazoyer, B., Cagé, J., Hudelot, C., & Viaud, M.-L. (2018). 
[“Real-time collection of reliable and representative tweets datasets related to news events”.](http://ceur-ws.org/Vol-2078/paper2.pdf)
 In “Proceedings of the First International Workshop on Analysis of Broad Dynamic Topics over Social Media (BroDyn 2018)”. 
 
 Please cite the paper if you use this infrastructure for research purpose.