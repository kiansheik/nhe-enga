DOCKER="docker"
IMAGE_NAME="kiansheik/nhe-enga"
TAG_NAME="production"

REPOSITORY=""
FULL_IMAGE_NAME=${IMAGE_NAME}:${TAG_NAME}

lint:
	echo no lint yet

push:
	make lint
	git add .
	git commit
	git push origin HEAD