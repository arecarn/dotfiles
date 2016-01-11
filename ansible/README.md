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
### openSUSE
Requirements:
- install Ansible
  ```
  zypper install http://download.opensuse.org/repositories/systemsmanagement/openSUSE_13.1/noarch/ansible-1.9.4-42.1.noarch.rpm
  ```
