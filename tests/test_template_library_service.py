import unittest

from services.template_library_service import TemplateLibraryService


class TemplateLibraryServiceTests(unittest.TestCase):
    def test_listados_no_vacios(self):
        self.assertTrue(TemplateLibraryService.listar_tipos_observacion())
        self.assertTrue(TemplateLibraryService.listar_tipos_recomendacion())

    def test_obtener_plantillas(self):
        self.assertIn("pie", TemplateLibraryService.obtener_observacion("plano").lower())
        self.assertIn("plantilla", TemplateLibraryService.obtener_recomendacion("descarga").lower())

    def test_obtener_tipo_inexistente(self):
        self.assertIsNone(TemplateLibraryService.obtener_observacion("no-existe"))
        self.assertIsNone(TemplateLibraryService.obtener_recomendacion("no-existe"))


if __name__ == "__main__":
    unittest.main()
