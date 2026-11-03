class ErrorAplicacion(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code

class NoEncontrado(ErrorAplicacion):
    def __init__(self, detail: str = "Recurso no encontrado"):
        super().__init__(detail, status_code=404)

class Conflicto(ErrorAplicacion):
    def __init__(self, detail: str = "Conflicto de datos"):
        super().__init__(detail, status_code=409)

class ReglaNegocio(ErrorAplicacion):
    def __init__(self, detail: str = "Violación de regla de negocio"):
        super().__init__(detail, status_code=422)


class NoAutenticado(ErrorAplicacion):
    def __init__(self, detail: str = "Credenciales inválidas"):
        super().__init__(detail, status_code=401)


class Prohibido(ErrorAplicacion):
    def __init__(self, detail: str = "No tiene permiso para esta operación"):
        super().__init__(detail, status_code=403)


class CuentaBloqueada(ErrorAplicacion):
    def __init__(self, detail: str = "Cuenta bloqueada temporalmente"):
        super().__init__(detail, status_code=423)