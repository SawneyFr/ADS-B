#I took the def on an other github. But here I use them and you have to use 2 arguments to use that code (first = first frame, second = second frame).
#It calculate the longitude and latitude too. 
#WARNING : it uses the util.py library so you have to have that code on the same repertory.
import math,util,sys,os.path, datetime

def df(msg):
    """Get the downlink format (DF) number
    Args:
        msg (string): 28 bytes hexadecimal message string
    Returns:
        int: DF number
    """
    return util.df(msg)

def icao(msg):
    """Get the ICAO 24 bits address, bytes 3 to 8.
    Args:
        msg (string): 28 bytes hexadecimal message string
    Returns:
        String: ICAO address in 6 bytes hexadecimal string
    """
    return msg[2:8]

def data(msg):
    """Return the data frame in the message, bytes 9 to 22"""
    return msg[8:22]

def typecode(msg):
    """Type code of ADS-B message
    Args:
        msg (string): 28 bytes hexadecimal message string
    Returns:
        int: type code number
    """
    msgbin = util.hex2bin(msg)
    return util.bin2int(msgbin[32:37])

# ---------------------------------------------
# Aircraft Identification
# ---------------------------------------------
def category(msg):
    """Aircraft category number
    Args:
        msg (string): 28 bytes hexadecimal message string
    Returns:
        int: category number
    """

    if typecode(msg) < 1 or typecode(msg) > 4:
        raise RuntimeError("%s: Not a identification message" % msg)
    msgbin = util.hex2bin(msg)
    return util.bin2int(msgbin[5:8])

def callsign(msg):
    """Aircraft callsign
    Args:
        msg (string): 28 bytes hexadecimal message string
    Returns:
        string: callsign
    """

    if typecode(msg) < 1 or typecode(msg) > 4:
        raise RuntimeError("%s: Not a identification message" % msg)

    chars = '#ABCDEFGHIJKLMNOPQRSTUVWXYZ#####_###############0123456789######'
    msgbin = util.hex2bin(msg)
    csbin = msgbin[40:96]

    cs = ''
    cs += chars[util.bin2int(csbin[0:6])]
    cs += chars[util.bin2int(csbin[6:12])]
    cs += chars[util.bin2int(csbin[12:18])]
    cs += chars[util.bin2int(csbin[18:24])]
    cs += chars[util.bin2int(csbin[24:30])]
    cs += chars[util.bin2int(csbin[30:36])]
    cs += chars[util.bin2int(csbin[36:42])]
    cs += chars[util.bin2int(csbin[42:48])]

    # clean string, remove spaces and marks, if any.
    # cs = cs.replace('_', '')
    cs = cs.replace('#', '')
    return cs

# ---------------------------------------------
# Positions
# ---------------------------------------------

def oe_flag(msg):
    """Check the odd/even flag. Bit 54, 0 for even, 1 for odd.
    Args:
        msg (string): 28 bytes hexadecimal message string
    Returns:
        int: 0 or 1, for even or odd frame
    """
    if typecode(msg) < 5 or typecode(msg) > 18:
        raise RuntimeError("%s: Not a position message" % msg)

    msgbin = util.hex2bin(msg)
    return int(msgbin[53])

def cprlat(msg):
    """CPR encoded latitude
    Args:
        msg (string): 28 bytes hexadecimal message string
    Returns:
        int: encoded latitude
    """
    if typecode(msg) < 5 or typecode(msg) > 18:
        raise RuntimeError("%s: Not a position message" % msg)

    msgbin = util.hex2bin(msg)
    return util.bin2int(msgbin[54:71])

def cprlon(msg):
    """CPR encoded longitude
    Args:
        msg (string): 28 bytes hexadecimal message string
    Returns:
        int: encoded longitude
    """
    if typecode(msg) < 5 or typecode(msg) > 18:
        raise RuntimeError("%s: Not a position message" % msg)

    msgbin = util.hex2bin(msg)
    return util.bin2int(msgbin[71:88])

def position(msg0, msg1, t0, t1):
    if (5 <= typecode(msg0) <= 8 and 5 <= typecode(msg1) <= 8):
        return surface_position(msg0, msg1, t0, t1)

    elif (9 <= typecode(msg0) <= 18 and 9 <= typecode(msg1) <= 18):
        return airborne_position(msg0, msg1, t0, t1)

    else:
        raise RuntimeError("incorrect or inconsistant message types")


def airborne_position(msg0, msg1, t0, t1):
    """Decode airborn position from a pair of even and odd position message
        131072 is 2^17, since CPR lat and lon are 17 bits each.
    Args:
        msg0 (string): even message (28 bytes hexadecimal string)
        msg1 (string): odd message (28 bytes hexadecimal string)
        t0 (int): timestamps for the even message
        t1 (int): timestamps for the odd message
    Returns:
        (float, float): (latitude, longitude) of the aircraft
    """

    msgbin0 = util.hex2bin(msg0)
    msgbin1 = util.hex2bin(msg1)

    cprlat_even = util.bin2int(msgbin0[54:71]) / 131072.0
    cprlon_even = util.bin2int(msgbin0[71:88]) / 131072.0
    cprlat_odd = util.bin2int(msgbin1[54:71]) / 131072.0
    cprlon_odd = util.bin2int(msgbin1[71:88]) / 131072.0

    air_d_lat_even = 360.0 / 60
    air_d_lat_odd = 360.0 / 59

    # compute latitude index 'j'
    j = util.floor(59 * cprlat_even - 60 * cprlat_odd + 0.5)

    lat_even = float(air_d_lat_even * (j % 60 + cprlat_even))
    lat_odd = float(air_d_lat_odd * (j % 59 + cprlat_odd))

    if lat_even >= 270:
        lat_even = lat_even - 360

    if lat_odd >= 270:
        lat_odd = lat_odd - 360

    # check if both are in the same latidude zone, exit if not
    if _cprNL(lat_even) != _cprNL(lat_odd):
        return None

    # compute ni, longitude index m, and longitude
    if (t0 > t1):
        ni = _cprN(lat_even, 0)
        m = util.floor(cprlon_even * (_cprNL(lat_even)-1) -
                       cprlon_odd * _cprNL(lat_even) + 0.5)
        lon = (360.0 / ni) * (m % ni + cprlon_even)
        lat = lat_even
    else:
        ni = _cprN(lat_odd, 1)
        m = util.floor(cprlon_even * (_cprNL(lat_odd)-1) -
                       cprlon_odd * _cprNL(lat_odd) + 0.5)
        lon = (360.0 / ni) * (m % ni + cprlon_odd)
        lat = lat_odd

    if lon > 180:
        lon = lon - 360

    return round(lat, 5), round(lon, 5)


def surface_position(msg0, msg1, t0, t1):
    # TODO: implement surface positon decoding
    raise RuntimeError('suface position decoding to be implemented soon...')

#_cpr permettent de calculer la position de l'avion (longitude et latitude)
def _cprN(lat, is_odd):
    nl = _cprNL(lat) - is_odd
    return nl if nl > 1 else 1


def _cprNL(lat):
    try:
        nz = 15
        a = 1 - math.cos(math.pi / (2 * nz))
        b = math.cos(math.pi / 180.0 * abs(lat)) ** 2
        nl = 2 * math.pi / (math.acos(1 - a/b))
        NL = util.floor(nl)
        return NL
    except:
        # happens when latitude is +/-90 degree
        return 1


def altitude(msg):
    """Decode aircraft altitude
    Args:
        msg (string): 28 bytes hexadecimal message string
    Returns:
        int: altitude in feet
    """
    if typecode(msg) < 9 or typecode(msg) > 18:
        raise RuntimeError("%s: Not a position message" % msg)

    msgbin = util.hex2bin(msg)
    q = msgbin[47]
    if q:
        n = util.bin2int(msgbin[40:47]+msgbin[48:52])
        alt = n * 25 - 1000
        return alt
    else:
        return None

def nic(msg):
    """Calculate NIC, navigation integrity category
    Args:
        msg (string): 28 bytes hexadecimal message string
    Returns:
        int: NIC number (from 0 to 11), -1 if not applicable
    """
    if typecode(msg) < 9 or typecode(msg) > 18:
        raise RuntimeError("%s: Not a airborne position message" % msg)

    msgbin = util.hex2bin(msg)
    tc = typecode(msg)
    nic_sup_b = util.bin2int(msgbin[39])

    if tc in [0, 18, 22]:
        nic = 0
    elif tc == 17:
        nic = 1
    elif tc == 16:
        if nic_sup_b:
            nic = 3
        else:
            nic = 2
    elif tc == 15:
        nic = 4
    elif tc == 14:
        nic = 5
    elif tc == 13:
        nic = 6
    elif tc == 12:
        nic = 7
    elif tc == 11:
        if nic_sup_b:
            nic = 9
        else:
            nic = 8
    elif tc in [10, 21]:
        nic = 10
    elif tc in [9, 20]:
        nic = 11
    else:
        nic = -1
    return nic

# ---------------------------------------------
# Vitesse
# ---------------------------------------------

def velocity(msg):
    """Calculate the speed, heading, and vertical rate
    Args:
        msg (string): 28 bytes hexadecimal message string
    Returns:
        (int, float, int, string): speed (kt), heading (degree),
            rate of climb/descend (ft/min), and speed type
            ('GS' for ground speed, 'AS' for airspeed)
    """

    if typecode(msg) != 19:
        raise RuntimeError("%s: Not a airborne velocity message" % msg)

    msgbin = util.hex2bin(msg)

    subtype = util.bin2int(msgbin[37:40])

    if subtype in (1, 2):
        v_ew_sign = util.bin2int(msgbin[45])
        v_ew = util.bin2int(msgbin[46:56]) - 1       # east-west velocity

        v_ns_sign = util.bin2int(msgbin[56])
        v_ns = util.bin2int(msgbin[57:67]) - 1       # north-south velocity

        v_we = -1*v_ew if v_ew_sign else v_ew
        v_sn = -1*v_ns if v_ns_sign else v_ns

        spd = math.sqrt(v_sn*v_sn + v_we*v_we)  # unit in kts

        hdg = math.atan2(v_we, v_sn)
        hdg = math.degrees(hdg)                 # convert to degrees
        hdg = hdg if hdg >= 0 else hdg + 360    # no negative val

        tag = 'GS'

    else:
        hdg = util.bin2int(msgbin[46:56]) / 1024.0 * 360.0
        spd = util.bin2int(msgbin[57:67])

        tag = 'AS'

    vr_sign = util.bin2int(msgbin[68])
    vr = util.bin2int(msgbin[68:77])             # vertical rate
    rocd = -1*vr if vr_sign else vr         # rate of climb/descend

    return int(spd), round(hdg, 1), int(rocd), tag

def speed_heading(msg):
    """Get speed and heading only from the velocity message
    Args:
        msg (string): 28 bytes hexadecimal message string
    Returns:
        (int, float): speed (kt), heading (degree)
    """
    spd, hdg, rocd, tag = velocity(msg)
    return spd, hdg

# Début du code

if len(sys.argv) < 3:
    print("./"+sys.argv[0]+" <fichier avant> <fichier après>")
    sys.exit()

if not os.path.isfile(sys.argv[1]):
    print("Ce fichier n'existe pas : "+sys.argv[1])
    sys.exit()

try:
    f1 = open(sys.argv[1], "rb")
    data = str(f1.read())
    f1.close()

    f2 = open(sys.argv[2], "rb")
    data2 = str(f2.read())
    f2.close()

except IOError as err:
    print("Erreur : "+err.strerror)
    sys.exit()

#Fichier 1
data = data[2:][:-1]
tab = data.split("\\x")

count = 0
for i in tab[::-1]:
    if i == "00": count += 1
    else: break

tab = tab[:-count]

binarystr = ""
for octs in tab:
    if len(octs) == 4:
        binarystr += octs[1]
        binarystr += octs[3]
    elif len(octs) == 2:
        binarystr += octs[1]

#Fichier2
data2 = data2[2:][:-1]
tab2 = data2.split("\\x")

count2 = 0
for i in tab2[::-1]:
    if i == "00": count2 += 1
    else: break

tab2 = tab2[:-count2]

binarystr2 = ""
for octs in tab2:
    if len(octs) == 4:
        binarystr2 += octs[1]
        binarystr2 += octs[3]
    elif len(octs) == 2:
        binarystr2 += octs[1]
    
preambule = binarystr.find("10001101")      #préambule D8
if preambule == -1: 
    print("\x1b[1;49;31mPréambule '10001101' INTROUVABLE\x1b[0m")
    sys.exit()

print("\x1b[7;49;92m%s\x1b[0m"%(sys.argv[1]))
print("\x1b[1;49;96mPréambule détecté\x1b[0m")
binarystr = binarystr[preambule:]
print("Binaire à partir du préambule(\x1b[0;49;32m%s\x1b[0m): %s"%(len(binarystr),binarystr), end="\n")
binarystr = binarystr[:120]
hexastr = hex(int(binarystr, 2)).upper()[2:]
hexastr2 = hex(int(binarystr2, 2)).upper()[2:]
print("Hex: \x1b[0;49;34m%s\x1b[0m\n"%(hexastr))

print("Downlink format: %s" %(df(hexastr)))
print("Adresse ICAO: %s"%(icao(hexastr)))
print("Type Code : %s"%(typecode(hexastr)))

msg0=hexastr
msg1=hexastr2
t0=1
t1=2

#En fonction du typecode:

#       IDENTIFICATION
if typecode(hexastr) >= 1 and typecode(hexastr) <= 4:
    print("\x1b[1;49;36m\n--------Aircraft identification-----------\x1b[0m")
    print(category(hexastr))
    print(callsign(hexastr))

#       SURFACE
if typecode(hexastr) >= 5 and typecode(hexastr) <= 8:
    print("\x1b[1;49;35m\n--------Trame de surface---------\x1b[0m")  
    print("position de surface :")
    print(surface_position(msg0,msg1,t0,t1))

#       POSITION 1
if typecode(hexastr) >= 9 and typecode(hexastr) <= 18:
    print("\x1b[1;49;33m\n--------Aircraft position (9 to 18)-----------\x1b[0m")
    oe_flag(hexastr)
    cprlati=cprlat(hexastr)
    cprlong=cprlon(hexastr)
    print("Altitude: %s"%(altitude(hexastr)))
    print("catégorie d'intégrité de l'avion: %s"%(nic(hexastr)))
    print("latitude: %s longitude: %s"%(airborne_position(msg0,msg1,t0,t1)))

#       VITESSE
if typecode(hexastr) ==19:
    print("\n\x1b[1;49;36m\n----------Aircraft Velocity-----------\x1b[0m")
    print("vitesse: %s"%(velocity(hexastr)))
    print("speed heading: %s"%(speed_heading(hexastr)))


#       POSITION 2
if typecode(hexastr) >= 20 and typecode(hexastr) <= 22:
    print("\x1b[1;49;31m\n-----------Aircraft position (20 to 22)---------\x1b[0m")
    oe_flag(hexastr)
    cprlati=cprlat(hexastr)
    cprlong=cprlon(hexastr)
    print("Altitude: %s"%(altitude(hexastr)))
    print("catégorie d'intégrité de l'avion: %s"%(nic(hexastr)))
    print("latitude: %s longitude: %s"%(airborne_position(msg0,msg1,t0,t1)))

#       AUTRES
if typecode(hexastr) >= 23 and typecode(hexastr) <= 31:
    print("\x1b[1;49;90m\n----------oser----------\x1b[0m")
