ifneq (,)
.error This Makefile requires GNU Make.
endif

.PHONY: build pull tag login push enter

DIR = .
FILE = Dockerfile
IMAGE = "flaconi/smartnic-exporter"
TAG = latest

build:
	docker build \
		--network=host \
		-t $(IMAGE) -f $(DIR)/$(FILE) $(DIR)

tag:
	docker tag $(IMAGE) $(IMAGE):$(TAG)

login:
ifndef DOCKER_USER
	$(error DOCKER_USER must either be set via environment or parsed as argument)
endif
ifndef DOCKER_PASS
	$(error DOCKER_PASS must either be set via environment or parsed as argument)
endif
	@yes | docker login --username $(DOCKER_USER) --password $(DOCKER_PASS)

push:
	docker push $(IMAGE):$(TAG)

enter:
	docker run --rm --name $(subst /,-,$(IMAGE)) -it --entrypoint=/bin/sh $(ARG) $(IMAGE)
