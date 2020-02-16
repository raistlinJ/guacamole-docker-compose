docker save -o docker-images.tar $(docker-compose config | awk '{if ($1 == "image:") print $2;}')

