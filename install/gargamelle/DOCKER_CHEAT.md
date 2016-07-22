
#A quick way to recover space (assuming site is running)
sudo docker rm `docker ps -a | grep Exited | awk '{print $1 }'`
sudo docker rmi `docker images -aq`

# list all containers
docker ps -a

# remove a container
docker rm $container_id





