"""
Script automatizado para ejecutar las pruebas unitarias, medir la cobertura
y validar la calidad del código con Flake8 y Pylint.
"""

import subprocess
import sys

def run_command(command: list[str], description: str) -> int:
    """Ejecuta un comando en la terminal y muestra su salida."""
    print(f"\n{'=' * 70}")
    print(f"🚀 EJECUTANDO: {description}")
    print(f"💻 Comando: {' '.join(command)}")
    print(f"{'=' * 70}")
    
    # Ejecutamos el comando
    result = subprocess.run(command, text=True, check=False)
    
    if result.returncode != 0:
        print(f"\n⚠️  Atención: {description} finalizó con advertencias o errores (Código {result.returncode}).")
    else:
        print(f"\n✅ {description} superado con éxito.")
        
    return result.returncode

def main():
    """Función principal que orquesta las validaciones."""
    print("Iniciando suite de validación del Sistema de Hoteles...\n")
    
    # 1. Ejecutar pruebas unitarias recolectando datos de cobertura
    run_command(
        ["coverage", "run", "-m", "unittest", "discover", "-s", "tests"],
        "Pruebas Unitarias (unittest)"
    )
    
    # 2. Generar el reporte de cobertura en la terminal
    run_command(
        ["coverage", "report", "-m"],
        "Reporte de Cobertura (coverage)"
    )
    
    # 3. Validar estilo PEP8 con Flake8 (Req 6 y 7)
    run_command(
        ["flake8", "hotel_system/", "tests/"],
        "Validación de Estilo PEP8 (Flake8)"
    )
    
    # 4. Validar calidad de código y arquitectura con Pylint (Req 7)
    run_command(
        ["pylint", "hotel_system/", "tests/"],
        "Análisis Estático de Código (Pylint)"
    )
    
    print("\n" + "=" * 70)
    print("🏁 EJECUCIÓN FINALIZADA")
    print("Revisa los reportes de arriba para confirmar el 85% y 0 advertencias.")
    print("=" * 70 + "\n")

if __name__ == '__main__':
    main()