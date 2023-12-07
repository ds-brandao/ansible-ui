# Documentation for Final SEC440 - Basic front end with ansible actions wrapped in a container

## by `Daniel Brandao` [github](https://github.com/ds-brandao/finalSEC440)

## Table of Contents

1. [Diagram](#diagram)
2. [Introduction](#introduction)
3. [Tools used](#tools-used)
4. [Streamlit](#streamlit)
5. [Docker](#docker)
6. [Ansible](#ansible)

## Diagram

![diagram](ansibleUI-finalSec440.drawio.png)

<br />
<br />

## Introduction

We are building a full-statck application for a more **user-friendly way to use ansible**, a tool in which users do not need to know how to use ansible, but still can benefit from its features. The application will be be running using a docker container with a streamlit front end.

## Tools used

1. [Streamlit](https://www.streamlit.io/)
2. [Docker](https://www.docker.com/)
3. [Python](https://www.python.org/)
4. [Ansible](https://www.ansible.com/)

## Streamlit

> Streamlit is an open-source Python library that makes it easy to build a simple and efficient front-end by using python. See more at [official documentation](https://www.streamlit.io/)

In the application, we are changing the variables the user will need to provide when running the ansible playbook. Therefore, for each playbook, there will be different fields to be filled. The user will be able to select the playbook, fill the fields, and run the playbook. The user will also be able to see the output of the playbook.

Here we see the variables for the playbook `setStaticRoute.yml`:

<p align="center">
<img src="image.png" alt="ui-setStaticRoute" width="500"/>
</p>

<br />

## Docker

> Docker uses containers to create virtual environments isolated from the host machine. See more at [official documentation](https://docs.docker.com/get-started/overview/)

For this project, we are using `docker-compose` to build the container and prepare the enviroment for the application to run properly. Also, as an architecture decision, we are **mounting** our container to **specific folders in the host machine**. This way, we can have a better way to manage the files ansibles uses, as well as maintaining the ssh keys in the host machine.

```yaml
version: '3'

services:
  app:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - /etc/ansible:/etc/ansible
      - ~/.ssh:/root/.ssh
    env_file:
      - .env
```

To expalin a little more about the `docker-compose` structure, we have the `app` service, which is the container we are building with the **current directory**. We are exposing the port `8501` to the host machine, so we can access the application. We are also mounting the folders `/etc/ansible` and `~/.ssh` to the host machine, so we can use the same files when the container is running. Finally, we are using the `.env` file to set the environment variables for the container.

## Ansible

> Ansible is an open-source software provisioning, configuration management, and application-deployment tool. See more at [official documentation](https://docs.ansible.com/ansible/latest/index.html)

Ansible is the tool we are utilizing to run the commands on the target machines (in this case, only a **CentOS** machine). However, this tool is very versitile and can be used in many different ways in many different devices, as long as they have ssh access.

For demonstration purposes, I have written a playbook that connects to my home server and configures the application (pulling the latest version from github) and running the container.

file: [setupFinal440.yaml]()

Let's break down the playbook:

Everything before `tasks` is the **playbook header**. Here we are defining the specific variables for the playbook, all based on the user input from the application. Ansible allows us to call playbooks and specify the value for specific variables, therefore we can use the same playbook for different devices and modify them as needed in the application.

The `task` section is where we define the actions we want to run on the target machine. In this case, we are preparing the enviroment for the application we are pulling from github and running the container. To breaek down the tasks:

1. Installing pre-requisites for the application to run.
    - git
    - streamlit
    - python3
    - python3-pip
    - ansible
    - docker

2. Cloning the repository from github. Since we are using a private repository, we need to provide the credentials to the playbook. We are using the `pat` variable to store the credentials, which is a **vault** variable. This way, we can store the credentials in an encrypted file and use them in the playbook.

3. **Preparing the enviroment** for the application to run. We are moving the files from the cloned repository to the correct folders in the host, so we can run the application. This is necessary because we are mounting the folders `/etc/ansible` and `~/.ssh` to the host machine, so we can use the same files when the container is running.
    
    > We could build the container with **everything necessary inside of it** and not mount the folders to the host machine, however, there some *security risks* involved with this approach. Since we would need to store valid **ssh keys, ansible-vault files** and other sensitive information inside the container that would be *accessible to anyone with access* to the container.

4. Verifying the files are in the **correct location**. This is just a verification step to make sure the files are in the correct location before running the container.

5. Running the container. We are using the `command` module to run the command `docker-compose up -d` in the correct folder. This command will run the container in the background, so we can access the application.
