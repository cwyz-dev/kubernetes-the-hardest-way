RUNNER_IMAGE="ansible-runner:latest"

podman build -f Containerfile -t "$RUNNER_IMAGE" -q

podman run --rm \
  -v ansible:/ansible -v resources:/resources \
  -v "$HOME/.ssh/id_ed25519:/root/.ssh/id_ed25519:ro" \
  "$RUNNER_IMAGE" \
  sh -c 'ansible-playbook -i inventories/hosts.yaml playbooks/deploy.yaml'
