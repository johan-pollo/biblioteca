from pydantic import BaseModel, ConfigDict, Field, model_validator


class TokenRespuesta(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshSolicitud(BaseModel):
    refresh_token: str


class CambioContrasena(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contrasena_actual: str
    contrasena_nueva: str = Field(min_length=8, max_length=64)
    confirmar_contrasena: str = Field(min_length=8, max_length=64)

    @model_validator(mode="after")
    def validar_contrasena_nueva(self) -> "CambioContrasena":
        if self.contrasena_nueva != self.confirmar_contrasena:
            raise ValueError("Las contraseñas no coinciden")
        if (
            not any(caracter.isupper() for caracter in self.contrasena_nueva)
            or not any(caracter.islower() for caracter in self.contrasena_nueva)
            or not any(caracter.isdigit() for caracter in self.contrasena_nueva)
        ):
            raise ValueError("La contraseña debe incluir mayúscula, minúscula y número")
        return self