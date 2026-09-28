EPSILON = None          # etiqueta de transición-ε en el AFN
CONCAT = "·"            # operador de concatenación explícita


# 1. Tokenizador
def _leer_clase(expresion, i):
    i += 1
    conjunto = set()
    while i < len(expresion) and expresion[i] != "]":
        c = expresion[i]
        if c == "\\":
            i += 1
            c = {"t": "\t", "n": "\n"}.get(expresion[i], expresion[i])
        if i + 2 < len(expresion) and expresion[i + 1] == "-" and expresion[i + 2] != "]":
            fin = expresion[i + 2]
            for codigo in range(ord(c), ord(fin) + 1):
                conjunto.add(chr(codigo))
            i += 3
        else:
            conjunto.add(c)
            i += 1
    if i >= len(expresion):
        raise ValueError("Clase de caracteres sin cerrar ']'")
    return frozenset(conjunto), i + 1


def tokenizar(expresion):
    tokens = []
    i = 0
    while i < len(expresion):
        c = expresion[i]
        if c == "\\":
            i += 1
            literal = {"t": "\t", "n": "\n"}.get(expresion[i], expresion[i])
            tokens.append(("SIM", frozenset({literal})))
            i += 1
        elif c == "[":
            conjunto, i = _leer_clase(expresion, i)
            tokens.append(("SIM", conjunto))
        elif c in "|*+?()":
            tokens.append(("OP", c))
            i += 1
        else:
            tokens.append(("SIM", frozenset({c})))
            i += 1
    return _insertar_concatenacion(tokens)


def _insertar_concatenacion(tokens):
    resultado = []
    for k, token in enumerate(tokens):
        resultado.append(token)
        if k + 1 == len(tokens):
            break
        siguiente = tokens[k + 1]
        izquierda_ok = token[0] == "SIM" or token[1] in ")*+?"
        derecha_ok = siguiente[0] == "SIM" or siguiente[1] == "("
        if izquierda_ok and derecha_ok:
            resultado.append(("OP", CONCAT))
    return resultado


# 2. Shunting Yard (infix -> postfix)
PRECEDENCIA = {"|": 1, CONCAT: 2, "*": 3, "+": 3, "?": 3}


def shunting_yard(tokens):
    salida, pila = [], []
    for token in tokens:
        tipo, valor = token
        if tipo == "SIM":
            salida.append(token)
        elif valor == "(":
            pila.append(token)
        elif valor == ")":
            while pila and pila[-1][1] != "(":
                salida.append(pila.pop())
            if not pila:
                raise ValueError("Paréntesis desbalanceados")
            pila.pop()
        else:
            while (pila and pila[-1][1] != "("
                   and PRECEDENCIA[pila[-1][1]] >= PRECEDENCIA[valor]):
                salida.append(pila.pop())
            pila.append(token)
    while pila:
        if pila[-1][1] == "(":
            raise ValueError("Paréntesis desbalanceados")
        salida.append(pila.pop())
    return salida


# 3. Thompson (postfix -> AFN)
class AFN:
    def __init__(self):
        self.num_estados = 0
        self.transiciones = {}      # estado -> lista de (etiqueta, destino)
        self.inicial = None
        self.final = None

    def nuevo_estado(self):
        estado = self.num_estados
        self.num_estados += 1
        self.transiciones[estado] = []
        return estado

    def agregar(self, origen, etiqueta, destino):
        self.transiciones[origen].append((etiqueta, destino))


def thompson(postfix):
    afn = AFN()
    pila = []
    for tipo, valor in postfix:
        if tipo == "SIM":
            i, f = afn.nuevo_estado(), afn.nuevo_estado()
            afn.agregar(i, valor, f)
            pila.append((i, f))
        elif valor == CONCAT:
            (i2, f2), (i1, f1) = pila.pop(), pila.pop()
            afn.agregar(f1, EPSILON, i2)
            pila.append((i1, f2))
        elif valor == "|":
            (i2, f2), (i1, f1) = pila.pop(), pila.pop()
            i, f = afn.nuevo_estado(), afn.nuevo_estado()
            afn.agregar(i, EPSILON, i1); afn.agregar(i, EPSILON, i2)
            afn.agregar(f1, EPSILON, f); afn.agregar(f2, EPSILON, f)
            pila.append((i, f))
        elif valor in "*+?":
            i1, f1 = pila.pop()
            i, f = afn.nuevo_estado(), afn.nuevo_estado()
            afn.agregar(i, EPSILON, i1)
            afn.agregar(f1, EPSILON, f)
            if valor in "*?":
                afn.agregar(i, EPSILON, f)        # cero veces
            if valor in "*+":
                afn.agregar(f1, EPSILON, i1)      # repetir
            pila.append((i, f))
    if len(pila) != 1:
        raise ValueError("Expresión regular mal formada")
    afn.inicial, afn.final = pila[0]
    return afn


# 4. Construcción de subconjuntos (AFN -> AFD)
def cerradura_epsilon(afn, estados):
    pila, cerradura = list(estados), set(estados)
    while pila:
        e = pila.pop()
        for etiqueta, destino in afn.transiciones[e]:
            if etiqueta is EPSILON and destino not in cerradura:
                cerradura.add(destino)
                pila.append(destino)
    return frozenset(cerradura)


def mover(afn, estados, caracter):
    return {d for e in estados for etq, d in afn.transiciones[e]
            if etq is not EPSILON and caracter in etq}


class AFD:
    def __init__(self, alfabeto):
        self.alfabeto = alfabeto
        self.transiciones = {}      # (estado, caracter) -> estado
        self.inicial = 0
        self.finales = set()
        self.num_estados = 0


def construccion_subconjuntos(afn):
    alfabeto = set()
    for lista in afn.transiciones.values():
        for etq, _ in lista:
            if etq is not EPSILON:
                alfabeto |= etq
    afd = AFD(alfabeto)
    inicio = cerradura_epsilon(afn, {afn.inicial})
    ids = {inicio: 0}
    pendientes = [inicio]
    while pendientes:
        actual = pendientes.pop()
        if afn.final in actual:
            afd.finales.add(ids[actual])
        for c in alfabeto:
            destino = cerradura_epsilon(afn, mover(afn, actual, c))
            if not destino:
                continue
            if destino not in ids:
                ids[destino] = len(ids)
                pendientes.append(destino)
            afd.transiciones[(ids[actual], c)] = ids[destino]
    afd.num_estados = len(ids)
    return afd


# 5. Simulación
def simular_afd(afd, cadena):
    estado = afd.inicial
    for pos, c in enumerate(cadena):
        if (estado, c) not in afd.transiciones:
            return False, pos
        estado = afd.transiciones[(estado, c)]
    if estado in afd.finales:
        return True, None
    return False, len(cadena)


def compilar(expresion):
    postfix = shunting_yard(tokenizar(expresion))
    afn = thompson(postfix)
    afd = construccion_subconjuntos(afn)
    return afn, afd
