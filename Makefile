.PHONY: cluster image gpus3 gpus4 deploy-naive loadgen rollout fix-nospare fix-spare lab clean
CLUSTER=llm-lab

cluster:
	kind create cluster --config kind/kind-config.yaml

image:
	docker build -t fake-llm:lab app/
	kind load docker-image fake-llm:lab --name $(CLUSTER)

gpus3:
	./scripts/advertise-gpus.sh 3

gpus4:
	./scripts/advertise-gpus.sh 4

deploy-naive:
	kubectl apply -f k8s/00-service.yaml -f k8s/10-llm-naive.yaml
	kubectl rollout status deploy/llm --timeout=5m

loadgen:
	kubectl apply -f k8s/50-loadgen.yaml
	kubectl logs -f deploy/loadgen

# any change to the pod template triggers a rollout:  make rollout V=v2
rollout:
	kubectl set env deploy/llm MODEL_VERSION=$(V)
	kubectl rollout status deploy/llm --timeout=10m

fix-nospare:
	kubectl apply -f k8s/20-llm-fixed-nospare.yaml -f k8s/40-pdb.yaml

fix-spare:
	kubectl apply -f k8s/30-placeholder.yaml -f k8s/21-llm-fixed-spare.yaml -f k8s/40-pdb.yaml

lab:
	python3 lab/sigterm_lab.py

clean:
	kind delete cluster --name $(CLUSTER)
