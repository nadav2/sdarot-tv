image_name="sdarot-tv"
cloud_repo="gcr.io/sdarottv/sdarot-tv-server"

docker build -t $image_name .

id=$(docker images -q sdarot-tv)
echo Image id: "$id"

docker tag $image_name $cloud_repo
docker tag "$id" $cloud_repo
docker push $cloud_repo

image=$(docker inspect --format='{{index .RepoDigests 0}}' $image_name)

gcloud run deploy sdarot-tv-server \
--image="$image" \
--region=me-west1 \
--project=sdarottv \
 && gcloud run services update-traffic sdarot-tv-server --to-latest --project=sdarottv --region=me-west1
