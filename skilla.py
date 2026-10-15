import requests
import urllib3

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)


# INLOGGNING + ENHETERNAS IP


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

# PUT/PATCH (återanvänds i varje funktion)

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

# HOSTNAME

def konfigurera_hostname(enhet, hostname):
    path = "Cisco-IOS-XE-native:native/hostname"
    data = {
        "Cisco-IOS-XE-native:hostname": hostname
    }

    print(f"Konfigurerar hostname: [{hostname}]...")
    patch_data(enhet, path, data)


# GIGABIT INTERFACE

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

    print(f"Konfigurerar {enhet} {interface} med IP {ip_adress}")
    patch_data(enhet, path, data)


# SERIAL INTERFACE

def konfigurera_serial(
    enhet,
    interface_nummer,
    ip_adress,
    mask
):
    interface_url = interface_nummer.replace("/", "%2F")

    path = (
        "Cisco-IOS-XE-native:native/interface/"
        f"Serial={interface_url}"
    )

    data = {
        "Cisco-IOS-XE-native:Serial": {
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
    }

    print(f"Konfigurerar {enhet} Serial{interface_nummer} med IP {ip_adress}")
    put_data(enhet, path, data)


# LOOPBACK INTERFACE

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

    print(f"Konfigurerar {enhet} Loopback{loopback_nummer} med IP {ip_adress}")
    patch_data(enhet, path, data)

# EIGRP

def konfigurera_eigrp(
    enhet,
    as_nummer,
    networks,
    passive=None,
    redistribute_static=False
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
    if redistribute_static is not False:
        eigrp["redistribute"] = {
             "static": {}
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


#EIGRP Äldre version IOS

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


# STATIC ROUTE

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


# START


print()
print("        SKILLA - RESTCONF")

# HEMMA
print()
print("- HEMMA -")
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
print("- ISP -")
konfigurera_hostname("ISP", "ISP")
konfigurera_interface("ISP", "GigabitEthernet0/0/0", "10.11.12.2", "255.255.255.0")
konfigurera_serial("ISP", "0/1/0", "172.16.16.2", "255.255.255.0")
konfigurera_eigrp(
    "ISP",
    100,
    [
        ("172.16.16.0", "0.0.0.255"),
        ("10.11.12.0", "0.0.0.255")
    ]
)

# INTERNET
print()
print("- INTERNET -")
konfigurera_hostname("Internet", "Internet")
konfigurera_interface("Internet", "GigabitEthernet0/0/0", "10.11.12.3", "255.255.255.0")
konfigurera_loopback("Internet", 0, "10.11.33.33", "255.255.255.0")
konfigurera_eigrp(
    "Internet",
    100,
    [
        ("10.11.12.0", "0.0.0.255"),
        ("10.11.33.33", "0.0.0.0")
    ],
    redistribute_static=True
)
konfigurera_static_route("Internet", "0.0.0.0", "0.0.0.0", "Loopback0")

print()
print("SKILLA.PY ÄR KLAR")
