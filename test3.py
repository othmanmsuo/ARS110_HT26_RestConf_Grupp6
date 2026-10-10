import requests
import urllib3

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

# ==================================================
# INLOGGNING OCH ENHETER
# ==================================================

username = "admin"
password = "cisco"

enheter = {
    "Hemma": "100.100.100.1",
    "ISP": "100.100.100.2",
    "Internet": "100.100.100.3",
}

headers = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json"
}

# ==================================================
# RESTCONF HJÄLPFUNKTIONER
# ==================================================

def patch_data(enhet, path, data):
    ip = enheter[enhet]
    url = f"https://{ip}/restconf/data/{path}"

    try:
        svar = requests.patch(
            url,
            auth=(username, password),
            headers=headers,
            json=data,
            verify=False,
            timeout=10
        )

        if svar.status_code in [200, 201, 204]:
            print(f"[OK] {enhet}: konfiguration skickad")
            return True
        else:
            print(f"[FEL] {enhet}: HTTP {svar.status_code}")
            print(svar.text)
            return False

    except requests.exceptions.RequestException as error:
        print(f"[FEL] Kunde inte ansluta till {enhet}: {error}")
        return False

def put_data(enhet, path, data):
    ip = enheter[enhet]
    url = f"https://{ip}/restconf/data/{path}"

    try:
        svar = requests.put(
            url,
            auth=(username, password),
            headers=headers,
            json=data,
            verify=False,
            timeout=10
        )

        if svar.status_code in [200, 201, 204]:
            print(f"[OK] {enhet}: konfiguration skickad (PUT)")
            return True
        else:
            print(f"[FEL] {enhet}: HTTP {svar.status_code}")
            print(svar.text)
            return False

    except requests.exceptions.RequestException as error:
        print(f"[FEL] Kunde inte ansluta till {enhet}: {error}")
        return False

# ==================================================
# HOSTNAME
# ==================================================

def konfigurera_hostname(enhet, hostname):
    path = "Cisco-IOS-XE-native:native/hostname"
    data = {
        "Cisco-IOS-XE-native:hostname": hostname
    }

    print(f"Konfigurerar hostname {hostname}...")
    patch_data(enhet, path, data)

# ==================================================
# INTERFACE (GIGABIT & SERIAL FÖR 16.6)
# ==================================================

def konfigurera_interface(
    enhet,
    interface,
    ip_adress,
    mask
):
    interface_url = interface.replace('/', '%2F')
    path = f"ietf-interfaces:interfaces/interface={interface_url}"

    data = {
        "ietf-interfaces:interface": {
            "name": interface,
            "enabled": True,
            "ietf-ip:ipv4": {
                "address": [
                    {
                        "ip": ip_adress,
                        "netmask": mask
                    }
                ]
            }
        }
    }

    print(f"Konfigurerar {enhet} {interface}...")
    # Ändrad tillbaka till patch_data så vi slipper "type is not configured"-felet
    patch_data(enhet, path, data)

# ==================================================
# SERIAL INTERFACE (NATIVE FÖR HEMMA)
# ==================================================

def konfigurera_serial(
    enhet,
    interface_nummer,
    ip_adress,
    mask
):
    path = "Cisco-IOS-XE-native:native/interface"

    data = {
        "Cisco-IOS-XE-native:interface": {
            "Serial": [
                {
                    "name": interface_nummer,
                    "ip": {
                        "address": {
                            "primary": {
                                "address": ip_adress,
                                "mask": mask
                            }
                        }
                    }
                }
            ]
        }
    }

    print(f"Konfigurerar {enhet} Serial{interface_nummer}...")
    patch_data(enhet, path, data)

    # no shutdown
    ip = enheter[enhet]
    interface_url = interface_nummer.replace("/", "%2F")

    delete_url = (
        f"https://{ip}/restconf/data/"
        "Cisco-IOS-XE-native:native/interface/"
        f"Serial={interface_url}/shutdown"
    )

    try:
        svar = requests.delete(
            delete_url,
            auth=(username, password),
            headers=headers,
            verify=False,
            timeout=10
        )

        if svar.status_code in [200, 204, 404]:
            print(f"[OK] {enhet}: Serial{interface_nummer} aktiverat")
        else:
            print(f"[FEL] {enhet}: kunde inte aktivera Serial, HTTP {svar.status_code}")

    except requests.exceptions.RequestException as error:
        print(f"[FEL] {enhet}: {error}")

# ==================================================
# LOOPBACK INTERFACE
# ==================================================

def konfigurera_loopback(
    enhet,
    loopback_nummer,
    ip_adress,
    mask
):
    path = "Cisco-IOS-XE-native:native/interface"

    data = {
        "Cisco-IOS-XE-native:interface": {
            "Loopback": [
                {
                    "name": loopback_nummer,
                    "ip": {
                        "address": {
                            "primary": {
                                "address": ip_adress,
                                "mask": mask
                            }
                        }
                    }
                }
            ]
        }
    }

    print(f"Konfigurerar {enhet} Loopback{loopback_nummer}...")
    patch_data(enhet, path, data)

# ==================================================
# EIGRP
# ==================================================

# --------------------------------------------------
# HEMMA - nyare IOS XE / YANG-struktur
# --------------------------------------------------

def konfigurera_eigrp(
    enhet,
    as_nummer,
    networks,
    passive=None
):
    path = "Cisco-IOS-XE-native:native/router"

    network_lista = []

    for adress, wildcard in networks:
        network_lista.append({
            "ipv4-address": adress,
            "wildcard": wildcard
        })

    eigrp = {
        "autonomous-system": as_nummer,
        "network": {
            "address-wildcard": network_lista
        }
    }

    if passive is not None:
        eigrp["passive-interface"] = {
            "interface": passive
        }

    data = {
        "Cisco-IOS-XE-native:router": {
            "Cisco-IOS-XE-eigrp:router-eigrp": {
                "eigrp": {
                    "classic-mode": [
                        eigrp
                    ]
                }
            }
        }
    }

    print(f"Konfigurerar EIGRP AS {as_nummer} på {enhet}...")
    put_data(enhet, path, data)


# --------------------------------------------------
# ISP + INTERNET - IOS XE 16.6 / äldre YANG-struktur
# --------------------------------------------------

def konfigurera_eigrp_166(
    enhet,
    as_nummer,
    networks
):
    path = "Cisco-IOS-XE-native:native/router"

    network_lista = []

    for adress, wildcard in networks:
        network_lista.append({
            "number": adress,
            "wild-card": wildcard
        })

    data = {
        "Cisco-IOS-XE-native:router": {
            "Cisco-IOS-XE-eigrp:eigrp": [
                {
                    "id": as_nummer,
                    "network": network_lista
                }
            ]
        }
    }

    print(
        f"Konfigurerar EIGRP AS {as_nummer} "
        f"på {enhet} (IOS XE 16.6)..."
    )

    patch_data(enhet, path, data)




# ==================================================
# STATIC ROUTE
# ==================================================

def konfigurera_static_route(
    enhet,
    network,
    mask,
    next_hop
):
    ip = enheter[enhet]
    url = f"https://{ip}/restconf/data/Cisco-IOS-XE-native:native/ip"

    data = {
        "Cisco-IOS-XE-native:ip": {
            "route": {
                "ip-route-interface-forwarding-list": [
                    {
                        "prefix": network,
                        "mask": mask,
                        "fwd-list": [
                            {
                                "fwd": next_hop
                            }
                        ]
                    }
                ]
            }
        }
    }

    print(f"Konfigurerar route på {enhet}...")

    try:
        svar = requests.patch(
            url,
            auth=(username, password),
            headers=headers,
            json=data,
            verify=False,
            timeout=10
        )

        if svar.status_code in [200, 201, 204]:
            print(f"[OK] {enhet}: static route skapad")
        else:
            print(f"[FEL] {enhet}: HTTP {svar.status_code}")
            print(svar.text)

    except requests.exceptions.RequestException as error:
        print(f"[FEL] Static route på {enhet}: {error}")

# ==================================================
# START
# ==================================================

print()
print("======================================")
print("        SKILLA - RESTCONF")
print("======================================")

# HEMMA
print()
print("----- HEMMA -----")
konfigurera_hostname("Hemma", "Hemma")
konfigurera_interface("Hemma", "GigabitEthernet0/0/0", "10.10.10.1", "255.255.255.0")
konfigurera_serial("Hemma", "0/1/0", "172.16.16.1", "255.255.255.0")
konfigurera_eigrp(
    "Hemma",
    100,
    [
        ("10.10.10.0", "0.0.0.255"),
        ("172.16.16.0", "0.0.0.255")
    ],
    ["GigabitEthernet0/0/0"]
)

# ISP
print()
print("----- ISP -----")
konfigurera_hostname("ISP", "ISP")
konfigurera_interface("ISP", "GigabitEthernet0/0/0", "10.11.12.2", "255.255.255.0")
konfigurera_serial("ISP", "0/1/0", "172.16.16.2", "255.255.255.0")
konfigurera_eigrp_166(
    "ISP",
    100,
    [
        ("172.16.16.0", "0.0.0.255"),
        ("10.11.12.0", "0.0.0.255")
    ]
)

# INTERNET
print()
print("----- INTERNET -----")
konfigurera_hostname("Internet", "Internet")
konfigurera_interface("Internet", "GigabitEthernet0/0/0", "10.11.12.3", "255.255.255.0")
konfigurera_loopback("Internet", 0, "10.11.33.33", "255.255.255.0")
konfigurera_eigrp_166(
    "Internet",
    100,
    [
        ("10.11.12.0", "0.0.0.255"),
        ("10.11.33.33", "0.0.0.0")
    ]
)
konfigurera_static_route("Internet", "0.0.0.0", "0.0.0.0", "Loopback0")

print()
print("======================================")
print("SKILLA.PY ÄR KLAR")
print("======================================")
