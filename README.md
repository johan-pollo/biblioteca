# API REST de Biblioteca

API para administrar el catálogo de una biblioteca, sus socios y usuarios, los préstamos, las multas y los reportes. La aplicación está construida con FastAPI, SQLAlchemy 2, PostgreSQL, Alembic y JWT, y organiza el código con separación MVC.

Todos los endpoints se sirven bajo `/api/v1`. La documentación interactiva está disponible en `/docs` y `/redoc` salvo en producción.

## Funcionalidades

- Catálogo de autores, categorías y libros.
- Gestión de socios, préstamos, devoluciones y pago de multas.
- Registro público de socios y autenticación con access y refresh tokens JWT.
- Roles `admin`, `bibliotecario` y `socio`, con autorización por endpoint.
- Bloqueo temporal ante intentos de inicio de sesión fallidos y límites de solicitudes en autenticación.
- Migraciones de esquema con Alembic.
- Paginación uniforme en listados: `{ "items": [], "total": 0, "skip": 0, "limit": 10 }`.
- Pruebas automatizadas con pytest y TestClient.

## Tecnologías

| Tecnología | Versión requerida / uso |
|---|---|
| Python | 3.10 o superior; la imagen Docker usa Python 3.12 |
| FastAPI | `fastapi[standard]>=0.115` |
| SQLAlchemy | `>=2.0` |
| PostgreSQL | 16 en Docker; driver `psycopg[binary]>=3.2` |
| Alembic | `>=1.13` |
| Pydantic Settings | `>=2.4` |
| PyJWT | `>=2.9` |
| pwdlib con Argon2 | `pwdlib[argon2]>=0.2` |
| SlowAPI | `>=0.1.9` |
| pytest, pytest-cov, httpx | Dependencias de desarrollo de `requirements-dev.txt` |
| Cloudinary | SDK oficial de Python para subida y almacenamiento de imágenes de portada |

Las versiones instaladas concretas dependen del entorno y de la resolución de `pip`. Las restricciones de instalación están en [requirements.txt](./requirements.txt) y [requirements-dev.txt](./requirements-dev.txt).

## Arquitectura MVC

Cada capa tiene una responsabilidad diferenciada:

- **Routes:** exponen HTTP, reciben y validan parámetros/esquemas, aplican dependencias de autorización y delegan el trabajo. No ejecutan SQL.
- **Controllers:** contienen la lógica de negocio y las consultas SQLAlchemy. No dependen de `HTTPException`; para errores usan excepciones propias.
- **Schemas:** validan datos de entrada y definen las respuestas públicas. No consultan la base de datos ni exponen `password_hash`.
- **Models:** representan tablas y relaciones ORM.
- **Core:** configura ajustes, sesiones, autenticación, seguridad, dependencias, excepciones y rate limiting.

```text
app/
├── main.py                 # Aplicación FastAPI, middleware y montaje de routers
├── core/
│   ├── config.py           # Settings y variables de entorno
│   ├── database.py         # Base ORM, motor y sesiones SQLAlchemy
│   ├── dependencies.py     # Sesión, paginación, usuario autenticado y roles
│   ├── exceptions.py       # Excepciones de aplicación
│   ├── limiter.py          # Configuración de SlowAPI
│   └── security.py         # Hash Argon2 y creación/validación JWT
├── models/                 # Entidades y relaciones ORM
├── schemas/                # Esquemas Pydantic de entrada y salida
├── controllers/            # Consultas y reglas de negocio
├── routes/                 # Endpoints agrupados por recurso
└── scripts/
    └── crear_admin.py      # Alta interactiva del primer administrador
alembic/
└── versions/               # Revisiones versionadas del esquema
tests/
├── conftest.py             # Fixtures, base de pruebas y cliente HTTP
└── test_*.py               # Pruebas de autenticación, permisos y reglas
```

### Flujo de una petición

```mermaid
sequenceDiagram
    participant C as Cliente
    participant R as Router FastAPI
    participant D as Dependencias
    participant CT as Controller
    participant DB as PostgreSQL
    C->>R: Solicitud HTTP /api/v1
    R->>D: Validación, sesión, token y rol (si aplica)
    D-->>R: Datos validados y principal autenticado
    R->>CT: Invoca caso de uso con esquema y sesión
    CT->>DB: Consulta o transacción SQLAlchemy
    DB-->>CT: Resultado
    CT-->>R: Modelo o resultado de negocio
    R-->>C: Respuesta JSON y X-Request-ID
```

### Flujo JWT

```mermaid
sequenceDiagram
    participant C as Cliente
    participant A as /auth/login
    participant DB as Base de datos
    participant API as Endpoint protegido
    C->>A: username=email y password (formulario OAuth2)
    A->>DB: Busca usuario y verifica hash Argon2
    A->>DB: Persiste JTI del refresh token
    A-->>C: access_token + refresh_token
    C->>API: Authorization: Bearer access_token
    API->>DB: Valida JWT y consulta usuario/estado/rol
    API-->>C: Recurso autorizado
    C->>A: POST /auth/refresh con refresh_token
    A->>DB: Revoca el JTI recibido y registra uno nuevo
    A-->>C: Nuevo par de tokens
```

## Modelo de datos

```mermaid
erDiagram
    AUTORES ||--o{ LIBROS : escribe
    LIBROS ||--o{ LIBRO_CATEGORIA : clasifica
    CATEGORIAS ||--o{ LIBRO_CATEGORIA : contiene
    LIBROS ||--o{ PRESTAMOS : se_presta
    SOCIOS ||--o{ PRESTAMOS : solicita
    SOCIOS o|--o| USUARIOS : cuenta
    USUARIOS ||--o{ REFRESH_TOKENS : posee
    USUARIOS o|--o{ PRESTAMOS : registra

    AUTORES {
        int id PK
        string nombre
        string nacionalidad
        int anio_nacimiento
    }
    CATEGORIAS {
        int id PK
        string nombre
        string descripcion
    }
    LIBROS {
        int id PK
        string titulo
        string isbn UK
        int anio_publicacion
        int ejemplares
        string imagen_url
        int autor_id FK
    }
    LIBRO_CATEGORIA {
        int libro_id PK, FK
        int categoria_id PK, FK
    }
    SOCIOS {
        int id PK
        string nombre
        string email UK
        string telefono
        boolean activo
        datetime fecha_alta
    }
    USUARIOS {
        int id PK
        string email UK
        string nombre
        string password_hash
        enum rol
        boolean activo
        int socio_id FK, UK
        datetime creado_en
    }
    REFRESH_TOKENS {
        int id PK
        string jti UK
        int usuario_id FK
        datetime expira_en
        boolean revocado
        datetime creado_en
    }
    PRESTAMOS {
        int id PK
        int libro_id FK
        int socio_id FK
        int registrado_por_id FK
        date fecha_prestamo
        date fecha_limite
        date fecha_devolucion
        decimal multa
        boolean multa_pagada
    }
```

Los valores `NULL` y restricciones concretas se definen en los modelos y migraciones. `registrado_por_id` puede ser nulo para conservar préstamos históricos creados antes de incorporar la auditoría.

## Requisitos previos

- Windows 10/11 con PowerShell, Python 3.10+ y `pip`.
- PostgreSQL 16 o Docker Desktop con Docker Compose.
- Una clave secreta segura para JWT. No compartas ni subas el `.env`.

## Instalación y ejecución desde cero (PowerShell)

Desde la carpeta del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Genera una clave para desarrollo:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Edita `.env` y pega el resultado en `SECRET_KEY`. La clave debe tener al menos 32 caracteres. Para producción, usa un gestor de secretos; no reutilices una clave de ejemplo.

Inicia PostgreSQL y crea el esquema con Alembic:

```powershell
docker compose up -d db
alembic upgrade head
```

El servicio `db` publica PostgreSQL en `localhost:5432` y crea las bases `biblioteca_db` y `biblioteca_test` al inicializar un volumen nuevo. Si el volumen ya existía antes de configurar la base de pruebas, créala una sola vez:

```powershell
docker compose exec db createdb -U biblioteca biblioteca_test
```

Crea el administrador inicial. El script pide email, nombre y contraseña de forma interactiva, y no crea otra cuenta si ese email ya existe:

```powershell
python -m app.scripts.crear_admin
```

Inicia la API en desarrollo:

```powershell
fastapi dev app/main.py
```

O utilizando Uvicorn con recarga automática:

```powershell
uvicorn app.main:app --reload
```

Abre `http://127.0.0.1:8000/docs`. Pulsa **Authorize** y autentícate con `/api/v1/auth/login`; utiliza el correo en el campo `username`. En producción la documentación Swagger y ReDoc se deshabilitan.

### Flujo sugerido para probar en `/docs`

Usa contraseñas propias que cumplan los requisitos; el proyecto no distribuye contraseñas de demostración.

1. Ejecuta `python -m app.scripts.crear_admin` y crea el administrador `admin@biblioteca.com`.
2. Autoriza Swagger con ese admin. En `POST /api/v1/usuarios`, crea el bibliotecario `biblio@biblioteca.com` con rol `bibliotecario`.
3. En `POST /api/v1/auth/registro`, registra `ana@example.com` y `luis@example.com`. El registro crea cada socio y su usuario en la misma transacción.
4. Cierra sesión o vuelve a **Authorize** con `biblio@biblioteca.com` para probar autores, libros, socios, préstamos y reportes. Comprueba que bibliotecario no puede eliminar libros.
5. Autoriza como Ana y consulta `/api/v1/socios/me`, `/api/v1/socios/me/prestamos` y `/api/v1/prestamos`. Envía `?socio_id=` de Luis y verifica que solo aparezcan los préstamos de Ana; consultar directamente el préstamo de Luis debe devolver `404`.
6. Vuelve a autorizar como admin para probar administración de usuarios y la protección del último administrador activo.

### Ejecución completa en Docker (opcional)

Configura primero `.env` con una `SECRET_KEY` válida y `DATABASE_URL` con una URL para el servicio `db`. Después:

```powershell
docker compose up --build -d
docker compose logs -f api
```

El contenedor de API ejecuta `alembic upgrade head` antes de iniciar FastAPI. No publiques los valores de desarrollo de `POSTGRES_PASSWORD` en producción. Para detener los servicios sin borrar los datos persistidos:

```powershell
docker compose down
```

### Despliegue en Render (Web Service)

Para desplegar la aplicación en **Render** como Web Service:

- **Build Command:**
  ```bash
  pip install -r requirements.txt && alembic upgrade head
  ```
- **Start Command:**
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```
  *(o alternativamente: `fastapi run app/main.py --host 0.0.0.0 --port $PORT`)*

> [!NOTE]
> Asegúrate de configurar las variables de entorno necesarias (`DATABASE_URL`, `SECRET_KEY`, `ENVIRONMENT=prod`, etc.) en el panel de Render.

## Variables de entorno

| Variable | Obligatoria | Valor de desarrollo sugerido | Descripción |
|---|---:|---|---|
| `DATABASE_URL` | Sí | `postgresql+psycopg://biblioteca:biblioteca_dev@localhost:5432/biblioteca_db` | URL SQLAlchemy de la base principal. |
| `TEST_DATABASE_URL` | Para pruebas | `postgresql+psycopg://biblioteca:biblioteca_dev@localhost:5432/biblioteca_test` | Base aislada de pytest; nunca debe ser la base principal. |
| `SECRET_KEY` | Sí | Generada localmente | Clave JWT de al menos 32 caracteres. No se guarda en Git. |
| `ALGORITHM` | No | `HS256` | Algoritmo JWT permitido. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `15` | Duración del access token. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Duración del refresh token. |
| `CORS_ORIGINS` | No | `[]` | Lista JSON de orígenes permitidos, por ejemplo `["http://localhost:3000"]`. |
| `ENVIRONMENT` | No | `dev` | Entorno: `dev`, `test` o `prod`. No se permite `*` en CORS en producción. |
| `POSTGRES_PASSWORD` | No para Docker local | `biblioteca_dev` | Contraseña del contenedor PostgreSQL; el valor de desarrollo debe sustituirse en entornos compartidos o productivos. |
| `CLOUDINARY_URL` | Opcional / Recomendado | `cloudinary://<api_key>:<api_secret>@<cloud_name>` | URL de conexión al SDK de Cloudinary para almacenar portadas de libros. |

Las variables se leen en [app/core/config.py](./app/core/config.py), que centraliza `Settings` y `get_settings()` con caché.

## Migraciones Alembic

| Revisión | Cambio |
|---|---|
| `0001_estado_inicial` | Tablas de autores, categorías, libros, relación libro-categoría, socios y préstamos. |
| `0002_multa_pagada` | Agrega `prestamos.multa_pagada`, con valor inicial falso; marca como pagadas las multas con valor cero. |
| `0003_usuarios` | Crea usuarios, roles, vínculo opcional 1:1 con socio e índice funcional de email en minúsculas. |
| `0004_refresh_tokens` | Crea el registro de refresh tokens por JTI, usuario, vencimiento y revocación. |
| `0005_auditoria_prestamos` | Agrega a préstamos el usuario que registró la operación. |
| `0006_imagen_url_libros` | Añade la columna `imagen_url` en la tabla `libros` para portadas Cloudinary. |

Comandos útiles:

```powershell
alembic current
alembic history
alembic upgrade head
alembic downgrade -1
alembic downgrade base
alembic revision --autogenerate -m "descripcion_del_cambio"
```

Antes de usar una revisión autogenerada, revísala y corrige manualmente los cambios de datos, enums, índices funcionales y operaciones que Alembic no deduce con seguridad. Cada migración debe tener un `downgrade()` funcional y debe revisarse/confirmarse en su propio commit.

**Recrear una base de desarrollo vacía (destructivo):** haz copia de seguridad primero; el siguiente comando borra el volumen PostgreSQL de desarrollo y sus datos.

```powershell
docker compose down -v
docker compose up -d db
alembic upgrade head
python -m app.scripts.crear_admin
```

No ejecutes este procedimiento en una base con datos que deban conservarse.

## Seguridad, autenticación y roles

### JWT y credenciales

- El registro de socios y el login son públicos; el login recibe un formulario OAuth2 con `username=email` y `password`.
- El access token se envía en `Authorization: Bearer <access_token>`.
- Los tokens incluyen `sub`, `rol`, `type` (`access` o `refresh`), `iat`, `exp` y `jti`.
- JWT está firmado, no cifrado: su contenido puede decodificarse, así que no debe llevar secretos.
- Las contraseñas se almacenan como hashes Argon2 mediante `pwdlib`; nunca se incluyen en esquemas de respuesta.
- Solo se persiste el JTI de un refresh token, no el token completo.
- El access token no sirve como refresh token ni al contrario. El refresh se rota; si se reutiliza uno revocado, se revocan los refresh tokens activos del usuario.
- El estado y rol del usuario se vuelven a consultar en la base de datos para cada petición autenticada.
- El cambio de contraseña, el cambio de rol y la desactivación revocan refresh tokens según la operación.
- Los errores internos devuelven un mensaje genérico. El logging registra método, ruta, código, duración e ID de solicitud, no cuerpos, contraseñas ni tokens.

### Matriz de permisos

| Recurso / operación | Público | Socio autenticado | Bibliotecario | Administrador |
|---|:---:|:---:|:---:|:---:|
| Registro, login, refresh y health | Sí | Sí | Sí | Sí |
| Lectura de libros, autores y categorías | Sí | Sí | Sí | Sí |
| Crear/editar libros, autores y categorías | No | No | Sí | Sí |
| Eliminar libros, autores y categorías | No | No | No | Sí |
| Consultar o modificar su perfil de socio | No | Sí, propio | No | No |
| Consultar préstamos propios | No | Sí, propios | Según rutas de staff | Según rutas de staff |
| Lectura, alta y edición administrativa de socios | No | No | Sí | Sí |
| Eliminar socios | No | No | No | Sí |
| Crear préstamos, devolver y pagar multas | No | No | Sí | Sí |
| Reportes | No | No | Sí | Sí |
| Administrar usuarios y roles | No | No | No | Sí |
| `/auth/me`, logout y cambio de contraseña | No | Sí | Sí | Sí |

Los usuarios con rol socio no pueden cambiar su email, rol o estado; la ruta `/socios/me` solo acepta nombre y teléfono.

### Reglas de negocio de préstamos (R1–R11)

| Regla | Comportamiento |
|---|---|
| R1 | El socio debe existir. |
| R2 | El libro debe existir. |
| R3 | El socio debe estar activo. |
| R4 | El socio no debe tener préstamos vencidos sin devolver. |
| R5 | El socio no puede superar tres préstamos sin devolver. |
| R6 | El socio no puede tener el mismo libro en otro préstamo sin devolver. |
| R7 | Debe haber ejemplares disponibles. |
| R8 | La fecha límite se calcula sumando los días solicitados a la fecha del préstamo. |
| R9 | Solo se puede devolver un préstamo existente que aún no se haya devuelto; la fecha de devolución no puede preceder la fecha de préstamo. |
| R10 | La devolución tardía genera una multa de 0,50 por cada día de retraso. |
| R11 | El socio con multas sin pagar no puede solicitar otro préstamo. `/prestamos/{id}/pago-multa` permite registrar el pago de una multa pendiente. |

### Reglas de autenticación (A1–A7)

| Regla | Comportamiento |
|---|---|
| A1 | Email inexistente y contraseña incorrecta devuelven `401` con el mismo mensaje. |
| A2 | El usuario inactivo recibe `403`, incluso con un token vigente. |
| A3 | Cinco fallos consecutivos bloquean el login durante 15 minutos (`423`); un login exitoso reinicia el contador. |
| A4 | Un access token inválido o vencido no autentica (`401`). |
| A5 | Un refresh token no es válido como access token, ni viceversa. |
| A6 | El refresh debe existir, estar vigente y no revocado. La reutilización de uno rotado revoca los refresh activos del usuario. |
| A7 | Cada petición autenticada vuelve a consultar el usuario en la base de datos. |

### Reglas de autorización y usuarios (Z1–Z7)

| Regla | Comportamiento |
|---|---|
| Z1 | Un rol no autorizado recibe `403`. |
| Z2 | Un socio que solicita el préstamo de otra persona recibe `404`. |
| Z3 | En el listado de préstamos, un socio solo recibe los suyos; un `socio_id` ajeno enviado como filtro no amplía la consulta. |
| Z4 | El socio no puede cambiar email, estado ni rol; campos extra en `/socios/me` se rechazan con `422`. |
| Z5 | Siempre debe quedar un administrador activo; no se permite que el último admin activo se quite su rol o se desactive. |
| Z6 | Al cambiar rol o desactivar un usuario se revocan sus refresh tokens. |
| Z7 | Cada préstamo registra `registrado_por_id` cuando lo crea un usuario autenticado de staff. |

## Endpoints

Todas las rutas de la tabla incluyen el prefijo `/api/v1`. Los listados paginados aceptan `skip` (por defecto 0) y `limit` (por defecto 10; máximo 100). **Público** no requiere token; **Autenticado** requiere cualquier usuario activo; **Socio propio** restringe el recurso al socio autenticado; **Staff** significa bibliotecario o administrador.

| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| `GET` | `/health` | Público | Estado de API y base de datos. |
| `POST` | `/auth/registro` | Público | Crear usuario socio y socio asociado. Límite: 5/min por IP. |
| `POST` | `/auth/login` | Público | Obtener access y refresh token mediante formulario. Límite: 10/min por IP. |
| `POST` | `/auth/refresh` | Público con refresh válido | Rotar el par de tokens. |
| `POST` | `/auth/logout` | Autenticado | Revocar refresh tokens del usuario actual. |
| `GET` | `/auth/me` | Autenticado | Consultar la cuenta actual. |
| `PATCH` | `/auth/me/password` | Autenticado | Cambiar contraseña y revocar refresh tokens. |
| `GET` | `/autores` | Público | Listar autores; filtro opcional `nacionalidad`. |
| `GET` | `/autores/{autor_id}` | Público | Consultar un autor. |
| `GET` | `/autores/{autor_id}/libros` | Público | Listar libros del autor. |
| `POST`, `PATCH` | `/autores`, `/autores/{autor_id}` | Staff | Crear o editar autor. |
| `DELETE` | `/autores/{autor_id}` | Admin | Eliminar autor. |
| `GET` | `/categorias` | Público | Listar categorías. |
| `POST`, `PATCH` | `/categorias`, `/categorias/{categoria_id}` | Staff | Crear o editar categoría. |
| `DELETE` | `/categorias/{categoria_id}` | Admin | Eliminar categoría. |
| `GET` | `/libros` | Público | Buscar, filtrar, ordenar y paginar libros. |
| `GET` | `/libros/{libro_id}` | Público | Consultar un libro. |
| `POST`, `PATCH` | `/libros`, `/libros/{libro_id}` | Staff | Crear (soporta JSON o multipart con `imagen`) o editar libro. |
| `POST` | `/libros/{libro_id}/portada` | Staff | Subir o actualizar archivo de imagen de portada en Cloudinary. |
| `DELETE` | `/libros/{libro_id}` | Admin | Eliminar libro. |
| `GET` | `/socios/me` | Socio propio | Consultar su perfil. |
| `PATCH` | `/socios/me` | Socio propio | Editar nombre y teléfono únicamente. |
| `GET` | `/socios/me/prestamos` | Socio propio | Consultar sus préstamos; filtro opcional `estado`. |
| `GET` | `/socios/me/multas` | Socio propio | Multas pendientes y total adeudado. |
| `GET`, `POST` | `/socios` | Staff | Listar o registrar socios. |
| `GET`, `PATCH` | `/socios/{socio_id}` | Staff | Consultar o editar socio. |
| `GET` | `/socios/{socio_id}/prestamos` | Staff | Historial de un socio; filtro opcional `estado`. |
| `DELETE` | `/socios/{socio_id}` | Admin | Eliminar socio conforme a restricciones de datos. |
| `GET` | `/prestamos` | Autenticado | Listar préstamos; filtros `estado`, `socio_id`, `libro_id`. Socios solo ven los propios. |
| `GET` | `/prestamos/{prestamo_id}` | Autenticado | Consultar préstamo; socio solo el propio. |
| `POST` | `/prestamos` | Staff | Crear préstamo y guardar usuario registrador. |
| `POST` | `/prestamos/{prestamo_id}/devolucion` | Staff | Registrar devolución y multa si aplica. |
| `POST` | `/prestamos/{prestamo_id}/pago-multa` | Staff | Marcar multa pendiente como pagada. |
| `GET` | `/reportes/resumen` | Staff | Resumen agregado de la biblioteca. |
| `GET` | `/reportes/libros-mas-prestados` | Staff | Reporte paginado de libros más prestados. |
| `GET` | `/reportes/categorias` | Staff | Estadísticas paginadas por categoría. |
| `GET` | `/reportes/autores` | Staff | Estadísticas paginadas por autor. |
| `GET` | `/reportes/prestamos-vencidos` | Staff | Préstamos vencidos paginados. |
| `GET` | `/reportes/socios-con-multas` | Staff | Socios con multas paginados. |
| `GET` | `/usuarios` | Admin | Listar usuarios; filtros `rol`, `activo`. |
| `POST` | `/usuarios` | Admin | Crear usuario admin o bibliotecario. |
| `PATCH` | `/usuarios/{usuario_id}/rol` | Admin | Cambiar rol y revocar refresh tokens. |
| `PATCH` | `/usuarios/{usuario_id}/activo` | Admin | Cambiar estado y revocar refresh al desactivar. |

## Pruebas

Configura `TEST_DATABASE_URL` en `.env` apuntando a una base exclusiva, distinta de `DATABASE_URL`. En una instalación Docker nueva, el Compose crea `biblioteca_test`. En PowerShell:

```powershell
python -m pip install -r requirements-dev.txt
docker compose up -d db
$env:TEST_DATABASE_URL = "postgresql+psycopg://biblioteca:biblioteca_dev@localhost:5432/biblioteca_test"
python -m pytest --cov=app --cov-fail-under=70 -q
```

La fixture de pruebas aplica las migraciones a la base configurada y las revierte al terminar. No configures la URL de producción o de desarrollo normal como `TEST_DATABASE_URL`: las tablas de la base de pruebas se limpian durante los tests. El proyecto también puede probarse con una URL SQLite de archivo. Ejemplo:

```powershell
$env:TEST_DATABASE_URL = "sqlite:///C:/temp/biblioteca_test.db"
python -m pytest --cov=app --cov-fail-under=70 -q
```

La suite cubre validación y duplicación de registro, login y bloqueo, tokens y rotación, límites por IP, permisos por rol, privacidad de préstamos del socio, auditoría, multas, health y ciclo upgrade/downgrade de Alembic.

## Códigos HTTP frecuentes

| Código | Significado |
|---:|---|
| `200` | Operación de consulta o modificación completada. |
| `201` | Recurso creado. |
| `204` | Operación completada sin contenido (por ejemplo, logout). |
| `401` | Falta autenticación o el token/credencial no es válido; incluye `WWW-Authenticate: Bearer` cuando aplica. |
| `403` | Usuario autenticado sin permiso o cuenta inactiva. |
| `404` | Recurso inexistente o préstamo que no pertenece al socio. |
| `409` | Conflicto con el estado actual o duplicado. |
| `422` | Datos inválidos o regla de negocio incumplida. |
| `423` | Cuenta bloqueada temporalmente. |
| `429` | Se excedió el límite de solicitudes. |
| `500` | Error interno; respuesta genérica sin detalle de implementación. |
| `503` | Base de datos no disponible en el health check. |

## Seguridad web

- **CORS:** permite controlar qué orígenes de navegador pueden invocar la API. Configura los orígenes concretos en `CORS_ORIGINS`; el comodín `*` se rechaza en producción.
- **Rate limiting:** restringe intentos repetidos de login y registro por IP, reduciendo abuso automatizado como fuerza bruta y creación masiva de cuentas.
- **Request ID:** cada respuesta lleva `X-Request-ID` para correlacionar solicitudes con logs sin registrar credenciales.
- **Secretos:** `.env` está excluido de Git. Mantén claves y contraseñas fuera del repositorio y rota cualquier secreto expuesto.

## Integrantes

- Por definir
