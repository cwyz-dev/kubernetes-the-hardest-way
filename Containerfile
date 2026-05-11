FROM python:3.11-alpine AS python_base
RUN apk upgrade --no-cache --update

FROM python_base AS python_libraries
RUN apk add --no-cache --update bash sshpass openssh rsync

FROM python_libraries AS pip
RUN pip install --upgrade pip

FROM pip AS ansible_install
RUN pip install --no-cache-dir ansible-core

FROM ansible_install AS ansible_posix
RUN ansible-galaxy collection install ansible.posix

FROM ansible_posix AS ansible_podman
RUN ansible-galaxy collection install containers.podman

FROM ansible_podman
WORKDIR /ansible
ENV ANSIBLE_CONFIG=./ansible.cfg
CMD [ "bash" ]
