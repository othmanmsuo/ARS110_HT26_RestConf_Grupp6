import requests
import urllib3

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

# INLOGGNING OCH ENHETER

username = "admin"
password = "cisco"

enheter = {
    "Hemma": "100.100.100.1",
    "ISP": "100.100.100.2",
    "Internet": "100.100.100.3",
}

headers = {
    "Accept": "application/yang-data+json"
}

antal_fel = 0


# GET


def get_data(enhet, path):

    ip = enheter[enhet]

    url = f"https://{ip}/restconf/data/{path}"

    try:

        svar = requests.get(
            url,
            auth=(username, password),
            headers=headers,
            verify=False,
            timeout=10
        )

        if svar.status_code == 200:
            return svar.json()

        print(
            f"[FEL] {enhet}: HTTP "
            f"{svar.status_code}"
        )

        return None

    except requests.exceptions.RequestException as error:

        print(
            f"[FEL] Kunde inte ansluta till "
            f"{enhet}: {error}"
        )

        return None


# HOSTNAME

def kontrollera_hostname(enhet, ratt_hostname):

    global antal_fel

    data = get_data(
        enhet,
        "Cisco-IOS-XE-native:native/hostname"
    )

    if data is None:
        antal_fel += 1
        return

    hostname = data.get(
        "Cisco-IOS-XE-native:hostname"
    )

    if hostname == ratt_hostname:

        print(
            f"[OK] {enhet} hostname {hostname}"
        )

    else:

        print(
            f"[FEL] {enhet} hostname är "
            f"""{hostname}, ska vara "{ratt_hostname}" """
        )

        antal_fel += 1
        

# INTERFACE


def kontrollera_interface(
    enhet,
    interface_namn,
    ratt_ip
):

    global antal_fel

    data = get_data(
        enhet,
        "ietf-interfaces:interfaces"
    )

    if data is None:
        antal_fel += 1
        return

    interfaces = data.get(
        "ietf-interfaces:interfaces",
        {}
    ).get(
        "interface",
        []
    )

    for interface in interfaces:

        if interface.get("name") == interface_namn:

            ipv4 = interface.get(
                "ietf-ip:ipv4",
                {}
            )

            adresser = ipv4.get(
                "address",
                []
            )

            for adress in adresser:

                if adress.get("ip") == ratt_ip:

                    print(
                        f"[OK] {enhet} "
                        f"{interface_namn} "
                        f"{ratt_ip}"
                    )

                    return

            print(
                f"[FEL] {enhet} "
                f"{interface_namn} "
                f"saknar IP {ratt_ip}"
            )

            antal_fel += 1
            return

    print(
        f"[FEL] {enhet} "
        f"{interface_namn} hittades inte"
    )

    antal_fel += 1


# EIGRP

def kontrollera_eigrp(
    enhet,
    ratt_as,
    ratt_neighbors
):

    global antal_fel

    data = get_data(
        enhet,
        "Cisco-IOS-XE-eigrp-oper:"
        "eigrp-oper-data"
    )

    if data is None:
        antal_fel += 1
        return

    instances = data.get(
        "Cisco-IOS-XE-eigrp-oper:"
        "eigrp-oper-data",
        {}
    ).get(
        "eigrp-instance",
        []
    )

    hittade_as = False
    neighbors = []

    for instance in instances:

        if instance.get("as-num") == ratt_as:

            hittade_as = True

            interfaces = instance.get(
                "eigrp-interface",
                []
            )

            for interface in interfaces:

                nbr_lista = interface.get(
                    "eigrp-nbr",
                    []
                )

                for neighbor in nbr_lista:

                    adress = neighbor.get(
                        "nbr-address"
                    )

                    if adress is not None:
                        neighbors.append(adress)

    if hittade_as:

        print(
            f"[OK] {enhet} "
            f"EIGRP AS {ratt_as}"
        )

    else:

        print(
            f"[FEL] {enhet} "
            f"saknar EIGRP AS {ratt_as}"
        )

        antal_fel += 1
        return


    for ratt_neighbor in ratt_neighbors:

        if ratt_neighbor in neighbors:

            print(
                f"[OK] {enhet} "
                f"EIGRP neighbor "
                f"{ratt_neighbor}"
            )

        else:

            print(
                f"[FEL] {enhet} "
                f"saknar EIGRP neighbor "
                f"{ratt_neighbor}"
            )

            antal_fel += 1



# ROUTINGTABELL


def kontrollera_route(
    enhet,
    prefix,
    next_hop=None
):

    global antal_fel

    data = get_data(
        enhet,
        "Cisco-IOS-XE-fib-oper:"
        "fib-oper-data"
    )

    if data is None:
        antal_fel += 1
        return

    fib_data = data.get(
        "Cisco-IOS-XE-fib-oper:"
        "fib-oper-data",
        {}
    )

    instances = fib_data.get(
        "fib-ni-entry",
        []
    )

    ipv4_default = None

    for instance in instances:

        if instance.get(
            "instance-name"
        ) == "IPv4:Default":

            ipv4_default = instance
            break

    if ipv4_default is None:

        print(
            f"[FEL] {enhet} "
            "IPv4:Default FIB saknas"
        )

        antal_fel += 1
        return


    routes = ipv4_default.get(
        "fib-entries",
        []
    )

    for route in routes:

        if route.get("ip-addr") == prefix:

            # Om vi inte behöver kontrollera next-hop
            if next_hop is None:

                print(
                    f"[OK] {enhet} "
                    f"route {prefix}"
                )

                return


            # Kontrollera next-hop
            nhs = route.get(
                "fib-nexthop-entries",
                []
            )

            for nh in nhs:

                adress = nh.get(
                    "nh-addr"
                )

                if adress == next_hop:

                    print(
                        f"[OK] {enhet} "
                        f"route {prefix}"
                    )

                    return


            print(
                f"[FEL] {enhet} "
                f"route {prefix} har "
                f"fel next-hop"
            )

            antal_fel += 1
            return


    print(
        f"[FEL] {enhet} "
        f"saknar route {prefix}"
    )

    antal_fel += 1


# STATIC ROUTE

def kontrollera_static_route(
    enhet,
    network,
    mask,
    ratt_fwd
):

    global antal_fel

    data = get_data(
        enhet,
        "Cisco-IOS-XE-native:"
        "native/ip/route"
    )

    if data is None:

        print(
            f"[FEL] {enhet} "
            "saknar static route"
        )

        antal_fel += 1
        return


    route_data = data.get(
        "Cisco-IOS-XE-native:route",
        {}
    )

    routes = route_data.get(
        "ip-route-interface-forwarding-list",
        []
    )


    for route in routes:

        if (
            route.get("prefix") == network
            and
            route.get("mask") == mask
        ):

            fwd_lista = route.get(
                "fwd-list",
                []
            )

            for fwd in fwd_lista:

                if fwd.get("fwd") == ratt_fwd:

                    print(
                        f"[OK] {enhet} "
                        f"static route "
                        f"{network}/0 -> "
                        f"{ratt_fwd}"
                    )

                    return


            print(
                f"[FEL] {enhet} "
                "static route har fel "
                "forwarding"
            )

            antal_fel += 1
            return


    print(
        f"[FEL] {enhet} "
        "saknar rätt static route"
    )

    antal_fel += 1



# START


print()
print(" ROBERT - RESTCONF RÄTTARE")


# HEMMA

print()
print("- HEMMA -")

kontrollera_hostname(
    "Hemma",
    "Hemma"
)

kontrollera_interface(
    "Hemma",
    "GigabitEthernet0/0/0",
    "10.10.10.1"
)

kontrollera_eigrp(
    "Hemma",
    100,
    [
        "172.16.16.2"
    ]
)

kontrollera_route(
    "Hemma",
    "0.0.0.0/0",
    "172.16.16.2/32"
)

kontrollera_route(
    "Hemma",
    "10.11.12.0/24",
    "172.16.16.2/32"
)


# ISP

print()
print("- ISP -")

kontrollera_hostname(
    "ISP",
    "ISP"
)

kontrollera_interface(
    "ISP",
    "GigabitEthernet0/0/0",
    "10.11.12.2"
)

kontrollera_eigrp(
    "ISP",
    100,
    [
        "172.16.16.1",
        "10.11.12.3"
    ]
)

kontrollera_route(
    "ISP",
    "10.10.10.0/24",
    "172.16.16.1/32"
)

kontrollera_route(
    "ISP",
    "0.0.0.0/0",
    "10.11.12.3/32"
)


# INTERNET

print()
print("- INTERNET -")

kontrollera_hostname(
    "Internet",
    "Internet"
)


kontrollera_interface(
    "Internet",
    "GigabitEthernet0/0/0",
    "10.11.12.3"
)

kontrollera_interface(
    "Internet",
    "Loopback0",
    "10.11.33.33"
)

kontrollera_eigrp(
    "Internet",
    100,
    [
        "10.11.12.2"
    ]
)

kontrollera_route(
    "Internet",
    "10.10.10.0/24",
    "10.11.12.2/32"
)

kontrollera_route(
    "Internet",
    "172.16.16.0/24",
    "10.11.12.2/32"
)



kontrollera_static_route(
    "Internet",
    "0.0.0.0",
    "0.0.0.0",
    "Loopback0"
)


# RESULTAT

print()

if antal_fel == 0:

    print("RESULTAT: GODKÄND")

else:

    print("RESULTAT: UNDERKÄND")
    print(f"Antal fel: {antal_fel}")

