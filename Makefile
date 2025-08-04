DOCKER="docker"
IMAGE_NAME="kiansheik/nhe-enga"
TAG_NAME="production"

REPOSITORY=""
FULL_IMAGE_NAME=${IMAGE_NAME}:${TAG_NAME}

lint:
	zsh -c 'cd tupi; python3.11 setup.py sdist bdist_wheel;'
	zsh -c 'cd pydicate; python3.11 setup.py sdist bdist_wheel;'
	cp tupi/dist/tupi-0.1.0* gramatica/docs/src/.vuepress/public/pylibs/
	cp pydicate/dist/pydicate-0.1* gramatica/docs/src/.vuepress/public/pylibs/
	cp pydicate/dist/pydicate-0.1* ../tupi-annotation-suite/public/
	cp tupi/dist/tupi-0.1.0* ../tupi-annotation-suite/public/
	zsh -c 'cd gramatica/docs; export NODE_OPTIONS=--openssl-legacy-provider; npm run build;'
	cp -r gramatica/docs/src/.vuepress/dist/* gramatica/
	echo 'kiansheik.io' > gramatica/CNAME
	rm -rf gramatica/docs/src/.vuepress/dist/*
	curl -L -o neologisms.csv "https://docs.google.com/spreadsheets/d/1NH_SgkBYY-vAITMtxrZogzihZGsbhIXCaes6HJrcJww/export?format=csv&sheet=AdminWords"

push:
	make lint
	git add .
	git commit
	git push origin HEAD

gen_data:
	python3.11 gen_data.py > docs/tupi_dict_navarro.js
	python3.11 verbs.py