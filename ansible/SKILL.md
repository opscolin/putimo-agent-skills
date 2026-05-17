---
name: ansible
description: Ansible automation and orchestration toolkit. Use for working with Ansible playbooks, inventory management, and ad-hoc command execution. Triggered when users ask to list or query Ansible inventory, run or validate playbooks, execute ad-hoc Ansible commands, test host connectivity with ping, create new Ansible playbooks, or check Ansible version for troubleshooting.
---

# Ansible

## Quick Start

Default inventory file: `inventory.ini`
Playbook directory: `playbooks/`

All Ansible commands use the Bash tool. Set environment variables for non-interactive output:
- `ANSIBLE_FORCE_COLOR=0` - Disable colored output
- `ANSIBLE_HOST_KEY_CHECKING=False` - Skip host key verification

Activate django_ops environment when needed:
```bash
source ~/.pyenv/versions/django_ops/bin/activate
```

## Core Capabilities

### 1. List Inventory

Show inventory structure in JSON format:

```bash
ansible-inventory -i inventory.ini --list
```

### 2. List Hosts

List all hosts from inventory:

```bash
ansible all -i inventory.ini --list-hosts
```

### 3. Validate Playbook

Check playbook syntax before execution:

```bash
ansible-playbook -i inventory.ini playbooks/myplaybook.yml --syntax-check
```

### 4. Ping Hosts

Test connectivity to all hosts:

```bash
ansible all -i inventory.ini -m ping
```

For specific groups:
```bash
ansible webservers -i inventory.ini -m ping
```

### 5. Run Ad-Hoc Commands

Execute modules directly on hosts:

```bash
# Run shell command
ansible <host_pattern> -i inventory.ini -m shell -a "<command>"

# Run specific module
ansible <host_pattern> -i inventory.ini -m <module> -a "<arguments>"
```

Common modules:
- `shell` - Execute shell commands
- `copy` - Copy files to hosts
- `yum/apt` - Package management
- `service` - Manage services
- `setup` - Gather facts

### 6. Get Ansible Version

```bash
ansible --version
```

### 7. Generate Playbook

Create new playbook files in `playbooks/` directory.

Basic playbook template:

```yaml
---
- name: Playbook Name
  hosts: all
  become: yes
  tasks:
    - name: Task description
      <module_name>:
        <parameter>: <value>
```

### 8. Run Playbook

Execute playbook with output:

```bash
# Basic execution
ansible-playbook -i inventory.ini playbooks/myplaybook.yml

# With extra variables
ansible-playbook -i inventory.ini playbooks/myplaybook.yml -e "var=value"

# Limit to specific hosts
ansible-playbook -i inventory.ini playbooks/myplaybook.yml --limit <host_pattern>

# Dry run (check mode)
ansible-playbook -i inventory.ini playbooks/myplaybook.yml --check

# Check which hosts this playbook applies to
ansible-playbook -i inventory.ini playbooks/myplaybook.yml --limit <host_pattern> --list-hosts
```

## Common Patterns

### Check syntax before running
Always validate playbooks before execution to catch errors early.

### Test connectivity first
Use `ansible all -m ping` to verify inventory and SSH access before running complex playbooks.

### Use host patterns
- `all` - All hosts
- `webservers` - Specific group
- `host1,host2` - Specific hosts
- `webservers:!staging` - All webservers except staging
- `webservers:&staging` - Webservers in staging group

### Idempotent operations
Ansible modules are idempotent by design. Running the same playbook multiple times should be safe.

### Verbose output
Add `-v`, `-vv`, or `-vvv` flags for debugging:
```bash
ansible-playbook playbook.yml -v
```
