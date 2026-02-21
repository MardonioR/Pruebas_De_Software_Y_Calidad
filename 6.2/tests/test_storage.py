"""
Módulo de pruebas unitarias para las utilidades de persistencia (storage.py).
Verifica la lectura/escritura de archivos JSON y la tolerancia a fallos (Req 5).
"""

import unittest
import json
from pathlib import Path
from unittest.mock import patch

# Importamos las clases y funciones de tu capa de almacenamiento
from hotel_system.storage import JsonStore, index_by_id, safe_get


class TestJsonStore(unittest.TestCase):
    """Pruebas para la clase JsonStore, enfocadas en la tolerancia a fallos."""

    def setUp(self):
        """Prepara un archivo temporal para las pruebas."""
        self.test_file = Path("test_db.json")
        self.store = JsonStore(self.test_file)

        # Función "loader" simulada para las pruebas.
        # Imita a Hotel.from_dict, exigiendo que exista la llave 'name'
        def mock_loader(data: dict) -> str:
            if "name" not in data:
                raise KeyError("name")
            if not isinstance(data["name"], str):
                raise ValueError("name must be a string")
            return data["name"]

        self.loader = mock_loader

    def tearDown(self):
        """Limpia el archivo temporal."""
        self.test_file.unlink(missing_ok=True)

    # ---------------------------------------------------------
    # PRUEBAS DE LECTURA (load_list)
    # ---------------------------------------------------------

    def test_load_list_file_not_found(self):
        """Si el archivo no existe, debe retornar una lista vacía."""
        # Nos aseguramos de que no exista
        self.test_file.unlink(missing_ok=True)
        result = self.store.load_list(item_loader=self.loader, item_name="test")
        self.assertEqual(result, [])

    @patch('builtins.print')
    def test_load_list_invalid_json_format(self, mock_print):
        """Si el archivo no es un JSON válido, atrapa el error y retorna []."""
        self.test_file.write_text("ESTO NO ES UN JSON {ROTO}", encoding="utf-8")

        result = self.store.load_list(item_loader=self.loader, item_name="test")

        self.assertEqual(result, [])
        # Verificamos que se haya impreso el error en consola (Req 5)
        mock_print.assert_called_once()
        self.assertIn("ERROR: Invalid JSON", mock_print.call_args[0][0])

    @patch('builtins.print')
    def test_load_list_not_a_list(self, mock_print):
        """Si el JSON es válido pero es un diccionario en vez de lista, retorna []."""
        self.test_file.write_text('{"soy_diccionario": true}', encoding="utf-8")

        result = self.store.load_list(item_loader=self.loader, item_name="test")

        self.assertEqual(result, [])
        self.assertIn("ERROR: Expected a JSON list", mock_print.call_args[0][0])

    @patch('builtins.print')
    def test_load_list_mixed_valid_and_invalid_data(self, mock_print):
        """
        PRUEBA PARA EL REQ 5:
        Si hay elementos válidos e inválidos (faltan llaves, tipos incorrectos),
        descarta los malos, notifica en consola y carga los buenos.
        """
        mixed_data = [
            {"name": "Elemento Bueno 1"},
            "Soy un string, no un diccionario",       # Falla: no es dict
            {"id": 123},                              # Falla: KeyError (falta 'name')
            {"name": 456},                            # Falla: ValueError (no es string)
            {"name": "Elemento Bueno 2"}
        ]
        self.test_file.write_text(json.dumps(mixed_data), encoding="utf-8")

        result = self.store.load_list(item_loader=self.loader, item_name="item")

        # Debió cargar solo los 2 elementos buenos y saltarse los 3 malos
        self.assertEqual(len(result), 2)
        self.assertEqual(result, ["Elemento Bueno 1", "Elemento Bueno 2"])

        # Verificamos que la consola haya gritado 3 veces por los errores
        self.assertEqual(mock_print.call_count, 3)

    @patch.object(Path, 'read_text')
    @patch('builtins.print')
    def test_load_list_os_error(self, mock_print, mock_read):
        """Si ocurre un error a nivel sistema operativo al leer, atrapa la excepción."""
        mock_read.side_effect = OSError("Permiso denegado")

        # Creamos el archivo para que pase la validación de `.exists()`
        self.test_file.touch()

        result = self.store.load_list(item_loader=self.loader, item_name="test")
        self.assertEqual(result, [])
        mock_print.assert_called_once()

    # ---------------------------------------------------------
    # PRUEBAS DE ESCRITURA (save_list)
    # ---------------------------------------------------------

    def test_save_list_with_to_dict(self):
        """Prueba que los objetos con método to_dict se serialicen bien."""
        class MockItem:
            def to_dict(self):
                return {"name": "Test Item"}

        items = [MockItem()]
        self.store.save_list(items)

        data = json.loads(self.test_file.read_text(encoding="utf-8"))
        self.assertEqual(data, [{"name": "Test Item"}])

    def test_save_list_without_to_dict(self):
        """Prueba que los objetos simples (ej. diccionarios) se guarden directo."""
        items = [{"name": "Dict Item"}]
        self.store.save_list(items)

        data = json.loads(self.test_file.read_text(encoding="utf-8"))
        self.assertEqual(data, [{"name": "Dict Item"}])

    @patch.object(Path, 'write_text')
    @patch('builtins.print')
    def test_save_list_os_error(self, mock_print, mock_write):
        """Si falla la escritura por el SO, atrapa el error y no crashea."""
        mock_write.side_effect = OSError("Disco lleno")

        self.store.save_list([{"name": "test"}])

        mock_print.assert_called_once()
        self.assertIn("ERROR: Cannot write", mock_print.call_args[0][0])


class TestStorageHelpers(unittest.TestCase):
    """Pruebas para las funciones auxiliares de diccionarios."""

    def test_index_by_id(self):
        """Prueba que index_by_id convierta una lista a un diccionario indexado."""
        items = [
            {"id": "A1", "val": 10},
            {"id": "B2", "val": 20}
        ]
        result = index_by_id(items, get_id=lambda x: x["id"])

        expected = {
            "A1": {"id": "A1", "val": 10},
            "B2": {"id": "B2", "val": 20}
        }
        self.assertEqual(result, expected)

    def test_safe_get(self):
        """Prueba el comportamiento de la función safe_get."""
        dummy_dict = {"clave": "valor"}

        # Caso 1: La llave existe
        self.assertEqual(safe_get(dummy_dict, "clave"), "valor")

        # Caso 2: La llave NO existe (debe retornar None, no dar KeyError)
        self.assertIsNone(safe_get(dummy_dict, "no_existo"))


if __name__ == '__main__':
    unittest.main()
