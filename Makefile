DOCKER="docker"
IMAGE_NAME="kiansheik/nhe-enga"
TAG_NAME="production"

REPOSITORY=""
FULL_IMAGE_NAME=${IMAGE_NAME}:${TAG_NAME}

lint:
	zsh -c 'cd tupi; python3 setup.py sdist bdist_wheel;'

push:
	make lint
	git add .
	git commit
	git push origin HEAD

gen_data:
	python3 gen_data.py > docs/tupi_dict_navarro.js