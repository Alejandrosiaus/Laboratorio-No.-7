from proyecto1 import compilar, simular_afd

# ER que describe una producción válida (se compila con el motor del Proyecto 1)
ESP = "[ \t]*"
SIMBOLO = "[A-Za-z0-9]"
CUERPO = f"({SIMBOLO}([ \t]*{SIMBOLO})*|ε)"
FLECHA = "(->|→)"
ER_PRODUCCION = f"{ESP}[A-Z]{ESP}{FLECHA}{ESP}{CUERPO}{ESP}(\\|{ESP}{CUERPO}{ESP})*"

_AFN, _AFD = compilar(ER_PRODUCCION)


class ErrorGramatica(Exception):
    pass


class Gramatica:
    def __init__(self):
        self.inicial = None
        self.producciones = {}      # no-terminal -> lista de cuerpos (tuplas)

    def agregar(self, cabeza, cuerpo):
        self.producciones.setdefault(cabeza, [])
        if cuerpo not in self.producciones[cabeza]:
            self.producciones[cabeza].append(cuerpo)

    def __str__(self):
        orden = [self.inicial] + sorted(k for k in self.producciones if k != self.inicial)
        lineas = []
        for cabeza in orden:
            if cabeza in self.producciones:
                cuerpos = " | ".join(cuerpo_a_texto(c) for c in self.producciones[cabeza])
                lineas.append(f"    {cabeza} → {cuerpos}")
        return "\n".join(lineas)


def cuerpo_a_texto(cuerpo):
    return "".join(cuerpo) if cuerpo else "ε"


def es_no_terminal(simbolo):
    return simbolo.isupper()


def info_validador():
    return (f"ER de validación: {ER_PRODUCCION}\n"
            f"AFN (Thompson): {_AFN.num_estados} estados | "
            f"AFD (subconjuntos): {_AFD.num_estados} estados")


def validar_linea(linea):
    return simular_afd(_AFD, linea)


def cargar_gramatica(ruta):
    with open(ruta, encoding="utf-8-sig") as archivo:
        lineas = archivo.read().splitlines()

    gramatica = Gramatica()
    print(f"\nValidando '{ruta}' con el AFD del Proyecto 1:")
    for numero, linea in enumerate(lineas, start=1):
        linea = linea.rstrip()
        if not linea.strip() or linea.lstrip().startswith("#"):
            continue
        valida, pos = validar_linea(linea)
        if not valida:
            marcador = " " * pos + "^"
            raise ErrorGramatica(
                f"  Línea {numero}: RECHAZADA\n"
                f"      {linea}\n"
                f"      {marcador}  error en la columna {pos + 1}\n"
                f"  Ejecución detenida: la gramática no está bien escrita."
            )
        print(f"  Línea {numero}: ACEPTADA  ->  {linea.strip()}")

        cabeza, resto = linea.replace("→", "->").split("->", 1)
        cabeza = cabeza.strip()
        if gramatica.inicial is None:
            gramatica.inicial = cabeza
        for alternativa in resto.split("|"):
            texto = "".join(alternativa.split())
            cuerpo = () if texto == "ε" else tuple(texto)
            gramatica.agregar(cabeza, cuerpo)

    if gramatica.inicial is None:
        raise ErrorGramatica("  El archivo no contiene producciones.")
    return gramatica
