# docker-cicd-azure

Aplicación demo Flask containerizada con pipeline CI/CD en GitHub Actions que construye una imagen Docker, la publica en Azure Container Registry (ACR) y despliega en Azure App Service.

Repositorio: [jemjaf/docker-cicd-azure](https://github.com/jemjaf/docker-cicd-azure)

## Stack

| Componente | Tecnología |
|------------|------------|
| Backend | Python 3.14, Flask 3.1, Gunicorn |
| Contenedor | Docker multi-stage |
| CI/CD | GitHub Actions |
| Azure | ACR + App Service (Linux/containers) |

## Estructura del proyecto

```
.
├── app/
│   ├── __init__.py       # Factory de Flask
│   ├── routes.py         # Rutas HTTP
│   ├── demo_data.py      # Datos de ejemplo (productos, clientes, pedidos)
│   ├── static/           # CSS
│   └── templates/        # Plantillas HTML
├── .github/workflows/
│   └── ci-cd.yaml        # Pipeline build → push ACR → deploy App Service
├── Dockerfile
├── wsgi.py               # Entrypoint WSGI para Gunicorn
├── run.py                # Servidor de desarrollo local
├── requirements.txt
└── azure_github_oidc_setup.md   # Guía detallada de autenticación Azure
```

## Rutas de la aplicación

| Ruta | Descripción |
|------|-------------|
| `/` | Dashboard con contadores |
| `/productos` | Listado de productos |
| `/clientes` | Listado de clientes |
| `/pedidos` | Listado de pedidos |
| `/runtime` | Info del entorno (hostname, uptime, versión Python, etc.) |

## Desarrollo local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

La app arranca en `http://localhost:5000` (puerto configurable con `PORT`).

## Docker local

```bash
docker build -t docker-cicd-azure .
docker run -p 8000:8000 docker-cicd-azure
```

La imagen expone el puerto **8000** y usa Gunicorn como servidor WSGI.

---

## Valores de Azure (este proyecto)

Recursos desplegados en el sandbox de Real Hands-On Labs:

| Recurso | Valor |
|---------|-------|
| Resource Group | `1-199d089d-playground-sandbox` |
| Región | `southcentralus` |
| Azure Container Registry | `skoolapp` |
| Login server ACR | `skoolapp.azurecr.io` |
| App Service | `dockercicd` |
| App Service Plan | `ASP-1199d089dplaygroundsandbox-8d7b` |
| Imagen Docker | `skoolapp.azurecr.io/repo/appimg` |
| URL App Service | `https://dockercicd.azurewebsites.net` |

### Tags de imagen en CI/CD

El pipeline genera dos tags en cada push a `main`:

- `skoolapp.azurecr.io/repo/appimg:v{run_number}` — versión desplegada
- `skoolapp.azurecr.io/repo/appimg:latest`

---

## Pipeline CI/CD

Archivo: `.github/workflows/ci-cd.yaml`

**Trigger:** push a la rama `main`

**Flujo:**

1. Checkout del código
2. Setup de Docker
3. Login al ACR
4. Build y push de la imagen
5. Deploy al App Service `dockercicd`

**Método de autenticación:** ACR admin credentials + Publish Profile (sin OIDC), porque el entorno de laboratorio no permite crear App Registrations en Entra ID.

Para la configuración OIDC (entornos con permisos de directorio), ver [azure_github_oidc_setup.md](./azure_github_oidc_setup.md).

---

## Secretos y variables en GitHub

Configurar en **Settings → Secrets and variables → Actions**:

### Secrets (Repository secrets)

| Secret | Descripción | Cómo obtenerlo |
|--------|-------------|----------------|
| `ACR_PASSWORD` | Password del admin user del ACR | `az acr credential show -n skoolapp -g 1-199d089d-playground-sandbox` |
| `AZURE_WEBAPP_PUBLISH_PROFILE` | XML completo del publish profile | `az webapp deployment list-publishing-profiles -n dockercicd -g 1-199d089d-playground-sandbox --xml` |

### Variables (Repository variables)

| Variable | Descripción | Cómo obtenerlo |
|----------|-------------|----------------|
| `ACR_USERNAME` | Username del admin user del ACR | `az acr credential show -n skoolapp -g 1-199d089d-playground-sandbox --query username -o tsv` |

> Si prefiere guardar el username también como secret, cambie `${{ vars.ACR_USERNAME }}` por `${{ secrets.ACR_USERNAME }}` en el workflow.

### Comandos para obtener credenciales

```bash
RESOURCE_GROUP="1-199d089d-playground-sandbox"
ACR_NAME="skoolapp"
WEBAPP_NAME="dockercicd"

# Habilitar admin user del ACR (solo la primera vez)
az acr update -n $ACR_NAME --admin-enabled true -g $RESOURCE_GROUP

# Credenciales del ACR
az acr credential show -n $ACR_NAME -g $RESOURCE_GROUP

# Publish profile del App Service
az webapp deployment list-publishing-profiles \
  -n $WEBAPP_NAME -g $RESOURCE_GROUP --xml
```

---

## Editor: evitar errores de sintaxis YAML

GitHub Actions exige **solo espacios** para la indentación. Mezclar tabs y espacios provoca errores de sintaxis aunque en el editor se vea alineado.

### Configuración recomendada (Cursor / VS Code)

Cree `.vscode/settings.json` en la raíz del proyecto:

```json
{
  "[yaml]": {
    "editor.insertSpaces": true,
    "editor.tabSize": 2,
    "editor.detectIndentation": false
  },
  "editor.renderWhitespace": "boundary"
}
```

- `insertSpaces` — la tecla Tab inserta espacios, no tabs
- `tabSize: 2` — indentación estándar de YAML
- `detectIndentation: false` — evita que el editor mezcle estilos
- `renderWhitespace: "boundary"` — muestra puntos (·) en espacios y flechas (→) en tabs

### Corregir un archivo ya dañado

1. Abrir `.github/workflows/ci-cd.yaml`
2. `Ctrl+A` para seleccionar todo
3. `Ctrl+Shift+P` → **Convert Indentation to Spaces**
4. Guardar

### Verificar tabs desde terminal

```bash
grep -P '\t' .github/workflows/ci-cd.yaml
```

Si no imprime nada, el archivo está limpio.

---

## Referencias

- [azure_github_oidc_setup.md](./azure_github_oidc_setup.md) — OIDC y alternativa ACR + Publish Profile
- [Azure/webapps-deploy](https://github.com/Azure/webapps-deploy) — Action de deploy
- [docker/build-push-action](https://github.com/docker/build-push-action) — Action de build/push
