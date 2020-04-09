docker-compose build
docker swarm init
mkdir -p data/es_nodes/master
mkdir -p data/es_nodes/slave1
mkdir -p data/es_nodes/slave2
sudo sysctl -w vm.max_map_count=262144
docker network create --driver overlay net0 --attachable
docker stack deploy stream-index --compose-file docker-compose.yml --with-registry-auth
