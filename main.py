import argparse
import sys

from gramatica import ErrorGramatica, cargar_gramatica, info_validador
from eliminar_epsilon import eliminar_producciones_epsilon

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")   # para ε y → en PowerShell


def main():
    parser = argparse.ArgumentParser(description="Eliminación de producciones-ε")
    parser.add_argument("archivos", nargs="*",
                        default=["gramaticas/gramatica1.txt", "gramaticas/gramatica2.txt",
                                 "gramaticas/gramatica3.txt"])
    parser.add_argument("--conservar-epsilon", action="store_true")
    args = parser.parse_args()

    print("=" * 64)
    print(info_validador())
    print("=" * 64)

    codigo = 0
    for ruta in args.archivos:
        print(f"\n{'#' * 64}\n# ARCHIVO: {ruta}\n{'#' * 64}")
        try:
            gramatica = cargar_gramatica(ruta)
        except ErrorGramatica as error:
            print(error)
            codigo = 1
            continue
        except FileNotFoundError:
            print(f"  No se encontró el archivo '{ruta}'.")
            codigo = 1
            continue
        eliminar_producciones_epsilon(gramatica, args.conservar_epsilon)
    sys.exit(codigo)


if __name__ == "__main__":
    main()
