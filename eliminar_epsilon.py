from itertools import product

from gramatica import Gramatica, cuerpo_a_texto, es_no_terminal

LINEA = "-" * 64


def encontrar_anulables(gramatica):
    print(f"\n{LINEA}\nPASO 1: Encontrar símbolos y producciones anulables\n{LINEA}")
    anulables = set()
    iteracion = 0
    while True:
        iteracion += 1
        nuevos = {}
        for cabeza, cuerpos in gramatica.producciones.items():
            if cabeza in anulables:
                continue
            for cuerpo in cuerpos:
                if all(s in anulables for s in cuerpo):     # () cuenta como ε
                    nuevos[cabeza] = cuerpo
                    break
        if not nuevos:
            print(f"  Iteración {iteracion}: no hay nuevos anulables -> fin.")
            break
        print(f"  Iteración {iteracion}:")
        for cabeza, cuerpo in nuevos.items():
            if cuerpo:
                razon = f"todos los símbolos de '{cuerpo_a_texto(cuerpo)}' son anulables"
            else:
                razon = "tiene la producción-ε directa"
            print(f"      {cabeza} → {cuerpo_a_texto(cuerpo)}   ({razon})")
        anulables |= set(nuevos)
        print(f"      Anulables = {{{', '.join(sorted(anulables))}}}")

    producciones_anulables = [
        (c, cuerpo) for c, cuerpos in gramatica.producciones.items()
        for cuerpo in cuerpos if all(s in anulables for s in cuerpo)
    ]
    print("\n  Producciones anulables:")
    for cabeza, cuerpo in producciones_anulables:
        print(f"      {cabeza} → {cuerpo_a_texto(cuerpo)}")
    print(f"\n  Conjunto de símbolos anulables: {{{', '.join(sorted(anulables)) or '∅'}}}")
    return anulables


def expandir_produccion(cabeza, cuerpo, anulables):
    posiciones = [i for i, s in enumerate(cuerpo) if s in anulables]
    m = len(posiciones)
    texto = cuerpo_a_texto(cuerpo)

    if not cuerpo:
        print(f"\n  {cabeza} → ε : producción-ε, se elimina.")
        return []
    if m == 0:
        print(f"\n  {cabeza} → {texto} : m = 0, sin anulables, se conserva igual.")
        return [cuerpo]

    anulables_txt = ", ".join(f"{cuerpo[p]}(pos {p + 1})" for p in posiciones)
    print(f"\n  {cabeza} → {texto} : m = {m} [{anulables_txt}] -> 2^{m} = {2 ** m} casos")
    resultado = []
    for caso, decision in enumerate(product((1, 0), repeat=m), start=1):
        omitidas = {p for p, d in zip(posiciones, decision) if d == 0}
        nuevo = tuple(s for i, s in enumerate(cuerpo) if i not in omitidas)
        bits = "".join(map(str, decision))
        omit_txt = ", ".join(f"{cuerpo[p]}{p + 1}" for p in sorted(omitidas)) or "ninguno"
        if not nuevo:
            estado = "ε -> descartada"
        elif nuevo == (cabeza,):
            estado = f"{cabeza} → {cabeza} trivial -> descartada"
        elif nuevo in resultado:
            estado = "repetida -> descartada"
        else:
            estado = "nueva"
            resultado.append(nuevo)
        print(f"      caso {caso:>2} [{bits}] omite: {omit_txt:<12} -> "
              f"{cabeza} → {cuerpo_a_texto(nuevo):<10} {estado}")
    return resultado


def eliminar_producciones_epsilon(gramatica, conservar_epsilon=False):
    print(f"\n{LINEA}\nGRAMÁTICA ORIGINAL (símbolo inicial: {gramatica.inicial})\n{LINEA}")
    print(gramatica)

    anulables = encontrar_anulables(gramatica)

    print(f"\n{LINEA}\nPASO 2: Generar nuevas producciones (2^m casos)\n{LINEA}")
    print("  Convención: bit 1 = se conserva el anulable, bit 0 = se omite")
    nueva = Gramatica()
    nueva.inicial = gramatica.inicial
    for cabeza, cuerpos in gramatica.producciones.items():
        for cuerpo in cuerpos:
            for nuevo in expandir_produccion(cabeza, cuerpo, anulables):
                nueva.agregar(cabeza, nuevo)

    print(f"\n{LINEA}\nPASO 3: Símbolo inicial\n{LINEA}")
    inicial = gramatica.inicial
    if inicial not in anulables:
        print(f"  {inicial} no es anulable: ε ∉ L(G), el lenguaje no cambia.")
    elif conservar_epsilon:
        usados = set(gramatica.producciones) | {
            s for cs in gramatica.producciones.values() for c in cs for s in c}
        libre = next(ch for ch in "ZYXWVUTRQPONMLKJIHGFEDCBA" if ch not in usados)
        print(f"  {inicial} es anulable: ε ∈ L(G). Se agrega nuevo inicial "
              f"{libre} → {inicial} | ε para conservar ε.")
        final = Gramatica()
        final.inicial = libre
        final.agregar(libre, (inicial,))
        final.agregar(libre, ())
        for cabeza, cuerpos in nueva.producciones.items():
            for c in cuerpos:
                final.agregar(cabeza, c)
        nueva = final
    else:
        print(f"  {inicial} es anulable: ε ∈ L(G). La gramática resultante genera "
              f"L(G) − {{ε}}.\n  (Use --conservar-epsilon para agregar un nuevo "
              f"símbolo inicial S' → S | ε)")

    sin_producciones = sorted(
        {s for cs in nueva.producciones.values() for c in cs for s in c
         if es_no_terminal(s) and s not in nueva.producciones})
    if sin_producciones:
        print(f"  Aviso: {', '.join(sin_producciones)} ya no tiene(n) producciones "
              f"(símbolo(s) inútil(es), se eliminan en la siguiente simplificación).")

    print(f"\n{LINEA}\nGRAMÁTICA SIN PRODUCCIONES-ε\n{LINEA}")
    print(nueva)
    return nueva
