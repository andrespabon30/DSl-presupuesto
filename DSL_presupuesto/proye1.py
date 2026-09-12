import re

# ==========================================================
# DSL-PRESUPUESTO DOMESTICO
# Lexer + Parser + Analisis Sintactico + Analisis Semantico
# ==========================================================


PALABRAS_RESERVADAS = {
    "CALCULAR": "CALCULAR",
    "PRESUPUESTO": "PRESUPUESTO",
}


TIPOS = {"INGRESO", "GASTO"}
CLASIFICACIONES = {"FIJO", "HORMIGA", "VARIABLE"}


PATRONES_TOKENS = [
    ("NUMERO", r"-?\d+(?:\.\d+)?"),
    ("ASIGNACION", r"="),
    ("OPERADOR", r"[+\-*/]"),
    ("CIERRE", r";"),
    ("IDENTIFICADOR", r"[A-Za-z_][A-Za-z0-9_]*"),
]


def lexer(linea):
    tokens = []
    posicion = 0

    while posicion < len(linea):
        if linea[posicion].isspace():
            posicion += 1
            continue

        encontrado = False
        texto_restante = linea[posicion:]

        for tipo, patron in PATRONES_TOKENS:
            coincidencia = re.match(patron, texto_restante)

            if coincidencia:
                valor_original = coincidencia.group()

                if tipo == "NUMERO":
                    siguiente_posicion = posicion + len(valor_original)
                    if siguiente_posicion < len(linea) and re.match(r"[A-Za-z_]", linea[siguiente_posicion]):
                        numero_invalido = re.match(r"-?\d+(?:\.\d+)?[A-Za-z_][A-Za-z0-9_]*", texto_restante).group()
                        return tokens, {
                            "valido": False,
                            "estado": "Error",
                            "mensaje": (
                                f"Error lexico: numero invalido '{numero_invalido}'. "
                                "Los valores numericos no pueden contener letras."
                            )
                        }

                valor = valor_original.upper()

                if tipo == "NUMERO":
                    tipo_token = "VALOR"
                elif tipo == "IDENTIFICADOR" and valor in TIPOS:
                    tipo_token = "TIPO"
                elif tipo == "IDENTIFICADOR" and valor in CLASIFICACIONES:
                    tipo_token = "CLASIFICACION"
                elif tipo == "IDENTIFICADOR":
                    tipo_token = PALABRAS_RESERVADAS.get(valor, tipo)
                else:
                    tipo_token = tipo

                tokens.append({
                    "tipo": tipo_token,
                    "valor": valor
                })

                posicion += len(valor_original)
                encontrado = True
                break

        if not encontrado:
            return tokens, {
                "valido": False,
                "estado": "Error",
                "mensaje": f"Error lexico: caracter no permitido '{linea[posicion]}'."
            }

    return tokens, {
        "valido": True,
        "estado": "Correcto",
        "mensaje": "Analisis lexico correcto."
    }


def crear_resultado_parser(valido, tipo_instruccion, mensaje):
    return {
        "valido": valido,
        "estado": "Correcto" if valido else "Error",
        "tipo_instruccion": tipo_instruccion if valido else None,
        "mensaje": mensaje
    }


def tipo(tokens, indice):
    return tokens[indice]["tipo"] if indice < len(tokens) else "FALTANTE"


def valor(tokens, indice):
    return tokens[indice]["valor"] if indice < len(tokens) else "FALTANTE"


def parser(tokens):
    if not tokens:
        return crear_resultado_parser(False, None, "Error sintactico: instruccion vacia.")

    primer_token = tipo(tokens, 0)
    primer_valor = valor(tokens, 0)

    if primer_token == "TIPO":
        if primer_valor not in TIPOS:
            return crear_resultado_parser(False, None, f"Tipo de instruccion no valido: {primer_valor}.")
        if tipo(tokens, 1) != "CLASIFICACION" or valor(tokens, 1) not in CLASIFICACIONES:
            return crear_resultado_parser(
                False,
                None,
                f"Falta una clasificacion valida despues de {primer_valor}: FIJO, HORMIGA o VARIABLE."
            )
        if tipo(tokens, 2) != "IDENTIFICADOR":
            return crear_resultado_parser(False, None, f"Falta el identificador despues de la clasificacion {tokens[1]['valor']}.")
        if tipo(tokens, 3) != "ASIGNACION":
            return crear_resultado_parser(False, None, 'Falta el simbolo de asignacion "=" despues del identificador.')
        if tipo(tokens, 4) != "VALOR":
            return crear_resultado_parser(False, None, 'Falta un valor numerico despues del simbolo "=".')
        if tipo(tokens, 5) != "CIERRE":
            return crear_resultado_parser(False, None, 'Falta el cierre ";" al final.')
        if len(tokens) > 6:
            return crear_resultado_parser(False, None, 'Hay tokens adicionales despues del cierre ";".')

        return crear_resultado_parser(True, primer_valor, f"Instruccion de {primer_valor.lower()} valida.")

    if primer_token == "CALCULAR":
        if tipo(tokens, 1) != "PRESUPUESTO":
            return crear_resultado_parser(False, None, "Falta la palabra PRESUPUESTO despues de CALCULAR.")
        if tipo(tokens, 2) != "CIERRE":
            return crear_resultado_parser(False, None, 'Falta el cierre ";" al final.')
        if len(tokens) > 3:
            return crear_resultado_parser(False, None, 'Hay tokens adicionales despues del cierre ";".')

        return crear_resultado_parser(True, "CALCULAR", "Instruccion de calculo valida.")

    return crear_resultado_parser(
        False,
        None,
        f"Error sintactico: la instruccion no puede iniciar con '{tokens[0]['valor']}'."
    )


def crear_tabla_simbolos():
    return {
        "INGRESO_MENSUAL": None,
        "INGRESO_NOMBRE": None,
        "INGRESO_CLASIFICACION": None,
        "GASTOS": {},
        "TOTALES": {
            "FIJO": 0,
            "HORMIGA": 0,
            "VARIABLE": 0
        },
        "GASTO_TOTAL": 0,
        "SALDO_FINAL": None
    }


def crear_resultado_semantico(ejecutado, valido, estado, mensaje):
    return {
        "ejecutado": ejecutado,
        "valido": valido,
        "estado": estado,
        "mensaje": mensaje
    }


def analisis_semantico(tokens, tipo_instruccion, tabla_simbolos):
    if tipo_instruccion == "INGRESO":
        clasificacion = tokens[1]["valor"]
        identificador = tokens[2]["valor"]
        valor = float(tokens[4]["valor"])

        if valor <= 0:
            return crear_resultado_semantico(True, False, "Error", "El ingreso mensual debe ser mayor a 0.")

        tabla_simbolos["INGRESO_MENSUAL"] = valor
        tabla_simbolos["INGRESO_NOMBRE"] = identificador
        tabla_simbolos["INGRESO_CLASIFICACION"] = clasificacion
        return crear_resultado_semantico(
            True,
            True,
            "Correcto",
            f"Ingreso registrado: {identificador} | {clasificacion} | {valor:,.0f} COP"
        )

    if tipo_instruccion == "GASTO":
        clasificacion = tokens[1]["valor"]
        identificador = tokens[2]["valor"]
        valor = float(tokens[4]["valor"])

        if valor <= 0:
            return crear_resultado_semantico(True, False, "Error", "El gasto debe ser mayor a 0.")

        if identificador in tabla_simbolos["GASTOS"]:
            return crear_resultado_semantico(True, False, "Error", f"El gasto '{identificador}' ya fue declarado.")

        tabla_simbolos["GASTOS"][identificador] = {
            "categoria": clasificacion,
            "valor": valor
        }
        tabla_simbolos["TOTALES"][clasificacion] += valor

        return crear_resultado_semantico(
            True,
            True,
            "Correcto",
            f"Gasto registrado: {identificador} | {clasificacion} | {valor:,.0f} COP"
        )

    if tipo_instruccion == "CALCULAR":
        if tabla_simbolos["INGRESO_MENSUAL"] is None:
            return crear_resultado_semantico(
                True,
                False,
                "Error",
                "No se puede calcular sin registrar INGRESO MENSUAL."
            )

        gasto_total = sum(tabla_simbolos["TOTALES"].values())
        saldo_final = tabla_simbolos["INGRESO_MENSUAL"] - gasto_total

        tabla_simbolos["GASTO_TOTAL"] = gasto_total
        tabla_simbolos["SALDO_FINAL"] = saldo_final

        if saldo_final < 0:
            return crear_resultado_semantico(
                True,
                True,
                "Correcto",
                f"Presupuesto calculado. Advertencia: saldo negativo de {saldo_final:,.0f} COP"
            )

        return crear_resultado_semantico(
            True,
            True,
            "Correcto",
            f"Presupuesto calculado. Saldo disponible: {saldo_final:,.0f} COP"
        )

    return crear_resultado_semantico(True, False, "Error", "Tipo de instruccion desconocido.")


def compilar(programa):
    tabla_simbolos = crear_tabla_simbolos()
    analisis = []
    lineas = programa.strip().split("\n")

    for numero_linea, linea in enumerate(lineas, start=1):
        codigo = linea.strip()

        if not codigo:
            continue

        tokens, resultado_lexico = lexer(codigo)
        resultado_parser = crear_resultado_parser(False, None, "")
        resultado_semantico = crear_resultado_semantico(False, None, "No ejecutado", "")
        estado_linea = "OK"

        if not resultado_lexico["valido"]:
            estado_linea = "ERROR"
            resultado_parser = crear_resultado_parser(False, None, "No se ejecuta el parser por error lexico.")
        else:
            resultado_parser = parser(tokens)

            if not resultado_parser["valido"]:
                estado_linea = "ERROR"
            else:
                resultado_semantico = analisis_semantico(
                    tokens,
                    resultado_parser["tipo_instruccion"],
                    tabla_simbolos
                )

                if not resultado_semantico["valido"]:
                    estado_linea = "ERROR"

        analisis.append({
            "numero": numero_linea,
            "linea": codigo,
            "estado": estado_linea,
            "tokens": tokens,
            "lexico": resultado_lexico,
            "parser": resultado_parser,
            "semantico": resultado_semantico
        })

    return analisis, tabla_simbolos


def mostrar_analisis(analisis, tabla_simbolos):
    for item in analisis:
        print("\n==================================================")
        print(f"Linea {item['numero']}: {item['linea']}")
        print("==================================================")
        print("Tokens:", item["tokens"])
        print("Lexico:", item["lexico"]["mensaje"])
        print("Parser:", item["parser"]["mensaje"])
        print("Semantico:", item["semantico"]["mensaje"] or item["semantico"]["estado"])
        print("Estado:", item["estado"])

    print("\nTabla de simbolos:")
    print(tabla_simbolos)


if __name__ == "__main__":
    programa = """
    INGRESO FIJO NOMINA = 2500000;
    GASTO FIJO LUZ = 2500;
    GASTO HORMIGA CAFE = 3000;
    GASTO VARIABLE MERCADO = 250000;
    CALCULAR PRESUPUESTO;
    """

    analisis, tabla = compilar(programa)
    mostrar_analisis(analisis, tabla)
