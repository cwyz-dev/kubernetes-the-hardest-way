RUNNER_IMAGE="ansible-runner:latest"

podman build -f Containerfile -t "$RUNNER_IMAGE" -q

podman run --rm \
  -v ansible:/ansible -v resources:/resources \
  "$RUNNER_IMAGE" \
  sh -c 'ansibel-playbook -i inventories/hosts.yaml playbooks/deploy.yaml'
