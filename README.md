# Tweets collection and indexation infrastructure

Collect massive amounts of tweets in a given language using the Twitter streaming APIs, store them in text files and index them with elasticsearch.
The reason why we use stop-words to collect tweets is explained in: 
Mazoyer, B., Cagé, J., Hudelot, C., & Viaud, M.-L. (2018). 
[“Real-time collection of reliable andrepresentative tweets datasets related to newsevents”.](http://ceur-ws.org/Vol-2078/paper2.pdf)
 In “Proceedings of the First International Workshop on Analysis of Broad Dynamic Topics over Social Media (BroDyn 2018)”. 
 Please cite the paper if you use this infrastructure for research purpose.

## Summary:
* [HowTo](#howto)



## HowTo
* Install [Docker](https://docs.docker.com/get-docker/)
* Create Twitter API access tokens
You need to [create a Twitter developper account and a Twitter App](https://developer.twitter.com/en/docs/basics/apps/overview).
Then get the app's [access tokens](https://developer.twitter.com/en/docs/basics/authentication/guides/access-tokens).
If you have several accounts, you can get several tokens. Copy them in `config.py` within the `ACCESS` list.
* Setup other parameters in `config.py` : `KEYWORDS` the keywords you want to track, `LANG` the language of the tweets.
* Increase the [system limits on mmap counts](https://www.elastic.co/guide/en/elasticsearch/reference/current/vm-max-map-count.html) if needed:


    sudo sysctl -w vm.max_map_count=262144
    
* Build the docker infrastructure


    docker-compose build
    
* Initialize a swarm


    docker swarm init
    
* Create a network


    docker network create --driver overlay net0 --attachable

* Deploy docker stack


    docker stack deploy stream-index --compose-file docker-compose.yml --with-registry-auth
  
 The stack may take some minutes to be fully deployed. Check if services are deployed using
 
    docker service ls
    

## Check if streamer is running:
    
To check if a streamer is running, you can simply curl it using its port number (5050 for sample streamer,
5051, 5052 for the next streamers):

    curl localhost:5050

The response should look like:

    {"key": 0, "lang": null, "track": null} 

for sample streamer, and

    {"key": 2, "lang": "fr", "track": ["hier", "toujours", "beaucoup"]}
    
for the other streamers.

## Turn off the stack:

    docker stack rm stream-index

## Deploy a large number of streamers:
The current configuration provides 4 stream servers from streamer_0 to streamer_1. You can add more in the
`docker-compose.yml` file.
