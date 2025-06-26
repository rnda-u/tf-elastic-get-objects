SANDBOX_DIR := SANDBOX

run_terraform_init:
	terraform -chdir=$(SANDBOX_DIR) init

run_terraform_apply: 
	terraform -chdir=$(SANDBOX_DIR) apply --auto-approve
	terraform -chdir=$(SANDBOX_DIR) output -json > ./traitement/data.json

run_python_all_code:
	cd traitement/ && python export.py --show-raw-dates


run_python_code:
	cd traitement/ && python export.py
