import sys,os.path

if len(sys.argv) < 2:
    print("./"+sys.argv[0]+" <nom de dossier>")
    sys.exit()

if not os.path.isdir(sys.argv[1]):
    print("Ce dossier n'existe pas : "+sys.argv[1])
    sys.exit()

toprint = []
preambules = [["10001101", "\x1b[6;30;42m"], ["1011101", "\x1b[6;30;43m"], ["10100000", "\x1b[6;30;44m"], ["10101000", "\x1b[6;30;41m"]]

for tab in preambules:
    hexpr = hex(int(tab[0], 2)).upper()[2:]
    if not os.path.isdir(hexpr):
        os.mkdir(hexpr)

def get_keysort(elem):
    return elem[elem.find("Préambule "):]

def get_color(preambule):
    global preambules
    for tab in preambules:
        if tab[0] == preambule: return tab[1]
    return "\x1b[6;30;47m"

def search_preambule(binary):
    global preambules
    for pre in preambules:
        index = binary.find(pre[0])
        if index != -1: return pre[0]
    return None

def checkADSB(filename):
    global toprint
    if not os.path.isfile(filename): return
    try:
        f = open(filename, "rb")
        data = str(f.read())
        f.close()
    except IOError:
        return

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

    preambulestr = search_preambule(binarystr)
    if preambulestr == None:
        binarystr = binarystr[:120]
        if binarystr == "": hexastr = ""
        else: hexastr = hex(int(binarystr, 2)).upper()[2:]
        toprint.append(filename+" -> Préambule INTROUVABLE {"+hexastr+"}")
        os.remove(filename)
        return

    preambule = binarystr.find(preambulestr)
    preambulehex = hex(int(preambulestr, 2)).upper()[2:]

    binarystr = binarystr[preambule:]
    hexastr = hex(int(binarystr[:120], 2)).upper()[2:]

    if len(binarystr) >= 220:
        os.remove(filename)
        toprint.append("Fichier "+filename+" supprimé (Contenu >= 220)")
        return
    toprint.append(filename+" -> Préambule TROUVÉ ["+get_color(preambulestr)+preambulehex+"\x1b[0m]  {"+hexastr+"}")
    os.rename(filename, preambulehex+"/"+filename)

for filename in os.listdir(sys.argv[1]):
    if filename[-4:] != ".dat": continue
    checkADSB(filename)
toprint.sort(key=get_keysort)
for msg in toprint:
    print(msg)