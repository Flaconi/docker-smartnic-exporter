ifneq (,)
.error This Makefile requires GNU Make.
endif

.PHONY: build tag login push enter

DIR = .
FILE = Dockerfile
IMAGE = "flaconi/smartnic-exporter"
PYTHON_VERSIONS = 3.11-slim 3.12-slim


build-all:
	@for PY in $(PYTHON_VERSIONS); do \
		MAJOR=$$(echo $$PY | cut -d'.' -f1,2); \
		$(MAKE) build PYTHON_VERSION=$$PY VERSION_SUFFIX=$$MAJOR TAG=$(TAG); \
	done

build:
	docker build \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		-t $(IMAGE):$(TAG)-$(VERSION_SUFFIX) \
		-t $(IMAGE):latest-$(VERSION_SUFFIX) \
		$(if $(filter 3.12,$(VERSION_SUFFIX)),-t $(IMAGE):latest) \
		-f Dockerfile .

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

push-all:
	@for PY in $(PYTHON_VERSIONS); do \
		MAJOR=$$(echo $$PY | cut -d'.' -f1,2); \
		$(MAKE) push VERSION_SUFFIX=$$MAJOR TAG=$(TAG); \
	done

push:
	docker push $(IMAGE):$(TAG)-$(VERSION_SUFFIX)
	docker push $(IMAGE):latest-$(VERSION_SUFFIX)
	@if [ "$(VERSION_SUFFIX)" = "3.12" ]; then docker push $(IMAGE):latest; fi

enter:
	docker run --rm --name $(subst /,-,$(IMAGE)) -it --entrypoint=/bin/sh $(ARG) $(IMAGE)

help:
	@echo ""
	@echo "📦 docker-smartnic-exporter – Available commands:"
	@echo ""
	@echo "  make build-all TAG=<tag>     Build images for all Python versions"
	@echo "  make push-all TAG=<tag>      Push all images with correct tags"
	@echo "  make build TAG=<tag> PYTHON_VERSION=<ver> VERSION_SUFFIX=<suffix>   Build one variant"
	@echo "  make push TAG=<tag> VERSION_SUFFIX=<suffix>                         Push one variant"
	@echo "  make tag TAG=<tag>           Tag the base image (local use)"
	@echo "  make login DOCKER_USER=... DOCKER_PASS=...  Login to Docker (local use)"
	@echo "  make enter                   Open shell into latest image"
	@echo "  make help                    Show this help message"
	@echo ""

