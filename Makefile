.PHONY: proof fetch doctor build-sandbox build-cli containment kani-feasibility
proof:
	cd proof && lake build
fetch:
	python3 scripts/fetch_sources.py
doctor:
	python3 scripts/doctor.py
build-sandbox:
	bash scripts/build-sandbox.sh
build-cli:
	bash scripts/build-sandbox.sh cli
containment:
	python3 scripts/run-containment-vm.py
kani-feasibility:
	bash scripts/kani-feasibility.sh
