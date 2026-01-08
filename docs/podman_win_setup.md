# Setup Podman on Windows Workstations

Here you can find instructions on setting up Podman in a restrictive Windows system.

>
>⚠️ Podman is installed with [_user-mode networking_](https://docs.podman.io/en/latest/markdown/podman-machine-init.1.html#user-mode-networking) instead of the standard WSL networking setup.
> - This is because VPNs may block traffic from alternate network interfaces, such as those used by WSL VMs
> - With _user-mode networking_, all traffic from the Podman guest VM is relayed through a user-space process on the host, so VPNs see all Podman traffic as originating from the host itself, avoiding connectivity issues
>
> **TLDR;**<br>
> 💡 After the setup as described below, you can pull docker images without having to always connect to a non-office / non-VPN network and without the need to change DNS server entries in WSL VMs every time.
>

## ⚙️ Installation
### Step 1: Install Windows Subsystem for Linux (WSL) 🐧

- [🔗 Enable WSL](https://learn.microsoft.com/en-us/windows/wsl/install-manual#step-1---enable-the-windows-subsystem-for-linux) (requires admin)
    ```powershell
    dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
    ```
- [🔗 Enable Virtual Machine Feature](https://learn.microsoft.com/en-us/windows/wsl/install-manual#step-3---enable-virtual-machine-feature) (requires admin)


    ```powershell
    dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
    ```
- Restart your machine now to activate the enabled windows features.

- Now setup WSL:

    ```powershell
    wsl.exe --update
    wsl.exe --set-default-version 2
    ```

### Step 3: Install Podman 🐳

- [Install Podman using installer](https://github.com/containers/podman/blob/main/docs/tutorials/podman-for-windows.md#installing-podman) (requires admin) and restart your machine if required

- Now setup podman machine with _user-mode networking_ option:

    ```bash
    podman machine init --user-mode-networking
    podman machine start
    ```

<details>
<summary>If everything went well, <code>podman machine start</code> output should look like this (click to expand)</summary>

```text
$ podman machine start
Starting machine "podman-machine-default"
Starting user-mode networking...

This machine is currently configured in rootless mode. If your containers
require root permissions (e.g. ports < 1024), or if you run into compatibility
issues with non-podman clients, you can switch using the following command:

  podman machine set --rootful

API forwarding listening on: npipe:////./pipe/docker_engine

Docker API clients default to this address. You do not need to set DOCKER_HOST.
Machine "podman-machine-default" started successfully
```
</details>

### Step 4: Install user certificates inside Podman machine

- Run the powershell script [export-certs.ps1](./export-certs.ps1) to export all certificates to `ca-bundle.crt` in your home folder. 

- Login to the podman VM and copy this certificate bundle into the Podman machine:

    ```bash
    wsl -d podman-machine-default
    sudo cp /mnt/c/Users/******/ca-bundle.crt /etc/pki/ca-trust/source/anchors/windows-root.crt
    sudo update-ca-trust extract
    ```
- Update the trusted certificate authorities:

    ```bash
    sudo update-ca-trust extract
    ```

## 🧪 Test

- Launch httpd by pulling the image and running it:
    ```bash
    podman run --rm -d -p 8080:80 --name httpd docker.io/library/httpd
    ```
- Service should be up now and give a _200_ response:
    ```bash
    curl -i http://localhost:8080/
    ```
- Cleanup
    ```bash
    podman stop httpd
    ```

## 📚 References

- https://learn.microsoft.com/en-us/windows/wsl/install-manual
- https://github.com/containers/podman/blob/main/docs/tutorials/podman-for-windows.md
- https://docs.podman.io/en/latest/markdown/podman-machine-init.1.html
