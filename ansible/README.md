# Ansible Setup

## About
Ansible playbooks to manage the configuration of my computers

## Usage
```
$ ansible-playbook -i hosts <playbook> --ask-become-pass
```

### OSX
Requirements:
- install Homebrew
    ```
    ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
    ```
- install Ansible
    ```
    brew install ansible
    ```
### Ubuntu
Requirements:
- install Ansible
  ```
  apt install ansible
  ```
