image_name="sdarot-tv"
cloud_repo_name="sdarot-tv-server"
project_id="sdarottv"
cloud_repo="gcr.io/$project_id/$cloud_repo_name"

docker build -t $image_name .

id=$(docker images -q sdarot-tv)
echo Image id: "$id"

docker tag $image_name $cloud_repo
docker tag "$id" $cloud_repo
docker push $cloud_repo

image=$(docker inspect --format='{{index .RepoDigests 0}}' $image_name)

gcloud run deploy $cloud_repo_name \
--image="$image" \
--region=me-west1 \
--project=$project_id \
 && gcloud run services update-traffic $cloud_repo_name --to-latest --project=$project_id --region=me-west1
