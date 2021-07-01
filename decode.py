import sys,os.path, math

if len(sys.argv) < 2:
    print("./"+sys.argv[0]+" <nom de fichier>")
    sys.exit()

if not os.path.isfile(sys.argv[1]):
    print("Ce fichier n'existe pas : "+sys.argv[1])
    sys.exit()

try:
    f = open(sys.argv[1], "rb")
    data = str(f.read())
    f.close()
except IOError as err:
    print("Erreur : "+err.strerror)
    sys.exit()


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

preambule = binarystr.find("10001101")

if preambule == -1: print("\x1b[1;49;31mPréambule '10001101' INTROUVABLE\x1b[0m")
else:
    print("\x1b[1;49;96mPréambule détecté\x1b[0m")
    binarystr = binarystr[preambule:]
    print("Binaire à partir du préambule(\x1b[0;49;32m%s\x1b[0m): %s"%(len(binarystr),binarystr), end="\n")
    binarystr = binarystr[:120]
    hexastr = hex(int(binarystr, 2)).upper()[2:]
    print("Hex: \x1b[0;49;34m%s\x1b[0m\n"%(hexastr))
    
# ***affichage informations communes terminal***

dwk = binarystr[:5]
print("downlink format: %s | %s"%(dwk, int(dwk, 2)))
capability = binarystr[5:8]
print("capability: "+capability)
ICAO = binarystr[8:32]
ICAOlen = len(ICAO)
hexICAO = hex(int(ICAO, 2)).upper()[2:]
print("ICAO adress: %s(\x1b[0;49;32m%s\x1b[0m) | hex: %s"%(ICAO, ICAOlen, hexICAO))
TypeCode=binarystr[33:37]

if len(binarystr)<37:
    print("\x1b[1;49;31mERREUR : Le fichier ne comporte pas assez de bits\x1b[0m")
else:
    IntTypeCode = int(TypeCode, 2)
    print("Type Code (TC): %s | %s"%(TypeCode, IntTypeCode))

if IntTypeCode==0:
    print("\x1b[1;49;31mERREUR : type code null \x1b[0m")


# ***début analyse trame***

if IntTypeCode >= 1 and IntTypeCode <= 4:
    print("\x1b[1;49;36m\n-----Trame d'identification-----\x1b[0m")      # IDENTIFICATION TRAME
    C1 = binarystr[40:46]
    C2 = binarystr[46:52]
    C3 = binarystr[52:58]
    C4 = binarystr[58:64]
    C5 = binarystr[64:70]
    C6 = binarystr[70:76]
    C7 = binarystr[76:82]
    C8 = binarystr[82:88]
    tab = [C1, C2, C3, C4, C5, C6, C7, C8]
    
    resultstr = ""
    table = "#ABCDEFGHIJKLMNOPQRSTUVWXYZ#####_###############0123456789######"
    for CX in tab:
        binaryint = int(CX, 2)
        if (binaryint >= 1 and binaryint <= 26) or (binaryint >= 48 and binaryint <= 57) or binaryint == 32:
            resultstr += table[binaryint]
        else: resultstr += " "
    print("FlightID: '"+resultstr+"'")

# ----------------------------------TRAME DE SURFACE------------------------------------ #
if IntTypeCode >= 5 and IntTypeCode <= 8:
    print("\x1b[1;49;35m\n-----Trame de surface-----\x1b[0m")       

# ----------------------------TRAME DE POSITION 1------------------------------------------ #
if IntTypeCode >= 9 and IntTypeCode <= 18:                  
    print("\x1b[1;49;33m\n-----Trame de position aéroportée-----\x1b[0m")

    Altitude = int(binarystr[74:86], 2)
    print("Altitude (\x1b[0;49;32m%s\x1b[0m): %s | \x1b[1;49;36m%s\x1b[0m pieds"%(len(binarystr[74:86]), binarystr[74:86], Altitude))
    
    CPR = binarystr[85]
    print("CPR="+CPR)

    longitude = binarystr[86:103]
    latitude = binarystr[103:120]
    print("longitude(\x1b[0;49;32m%s\x1b[0m) : %s"%(len(longitude), longitude))
    print("latitude(\x1b[0;49;32m%s\x1b[0m) : %s"%(len(latitude), latitude))

    print("\n\x1b[0;49;92mPour connaître la longitude et la latitude, exécuter le programme 'calculatelatlong.py' situé dans le fichier 8D.")

# ---------------------------TRAME DE VITESSE------------------------------------------- #
if IntTypeCode == 19:
    print("\n\x1b[1;49;36m\n-----Trame de vitesse aéroportée-----\x1b[0m")         

# -----------------------------TRAME DE POSITION 2----------------------------------------- #
if IntTypeCode >= 20 and IntTypeCode <= 22:         
    print("\x1b[1;49;31m\n-----Trame de POSITION-----\x1b[0m")

# -------------------------------AUTRES--------------------------------------- #
if IntTypeCode >= 23 and IntTypeCode <= 31:
    print("\x1b[1;49;90m\n-----Trame de position aéroportée-----\x1b[0m")        #AUTRES